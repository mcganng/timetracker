#!/bin/bash

# ========================================
# Savant Time Tracker - Automated Installation Script
# For Ubuntu 20.04 LTS or later
# ========================================

set -e

echo "========================================="
echo " Savant Time Tracker - Installation"
echo "========================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Get actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}

# Prompt for configuration
echo "Please provide the following information:"
echo ""

read -p "Database password for 'timetracker' user: " DB_PASSWORD
read -p "Flask secret key (press Enter to generate): " SECRET_KEY

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    echo "Generated secret key: $SECRET_KEY"
fi

read -p "Your domain or IP address (e.g., timetracker.example.com or 192.168.1.100): " DOMAIN

echo ""
echo "========================================="
echo " Starting Installation..."
echo "========================================="
echo ""

# Step 1: Update system
echo "[1/10] Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install required packages
echo "[2/10] Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git ufw

# Step 3: Create application user
echo "[3/10] Creating application user..."
if ! id -u timetracker > /dev/null 2>&1; then
    adduser --system --group --home /opt/timetracker timetracker
fi
usermod -a -G timetracker www-data

# Step 4: Setup PostgreSQL database
echo "[4/10] Setting up PostgreSQL database..."
sudo -u postgres psql << SQL
DROP DATABASE IF EXISTS timetracker;
DROP USER IF EXISTS timetracker;
CREATE DATABASE timetracker;
CREATE USER timetracker WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;
ALTER DATABASE timetracker OWNER TO timetracker;
SQL

# Step 5: Install application files
echo "[5/10] Installing application files..."
mkdir -p /opt/timetracker
cd /opt/timetracker

# Create directory structure
mkdir -p templates static/css static/js database

# Copy application files (assuming they're in the same directory as this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r $SCRIPT_DIR/* /opt/timetracker/ 2>/dev/null || true

# Handle templates_git and database_git directories (if cloned from git repo)
if [ -d "$SCRIPT_DIR/templates_git" ]; then
    echo "   Copying templates from templates_git..."
    cp -r $SCRIPT_DIR/templates_git/* /opt/timetracker/templates/
fi
if [ -d "$SCRIPT_DIR/database_git" ]; then
    echo "   Copying database schema from database_git..."
    cp -r $SCRIPT_DIR/database_git/* /opt/timetracker/database/
fi

# Set ownership
chown -R timetracker:timetracker /opt/timetracker

# Step 6: Setup Python environment
echo "[6/10] Setting up Python virtual environment..."
sudo -u timetracker python3 -m venv /opt/timetracker/venv
sudo -u timetracker /opt/timetracker/venv/bin/pip install --upgrade pip
sudo -u timetracker /opt/timetracker/venv/bin/pip install -r /opt/timetracker/requirements.txt

# Step 7: Load database schema
echo "[7/10] Loading database schema..."
sudo -u timetracker PGPASSWORD=$DB_PASSWORD psql -U timetracker -d timetracker -f /opt/timetracker/database/schema.sql

# Step 8: Create environment file
echo "[8/10] Creating environment configuration..."
cat > /opt/timetracker/.env << ENV
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432
APP_HOST=0.0.0.0
APP_PORT=5000
ENV

chown timetracker:timetracker /opt/timetracker/.env
chmod 600 /opt/timetracker/.env

# Step 9: Create systemd service
echo "[9/10] Creating systemd service..."
cat > /etc/systemd/system/timetracker.service << SERVICE
[Unit]
Description=Savant Time Tracker Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=timetracker
Group=timetracker
WorkingDirectory=/opt/timetracker
Environment="PATH=/opt/timetracker/venv/bin"
EnvironmentFile=/opt/timetracker/.env
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 app:app
Restart=always
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/timetracker

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable timetracker
systemctl start timetracker

# Step 10: Configure Nginx
echo "[10/10] Configuring Nginx..."
cat > /etc/nginx/sites-available/timetracker << NGINX
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /opt/timetracker/static;
        expires 30d;
    }

    access_log /var/log/nginx/timetracker_access.log;
    error_log /var/log/nginx/timetracker_error.log;
}
NGINX

ln -sf /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Configure firewall
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Create backup script
cat > /opt/timetracker/backup.sh << 'BACKUP'
#!/bin/bash
BACKUP_DIR="/opt/timetracker/backups"
DB_NAME="timetracker"
DB_USER="timetracker"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR
PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
BACKUP

chmod +x /opt/timetracker/backup.sh
chown timetracker:timetracker /opt/timetracker/backup.sh

# Setup daily backup cron job
(crontab -u timetracker -l 2>/dev/null; echo "0 2 * * * /opt/timetracker/backup.sh >> /opt/timetracker/backup.log 2>&1") | crontab -u timetracker -

echo ""
echo "========================================="
echo " Installation Complete!"
echo "========================================="
echo ""
echo "Access your application at: http://$DOMAIN"
echo ""
echo "Important next steps:"
echo "  1. Create your first user account"
echo "  2. Configure SSL certificate (recommended):"
echo "     sudo apt install certbot python3-certbot-nginx"
echo "     sudo certbot --nginx -d $DOMAIN"
echo "  3. Test backup script:"
echo "     sudo -u timetracker /opt/timetracker/backup.sh"
echo ""
echo "Useful commands:"
echo "  Check status:    sudo systemctl status timetracker"
echo "  View logs:       sudo journalctl -u timetracker -f"
echo "  Restart app:     sudo systemctl restart timetracker"
echo "  Backup database: sudo -u timetracker /opt/timetracker/backup.sh"
echo ""
echo "Database credentials:"
echo "  Database: timetracker"
echo "  User:     timetracker"
echo "  Password: $DB_PASSWORD"
echo "  (Saved in: /opt/timetracker/.env)"
echo ""
