# Shinobi Django CCTV System - Technical Documentation

## System Overview

The Shinobi Django CCTV System is a centralized video surveillance management platform designed to connect and monitor distributed camera networks across multiple geographic locations. Despite its name, the system is built using Flask (not Django) as the web framework and provides an enterprise-grade solution for security monitoring.

## Technical Architecture

### Technology Stack

#### Backend
- **Web Framework**: Flask 2.x
- **Database**: PostgreSQL 15.x
- **Authentication**: Flask-Login with role-based access control
- **Form Handling**: Flask-WTF with CSRF protection
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Video Processing**: Integration with Shinobi Video Server

#### Frontend
- **Template Engine**: Jinja2
- **UI Framework**: Bootstrap 5
- **JavaScript**: Vanilla JS for interactive features
- **Icons**: Bootstrap Icons

#### Deployment
- **Container**: Docker with docker-compose
- **Web Server**: Gunicorn
- **Database**: PostgreSQL in Docker

### Database Schema

The system utilizes a relational database with the following key entities:

1. **User**: System users with role-based access control
   - Roles: Administrator, Warehouse Manager, Security Operator, Viewer
   - Attributes: username, email, password_hash, role, etc.

2. **Location**: Physical locations/warehouses being monitored
   - Attributes: name, address, city, state, country, vpn_status, etc.
   - Relationships: has many cameras, has many user access permissions

3. **Camera**: Surveillance cameras at each location
   - Attributes: name, rtsp_url, status, is_recording, is_ptz, etc.
   - Relationships: belongs to location

4. **Incident**: Security incidents recorded in the system
   - Attributes: title, description, severity, status, etc.
   - Relationships: can be associated with camera and location

5. **SystemHealth**: System performance metrics
   - Attributes: cpu_usage, memory_usage, storage_usage, etc.

### Authentication & Authorization

The system uses a role-based access control model:

1. **Administrator**: Full access to all features and settings
2. **Warehouse Manager**: Access to specific locations and their cameras
3. **Security Operator**: Monitoring and basic camera controls
4. **Viewer**: View-only access to authorized cameras

### Integration with Shinobi

The system connects to the Shinobi Video Server API to:
- Retrieve camera status
- Control PTZ cameras (pan, tilt, zoom)
- Start/stop recording
- Capture snapshots

## Key Features

### Centralized Dashboard
- System health monitoring (CPU, memory, storage usage)
- Location and camera status overview
- Recent security incidents display

### Camera Management
- Live video streams via RTSP
- Camera status monitoring
- Recording controls
- PTZ camera controls

### Location Management
- Multi-site monitoring capabilities
- Location status tracking
- VPN connection status monitoring

### Incident Management
- Creation and tracking of security incidents
- Severity classification
- Status updates
- Associated camera snapshots

### System Health Monitoring
- Resource utilization tracking
- Connection status monitoring
- Performance metrics

## API Endpoints

The system provides several internal API endpoints for client-side functionality:

- `/api/dashboard/stats`: Dashboard statistics
- `/api/camera/{id}/status`: Camera status information
- `/api/camera/{id}/recording`: Recording control

## Deployment Instructions

### Docker Deployment

1. Clone the repository
2. Update environment variables in docker-compose.yml
3. Run `docker-compose up -d` to start the system
4. Access the web interface at http://localhost:5000
5. Log in with default credentials (admin/admin123)

### Environment Variables

Essential environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session encryption
- `FLASK_SECRET_KEY`: Flask application secret key

## Security Considerations

- Password hashing using Werkzeug's generate_password_hash
- CSRF protection using Flask-WTF
- Role-based access control
- SSL/TLS for production deployment (not included in docker-compose.yml)

## Backup and Recovery

- PostgreSQL data is persisted via Docker volume: postgres_data
- Static files and uploads are mounted as a volume: ./static/uploads:/app/static/uploads

## Scaling Considerations

- The docker-compose.yml file can be modified to include load balancing
- For high-availability deployments, consider:
  - Multiple web server instances
  - Database replication
  - Redis for session management
  - Centralized logging