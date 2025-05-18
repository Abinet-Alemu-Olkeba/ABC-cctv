from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models import User, Role, Location, Camera, SystemHealth, Incident, LocationAccess
from forms import LoginForm, UserForm, LocationForm, CameraForm, IncidentForm
from shinobi_api import get_cameras, get_camera_status, start_recording, stop_recording
from datetime import datetime
import logging

def register_routes(app):
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        
        form = LoginForm()
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get accessible locations for current user
        if current_user.role.name == "Administrator":
            locations = Location.query.all()
        else:
            location_ids = [access.location_id for access in current_user.location_access]
            locations = Location.query.filter(Location.id.in_(location_ids)).all()
        
        # Get system health data
        health = SystemHealth.query.order_by(SystemHealth.last_updated.desc()).first()
        
        # Get total cameras count
        camera_count = 0
        online_cameras = 0
        for location in locations:
            camera_count += len(location.cameras)
            online_cameras += len([cam for cam in location.cameras if cam.status == 'online'])
        
        # Get recent incidents
        incidents = Incident.query.order_by(Incident.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', 
                              locations=locations, 
                              health=health,
                              camera_count=camera_count,
                              online_cameras=online_cameras,
                              offline_cameras=camera_count - online_cameras,
                              incidents=incidents)
    
    @app.route('/cameras')
    @login_required
    def cameras():
        # Get locations user has access to
        if current_user.role.name == "Administrator":
            locations = Location.query.all()
        else:
            location_ids = [access.location_id for access in current_user.location_access]
            locations = Location.query.filter(Location.id.in_(location_ids)).all()
        
        # Get cameras for each location
        cameras = []
        for location in locations:
            location_cameras = Camera.query.filter_by(location_id=location.id).all()
            cameras.extend(location_cameras)
        
        return render_template('cameras.html', cameras=cameras, locations=locations)
    
    @app.route('/camera/<int:camera_id>')
    @login_required
    def camera_detail(camera_id):
        camera = Camera.query.get_or_404(camera_id)
        
        # Check if user has access to this camera's location
        if not current_user.has_access_to_location(camera.location_id) and current_user.role.name != "Administrator":
            flash('You do not have access to this camera', 'danger')
            return redirect(url_for('cameras'))
        
        return render_template('camera_detail.html', camera=camera)
    
    @app.route('/locations')
    @login_required
    def locations():
        # Only administrators and warehouse managers can see all locations
        if current_user.role.name in ["Administrator", "Warehouse Manager"]:
            if current_user.role.name == "Administrator":
                locations = Location.query.all()
            else:
                location_ids = [access.location_id for access in current_user.location_access]
                locations = Location.query.filter(Location.id.in_(location_ids)).all()
                
            return render_template('locations.html', locations=locations)
        else:
            flash('You do not have permission to access locations management', 'warning')
            return redirect(url_for('dashboard'))
    
    @app.route('/location/add', methods=['GET', 'POST'])
    @login_required
    def add_location():
        # Only administrators can add locations
        if current_user.role.name != "Administrator":
            flash('You do not have permission to add locations', 'danger')
            return redirect(url_for('locations'))
            
        form = LocationForm()
        if form.validate_on_submit():
            location = Location(
                name=form.name.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                country=form.country.data,
                zipcode=form.zipcode.data
            )
            db.session.add(location)
            db.session.commit()
            flash(f'Location {location.name} has been added', 'success')
            return redirect(url_for('locations'))
            
        return render_template('location_form.html', form=form, title="Add New Location")
    
    @app.route('/location/<int:location_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_location(location_id):
        # Only administrators can edit locations
        if current_user.role.name != "Administrator":
            flash('You do not have permission to edit locations', 'danger')
            return redirect(url_for('locations'))
            
        location = Location.query.get_or_404(location_id)
        form = LocationForm(obj=location)
        
        if form.validate_on_submit():
            form.populate_obj(location)
            db.session.commit()
            flash(f'Location {location.name} has been updated', 'success')
            return redirect(url_for('locations'))
            
        return render_template('location_form.html', form=form, title=f"Edit Location: {location.name}")
    
    @app.route('/users')
    @login_required
    def users():
        # Only administrators can manage users
        if current_user.role.name != "Administrator":
            flash('You do not have permission to access user management', 'danger')
            return redirect(url_for('dashboard'))
            
        users = User.query.all()
        return render_template('users.html', users=users)
    
    @app.route('/user/add', methods=['GET', 'POST'])
    @login_required
    def add_user():
        # Only administrators can add users
        if current_user.role.name != "Administrator":
            flash('You do not have permission to add users', 'danger')
            return redirect(url_for('users'))
            
        form = UserForm()
        # Populate role choices
        form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
        
        if form.validate_on_submit():
            # Check if username or email already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists', 'danger')
                return render_template('user_form.html', form=form, title="Add New User")
                
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already exists', 'danger')
                return render_template('user_form.html', form=form, title="Add New User")
                
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role_id=form.role_id.data,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Add location access if specified
            if form.locations.data:
                for location_id in form.locations.data:
                    access = LocationAccess(user_id=user.id, location_id=location_id)
                    db.session.add(access)
                db.session.commit()
                
            flash(f'User {user.username} has been added', 'success')
            return redirect(url_for('users'))
            
        return render_template('user_form.html', form=form, title="Add New User")
    
    @app.route('/system-health')
    @login_required
    def system_health():
        # Get latest system health data
        health = SystemHealth.query.order_by(SystemHealth.last_updated.desc()).first()
        
        # Get locations and their status
        if current_user.role.name == "Administrator":
            locations = Location.query.all()
        else:
            location_ids = [access.location_id for access in current_user.location_access]
            locations = Location.query.filter(Location.id.in_(location_ids)).all()
        
        # Camera statistics
        total_cameras = Camera.query.count()
        online_cameras = Camera.query.filter_by(status='online').count()
        offline_cameras = total_cameras - online_cameras
        
        return render_template('system-health.html', 
                              health=health, 
                              locations=locations,
                              total_cameras=total_cameras,
                              online_cameras=online_cameras,
                              offline_cameras=offline_cameras)
    
    @app.route('/settings')
    @login_required
    def settings():
        # Only administrators can access settings
        if current_user.role.name != "Administrator":
            flash('You do not have permission to access system settings', 'danger')
            return redirect(url_for('dashboard'))
            
        return render_template('settings.html')
    
    # API endpoints for AJAX requests
    
    @app.route('/api/camera/<int:camera_id>/status')
    @login_required
    def camera_status(camera_id):
        camera = Camera.query.get_or_404(camera_id)
        
        # Check if user has access to this camera
        if not current_user.has_access_to_location(camera.location_id) and current_user.role.name != "Administrator":
            return jsonify({'error': 'Access denied'}), 403
        
        # Get status from Shinobi API (mock for now)
        status = get_camera_status(camera.shinobi_id, camera.shinobi_api_key, camera.shinobi_group_key)
        
        # Update camera status in database
        camera.status = status
        camera.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': camera.id,
            'name': camera.name,
            'status': camera.status,
            'is_recording': camera.is_recording,
            'last_updated': camera.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    @app.route('/api/camera/<int:camera_id>/recording', methods=['POST'])
    @login_required
    def toggle_recording(camera_id):
        camera = Camera.query.get_or_404(camera_id)
        
        # Check if user has access to this camera
        if not current_user.has_access_to_location(camera.location_id) and current_user.role.name != "Administrator":
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if user has permission to control recording
        if current_user.role.name not in ["Administrator", "Warehouse Manager", "Security Operator"]:
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({'error': 'Invalid request'}), 400
        
        action = data['action']
        if action == 'start':
            # Start recording via Shinobi API
            success = start_recording(camera.shinobi_id, camera.shinobi_api_key, camera.shinobi_group_key)
            if success:
                camera.is_recording = True
                db.session.commit()
                return jsonify({'success': True, 'message': 'Recording started', 'is_recording': True})
            else:
                return jsonify({'error': 'Failed to start recording'}), 500
        elif action == 'stop':
            # Stop recording via Shinobi API
            success = stop_recording(camera.shinobi_id, camera.shinobi_api_key, camera.shinobi_group_key)
            if success:
                camera.is_recording = False
                db.session.commit()
                return jsonify({'success': True, 'message': 'Recording stopped', 'is_recording': False})
            else:
                return jsonify({'error': 'Failed to stop recording'}), 500
        else:
            return jsonify({'error': 'Invalid action'}), 400
    
    @app.route('/api/dashboard/stats')
    @login_required
    def dashboard_stats():
        try:
            # Get system health data
            health = SystemHealth.query.order_by(SystemHealth.last_updated.desc()).first()
            
            # Default values for health metrics
            default_cpu = 25.5
            default_memory = 40.2
            default_storage = 60.7
            default_vpn = 3
            
            # Get camera statistics
            if current_user.role.name == "Administrator":
                total_cameras = Camera.query.count()
                online_cameras = Camera.query.filter_by(status='online').count()
            else:
                # Get only cameras from locations user has access to
                location_ids = [access.location_id for access in current_user.location_access]
                if not location_ids:  # If empty list, use a value that won't match anything
                    location_ids = [-1]
                total_cameras = Camera.query.filter(Camera.location_id.in_(location_ids)).count()
                online_cameras = Camera.query.filter(Camera.location_id.in_(location_ids), Camera.status=='online').count()
            
            offline_cameras = total_cameras - online_cameras
            
            # Get location statistics
            if current_user.role.name == "Administrator":
                total_locations = Location.query.count()
                online_locations = Location.query.filter_by(vpn_status=True).count()
            else:
                location_ids = [access.location_id for access in current_user.location_access]
                total_locations = len(location_ids)
                if not location_ids:  # If empty list, use a value that won't match anything
                    location_ids = [-1]
                online_locations = Location.query.filter(Location.id.in_(location_ids), Location.vpn_status==True).count()
                
            offline_locations = total_locations - online_locations
            
            # Get recent incidents
            if current_user.role.name == "Administrator":
                incident_count = Incident.query.filter_by(status='open').count()
            else:
                location_ids = [access.location_id for access in current_user.location_access]
                if not location_ids:  # If empty list, use a value that won't match anything
                    location_ids = [-1]
                incident_count = Incident.query.filter(
                    Incident.location_id.in_(location_ids),
                    Incident.status=='open'
                ).count()
            
            # Prepare response with safe values
            cpu = health.cpu_usage if health else default_cpu
            memory = health.memory_usage if health else default_memory
            storage = health.storage_usage if health else default_storage
            vpn_conn = health.vpn_connections if health else default_vpn
            
            return jsonify({
                'system': {
                    'cpu': cpu,
                    'memory': memory,
                    'storage': storage,
                    'vpn_connections': vpn_conn
                },
                'cameras': {
                    'total': total_cameras,
                    'online': online_cameras,
                    'offline': offline_cameras
                },
                'locations': {
                    'total': total_locations,
                    'online': online_locations,
                    'offline': offline_locations
                },
                'incidents': {
                    'open': incident_count
                }
            })
        except Exception as e:
            app.logger.error(f"Error in dashboard_stats: {str(e)}")
            return jsonify({
                'system': {'cpu': 0, 'memory': 0, 'storage': 0, 'vpn_connections': 0},
                'cameras': {'total': 0, 'online': 0, 'offline': 0},
                'locations': {'total': 0, 'online': 0, 'offline': 0},
                'incidents': {'open': 0}
            }), 200  # Return 200 even on error with default values
