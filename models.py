from datetime import datetime
from app import db
from flask_login import UserMixin


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    location_access = db.relationship('LocationAccess', backref='user', lazy=True)
    
    def has_access_to_location(self, location_id):
        # Admins have access to all locations
        if self.role.name == "Administrator":
            return True
        # Check if user has specific access to this location
        return any(access.location_id == location_id for access in self.location_access)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    vpn_status = db.Column(db.Boolean, default=False)
    last_online = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cameras = db.relationship('Camera', backref='location', lazy=True, cascade="all, delete-orphan")
    user_access = db.relationship('LocationAccess', backref='location', lazy=True, cascade="all, delete-orphan")
    incidents = db.relationship('Incident', backref='location', lazy=True)


class LocationAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rtsp_url = db.Column(db.String(255), nullable=False)
    shinobi_id = db.Column(db.String(100))
    shinobi_api_key = db.Column(db.String(100))
    shinobi_group_key = db.Column(db.String(100))
    status = db.Column(db.String(20), default="offline")  # online, offline, error
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    is_recording = db.Column(db.Boolean, default=False)
    is_ptz = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemHealth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    storage_usage = db.Column(db.Float)
    vpn_connections = db.Column(db.Integer)
    online_cameras = db.Column(db.Integer)
    offline_cameras = db.Column(db.Integer)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    snapshot_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default="open")  # open, closed, investigating
    severity = db.Column(db.String(20), default="medium")  # low, medium, high, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    camera = db.relationship('Camera', backref='incidents')
    reporter = db.relationship('User', backref='reported_incidents')
