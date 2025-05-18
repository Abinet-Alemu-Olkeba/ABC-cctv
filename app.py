import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "super-secure-shinobi-key123456789")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = False  # Temporarily disable CSRF to simplify login process

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

with app.app_context():
    # Import models to create tables
    import models
    
    # Initialize database
    db.create_all()
    
    # Create admin user if none exists
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    # Create roles if they don't exist
    if not Role.query.filter_by(name="Administrator").first():
        admin_role = Role(name="Administrator", description="Full system access")
        manager_role = Role(name="Warehouse Manager", description="Access to assigned warehouses")
        security_role = Role(name="Security Operator", description="Monitoring and basic controls")
        viewer_role = Role(name="Viewer", description="View-only access")
        
        db.session.add_all([admin_role, manager_role, security_role, viewer_role])
        db.session.commit()
    
    # Create admin user if none exists
    if not User.query.filter_by(username="admin").first():
        admin_role = Role.query.filter_by(name="Administrator").first()
        admin = User(
            username="admin",
            email="admin@shinobi.system",
            password_hash=generate_password_hash("admin123"),
            first_name="System",
            last_name="Administrator",
            role_id=admin_role.id,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
