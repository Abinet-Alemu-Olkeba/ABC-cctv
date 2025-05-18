from app import db, app
from models import User, Role
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Check if admin role exists
    admin_role = Role.query.filter_by(name='Administrator').first()
    if not admin_role:
        # Create admin role
        admin_role = Role(name='Administrator', description='System Administrator')
        db.session.add(admin_role)
        db.session.commit()
        print('Created Administrator role')
    
    # Check if admin user exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            role_id=admin_role.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Created admin user: admin/admin123')
    else:
        print('Admin user already exists')

