# OralHealth Deployment Guide

## VPS Deployment Instructions for oralhealth.xeradb.com

This guide provides step-by-step instructions to deploy the OralHealth Django application to your VPS.

### Prerequisites

- VPS with Ubuntu 20.04+ or similar
- Domain: oralhealth.xeradb.com pointing to your VPS
- PostgreSQL database
- Python 3.8+
- Nginx
- SSL certificate (Let's Encrypt recommended)

### Database Configuration

Your PostgreSQL database is already configured:
- **Database name**: `oralhealth_production`
- **Username**: `oralhealth_user`
- **Password**: `Choxos10203040`
- **Host**: `localhost`

### Step 1: Prepare the VPS Environment

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git supervisor

# Install Node.js (for frontend build tools if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 2: Create PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user (if not already created)
CREATE DATABASE oralhealth_production;
CREATE USER oralhealth_user WITH PASSWORD 'Choxos10203040';
GRANT ALL PRIVILEGES ON DATABASE oralhealth_production TO oralhealth_user;
ALTER USER oralhealth_user CREATEDB;
\q
```

### Step 3: Deploy Application Code

```bash
# Navigate to web directory
cd /var/www

# Clone the repository
sudo git clone https://github.com/choxos/oralhealth.git
sudo chown -R www-data:www-data oralhealth
cd oralhealth

# Create virtual environment
sudo -u www-data python3 -m venv venv
sudo -u www-data ./venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u www-data ./venv/bin/pip install -r requirements.txt
sudo -u www-data ./venv/bin/pip install gunicorn psycopg2-binary dj-database-url
```

### Step 4: Configure Environment Variables

```bash
# Create environment file
sudo -u www-data touch /var/www/oralhealth/.env

# Add configuration to .env file
sudo tee /var/www/oralhealth/.env > /dev/null <<EOL
# Production settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=oralhealth.xeradb.com,localhost,127.0.0.1

# Database configuration
DATABASE_URL=postgresql://oralhealth_user:Choxos10203040@localhost:5432/oralhealth_production

# Additional settings
STATIC_ROOT=/var/www/oralhealth/staticfiles
MEDIA_ROOT=/var/www/oralhealth/media
EOL

# Set proper permissions
sudo chown www-data:www-data /var/www/oralhealth/.env
sudo chmod 600 /var/www/oralhealth/.env
```

### Step 5: Initialize Django Application

```bash
# Run migrations
sudo -u www-data ./venv/bin/python manage.py makemigrations
sudo -u www-data ./venv/bin/python manage.py migrate

# Collect static files
sudo -u www-data ./venv/bin/python manage.py collectstatic --noinput

# Create superuser (optional)
sudo -u www-data ./venv/bin/python manage.py createsuperuser

# Populate with initial data
sudo -u www-data ./venv/bin/python manage.py populate_uk_guidelines
sudo -u www-data ./venv/bin/python manage.py import_cochrane_sof
```

### Step 6: Configure Gunicorn

```bash
# Create Gunicorn configuration
sudo tee /var/www/oralhealth/gunicorn_config.py > /dev/null <<EOL
import multiprocessing

# Server socket
bind = "127.0.0.1:8008"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "/var/log/oralhealth/access.log"
errorlog = "/var/log/oralhealth/error.log"

# Process naming
proc_name = "oralhealth"

# Server mechanics
daemon = False
pidfile = "/var/run/oralhealth.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
EOL

# Create log directory
sudo mkdir -p /var/log/oralhealth
sudo chown www-data:www-data /var/log/oralhealth
```

### Step 7: Configure Supervisor

```bash
# Create supervisor configuration
sudo tee /etc/supervisor/conf.d/oralhealth.conf > /dev/null <<EOL
[program:oralhealth]
command=/var/www/oralhealth/venv/bin/gunicorn --config gunicorn_config.py oralhealth.wsgi:application
directory=/var/www/oralhealth
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/oralhealth/supervisor.log
stderr_logfile=/var/log/oralhealth/supervisor_error.log
environment=PATH="/var/www/oralhealth/venv/bin"
EOL

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start oralhealth
```

### Step 8: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/oralhealth.xeradb.com > /dev/null <<EOL
upstream oralhealth_app {
    server 127.0.0.1:8008;
}

server {
    listen 80;
    server_name oralhealth.xeradb.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name oralhealth.xeradb.com;

    # SSL Configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/oralhealth.xeradb.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/oralhealth.xeradb.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Application settings
    client_max_body_size 75M;
    keepalive_timeout 5;

    # Static files
    location /static/ {
        alias /var/www/oralhealth/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/oralhealth/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Application
    location / {
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://oralhealth_app;
    }

    # Favicon
    location /favicon.ico {
        alias /var/www/oralhealth/staticfiles/images/favicon.ico;
    }

    # Robots.txt
    location /robots.txt {
        alias /var/www/oralhealth/staticfiles/robots.txt;
    }
}
EOL

# Enable site
sudo ln -sf /etc/nginx/sites-available/oralhealth.xeradb.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 9: SSL Certificate with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d oralhealth.xeradb.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 10: Create Update Script

```bash
# Create deployment script
sudo tee /var/www/oralhealth/deploy.sh > /dev/null <<EOL
#!/bin/bash

echo "Starting OralHealth deployment..."

# Navigate to project directory
cd /var/www/oralhealth

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Update data if needed
python manage.py populate_uk_guidelines
python manage.py import_cochrane_sof

# Restart application
sudo supervisorctl restart oralhealth

# Reload nginx
sudo systemctl reload nginx

echo "Deployment completed successfully!"
EOL

# Make script executable
sudo chmod +x /var/www/oralhealth/deploy.sh
sudo chown www-data:www-data /var/www/oralhealth/deploy.sh
```

### Step 11: Database Backup Script

```bash
# Create backup script
sudo tee /var/www/oralhealth/backup_db.sh > /dev/null <<EOL
#!/bin/bash

BACKUP_DIR="/var/backups/oralhealth"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="oralhealth_backup_\$DATE.sql"

# Create backup directory
mkdir -p \$BACKUP_DIR

# Create database backup
pg_dump -h localhost -U oralhealth_user -d oralhealth_production > \$BACKUP_DIR/\$BACKUP_FILE

# Compress backup
gzip \$BACKUP_DIR/\$BACKUP_FILE

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: \$BACKUP_FILE.gz"
EOL

# Make script executable
sudo chmod +x /var/www/oralhealth/backup_db.sh

# Add to crontab for daily backups
sudo crontab -l | { cat; echo "0 2 * * * /var/www/oralhealth/backup_db.sh"; } | sudo crontab -
```

### Step 12: Monitoring and Logs

```bash
# View application logs
sudo tail -f /var/log/oralhealth/supervisor.log

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check application status
sudo supervisorctl status oralhealth

# Restart application
sudo supervisorctl restart oralhealth
```

### Troubleshooting

1. **Database connection issues:**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test database connection
   sudo -u www-data psql -h localhost -U oralhealth_user -d oralhealth_production
   ```

2. **Permission issues:**
   ```bash
   # Fix ownership
   sudo chown -R www-data:www-data /var/www/oralhealth
   
   # Fix permissions
   sudo chmod -R 755 /var/www/oralhealth
   sudo chmod 600 /var/www/oralhealth/.env
   ```

3. **Static files not loading:**
   ```bash
   # Collect static files
   sudo -u www-data ./venv/bin/python manage.py collectstatic --noinput
   
   # Check nginx configuration
   sudo nginx -t
   ```

### Maintenance

- **Update application:** Run `/var/www/oralhealth/deploy.sh`
- **Backup database:** Run `/var/www/oralhealth/backup_db.sh`
- **View logs:** Check `/var/log/oralhealth/` directory
- **Monitor performance:** Use Django Debug Toolbar in development

### Security Notes

1. Change the SECRET_KEY in production
2. Keep dependencies updated
3. Regularly backup the database
4. Monitor access logs for suspicious activity
5. Use strong passwords for database users
6. Keep SSL certificates updated

Your OralHealth application should now be accessible at https://oralhealth.xeradb.com