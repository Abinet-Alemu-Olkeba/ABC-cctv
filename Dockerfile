FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir gunicorn psycopg2-binary 
RUN pip install --no-cache-dir flask flask-sqlalchemy flask-login flask-wtf werkzeug email-validator

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py

# Create non-root user for security
RUN useradd -m shinobi
USER shinobi

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "main:app"]