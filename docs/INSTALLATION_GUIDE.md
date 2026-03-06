# Savant Time Tracker - Complete Installation Guide

Self-hosted web application for time tracking with PostgreSQL database backend.

## System Requirements

- **OS:** Ubuntu 20.04 LTS or later (tested on 20.04 and 22.04)
- **RAM:** Minimum 2GB (4GB recommended)
- **Disk:** Minimum 10GB free space
- **Network:** Static IP or domain name recommended
- **Ports:** 80 (HTTP), 443 (HTTPS - optional), 5432 (PostgreSQL - internal only)

---

## Quick Start (15 Minutes)

For those who want to get running quickly:

```bash
# 1. Download installation script
wget https://your-server/install.sh
chmod +x install.sh

# 2. Run installation
sudo ./install.sh

# 3. Access application
# Open browser to: http://your-server-ip
```

---

## Complete Installation Guide

### Step 1: Update System

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git
```

### Step 2: Create Application User

```bash
# Create dedicated user for the application
sudo adduser --system --group --home /opt/timetracker timetracker

# Add nginx to timetracker group
sudo usermod -a -G timetracker www-data
```

### Step 3: Setup PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run these commands:
CREATE DATABASE timetracker;
CREATE USER timetracker WITH PASSWORD 'change_this_password';
GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;
\q

# Load database schema
sudo -u timetracker psql -U timetracker -d timetracker -f /path/to/schema.sql
```

**IMPORTANT:** Change `'change_this_password'` to a strong password!

### Step 4: Install Application

```bash
# Create application directory
sudo mkdir -p /opt/timetracker
sudo chown timetracker:timetracker /opt/timetracker

# Switch to timetracker user
sudo su - timetracker

# Clone or copy application files to /opt/timetracker
# Your directory structure should be:
# /opt/timetracker/
# ├── app.py
# ├── requirements.txt
# ├── templates/
# ├── static/
# └── database/

# Create Python virtual environment
cd /opt/timetracker
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Exit timetracker user
exit
```

### Step 5: Configure Environment Variables

```bash
# Create environment file
sudo nano /opt/timetracker/.env
```

Add this content (adjust values):

```bash
# Flask Configuration
SECRET_KEY=generate_random_secret_key_here
FLASK_ENV=production

# Database Configuration
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=your_database_password_here
DB_PORT=5432

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=5000
```

**Generate SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### Step 6: Create Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/timetracker.service
```

Add this content:

```ini
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

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/timetracker

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable timetracker
sudo systemctl start timetracker

# Check status
sudo systemctl status timetracker
```

### Step 7: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/timetracker
```

Add this content:

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # Increase timeouts for long-running requests
    client_max_body_size 10M;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/timetracker/static;
        expires 30d;
    }

    # Logging
    access_log /var/log/nginx/timetracker_access.log;
    error_log /var/log/nginx/timetracker_error.log;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 8: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Step 9: SSL Certificate (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Step 10: Create First User

```bash
# Access the application via browser
# Navigate to: http://your-server-ip

# Click "Register" and create your first user account
```

When creating an account, you'll see:
- **Required fields:** Full Name, Username, Email, Password
- **Optional fields:** Date of Hire, Total PTO Time (in hours)

The optional employment fields allow tracking of:
- When each user was hired
- Total PTO hours available for each user
- Admins can edit these values later in User Management

---

## Using the Application

### Regular User Features

Once logged in, users can:
- **Dashboard** - View utilization metrics and project hours
- **Time Entry** - Log time against projects and admin codes
- **Projects** - View active and closed projects
- **Configuration** - View job codes and holidays

### Admin Features

Users with admin role can access additional features via the **Admin** menu:

1. **User Management** (`/admin/user-management`)
   - View all user accounts with hire dates and PTO balances
   - Edit employment information (hire date, PTO time) for any user
   - Change passwords for any user
   - Activate/deactivate user accounts
   - Delete user accounts

2. **Manage User Data** (`/admin/manage-user-data`)
   - View and edit time entries for any user
   - Bulk manage project assignments

3. **Server Config** (`/admin/server-config`)
   - Configure timezone and NTP servers
   - View network settings
   - Manage server information

4. **Code Editor** (`/admin/code-editor`)
   - Edit application templates and files
   - Make configuration changes

5. **System Reports** (`/admin/reports`)
   - View project hours across all users
   - Analyze team utilization metrics
   - Generate summary reports

6. **System Backup** (`/admin/system-backup`)
   - Create full system backups (database + files)
   - Download backup archives
   - Restore from previous backups
   - Manage backup files

---

## Backup and Restore

### Automated Daily Backup Setup

Create backup script:

```bash
sudo nano /opt/timetracker/backup.sh
```

Add this content:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/timetracker/backups"
DB_NAME="timetracker"
DB_USER="timetracker"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Remove old backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

```bash
# Make executable
sudo chmod +x /opt/timetracker/backup.sh
sudo chown timetracker:timetracker /opt/timetracker/backup.sh

# Create cron job for daily backup at 2 AM
sudo crontab -e -u timetracker
```

Add this line:

```
0 2 * * * /opt/timetracker/backup.sh >> /opt/timetracker/backup.log 2>&1
```

### Manual Backup

```bash
# Backup database
sudo -u timetracker pg_dump -U timetracker timetracker > /tmp/timetracker_backup.sql

# Compress
gzip /tmp/timetracker_backup.sql

# Copy to safe location
cp /tmp/timetracker_backup.sql.gz /path/to/safe/location/
```

### Restore from Backup

```bash
# Stop application
sudo systemctl stop timetracker

# Drop existing database (WARNING: This deletes all data!)
sudo -u postgres psql -c "DROP DATABASE IF EXISTS timetracker;"
sudo -u postgres psql -c "CREATE DATABASE timetracker;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;"

# Restore from backup
gunzip -c /path/to/backup/db_backup_XXXXXXXX.sql.gz | sudo -u timetracker psql -U timetracker timetracker

# Start application
sudo systemctl start timetracker
```

---

## Monitoring and Maintenance

### Check Application Status

```bash
# Check service status
sudo systemctl status timetracker

# View logs
sudo journalctl -u timetracker -f

# Check Nginx logs
sudo tail -f /var/log/nginx/timetracker_access.log
sudo tail -f /var/log/nginx/timetracker_error.log
```

### Database Maintenance

```bash
# Connect to database
sudo -u timetracker psql -U timetracker timetracker

# In PostgreSQL prompt:

# Check database size
SELECT pg_size_pretty(pg_database_size('timetracker'));

# Vacuum database (clean up)
VACUUM ANALYZE;

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Update Application

```bash
# Stop service
sudo systemctl stop timetracker

# Backup database first!
sudo -u timetracker /opt/timetracker/backup.sh

# Update code
cd /opt/timetracker
sudo -u timetracker git pull  # or copy new files

# Update dependencies if needed
sudo -u timetracker /opt/timetracker/venv/bin/pip install -r requirements.txt

# Run any database migrations if needed
# sudo -u timetracker psql -U timetracker timetracker -f migrations/001_migration.sql

# Start service
sudo systemctl start timetracker

# Check status
sudo systemctl status timetracker
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u timetracker -n 50 --no-pager

# Common issues:
# 1. Database connection - check .env file
# 2. Port already in use - check with: sudo netstat -tlnp | grep 5000
# 3. Python package issues - reinstall: pip install -r requirements.txt
```

### Can't Connect to Database

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"

# Check password in .env file matches database
```

### Nginx 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status timetracker

# Check if application is listening on port 5000
sudo netstat -tlnp | grep 5000

# Check Nginx error log
sudo tail -f /var/log/nginx/timetracker_error.log
```

### Slow Performance

```bash
# Check database performance
sudo -u timetracker psql -U timetracker timetracker

# In PostgreSQL:
# Check slow queries
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Add indexes if needed (already included in schema)

# Increase Gunicorn workers in systemd service
# Edit: /etc/systemd/system/timetracker.service
# Change: --workers 4  to  --workers 8
```

---

## Security Best Practices

### 1. Change Default Passwords

```bash
# Change database password
sudo -u postgres psql
ALTER USER timetracker WITH PASSWORD 'new_secure_password';
\q

# Update .env file with new password
sudo nano /opt/timetracker/.env
```

### 2. Enable HTTPS (SSL)

Use Let's Encrypt (see Step 9 above) or your own SSL certificate.

### 3. Regular Updates

```bash
# Update system packages monthly
sudo apt update && sudo apt upgrade -y

# Update Python packages quarterly
sudo -u timetracker /opt/timetracker/venv/bin/pip list --outdated
```

### 4. Firewall Configuration

```bash
# Only allow necessary ports
sudo ufw status
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 5. Database Security

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ensure database only listens locally
# Change:
# host    all             all             0.0.0.0/0               md5
# To:
# host    all             all             127.0.0.1/32            md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Scaling and Performance

### Increase Workers

Edit `/etc/systemd/system/timetracker.service`:

```ini
# For 4GB RAM server
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 8 --bind 127.0.0.1:5000 app:app

# For 8GB RAM server
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 16 --bind 127.0.0.1:5000 app:app
```

### Database Tuning

Edit `/etc/postgresql/*/main/postgresql.conf`:

```ini
# For 4GB RAM server
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 5242kB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL: `sudo systemctl restart postgresql`

---

## Remote Access Setup

### Access from Another Computer

If you want to access the application from computers on your network:

1. **Find server IP:**
```bash
ip addr show | grep inet
```

2. **Access via browser:**
```
http://server-ip-address
```

### Access from Internet

1. **Configure router port forwarding:**
   - Forward port 80 (HTTP) to server IP
   - Forward port 443 (HTTPS) to server IP

2. **Use dynamic DNS** (if no static IP):
   - Services: DuckDNS, No-IP, Dynu
   - Install DDNS client on server

3. **Security considerations:**
   - MUST use HTTPS if accessing over internet
   - Consider VPN instead of exposing directly
   - Use strong passwords for all accounts

---

## Migration from Excel

### Import Existing Data

Create migration script:

```python
# migrate_excel.py
import pandas as pd
import psycopg2
from datetime import datetime

# Read Excel file
df = pd.read_excel('savant_time_tracker.xlsx', sheet_name='Master Log', header=1)

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='timetracker',
    user='timetracker',
    password='your_password'
)
cur = conn.cursor()

# Import data
for _, row in df.iterrows():
    cur.execute('''
        INSERT INTO time_entries 
        (user_id, entry_date, job_number, job_task_code, description, 
         hours, category, customer_name, job_description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        1,  # user_id - adjust as needed
        row['Date'],
        row['Job Number'],
        row['Job Task No'],
        row['Description'],
        row['Hours'],
        row['Category'],
        row['Customer Name'],
        row['Job Description']
    ))

conn.commit()
cur.close()
conn.close()
```

Run: `python3 migrate_excel.py`

---

## Uninstallation

If you need to remove the application:

```bash
# Stop and disable service
sudo systemctl stop timetracker
sudo systemctl disable timetracker

# Remove service file
sudo rm /etc/systemd/system/timetracker.service
sudo systemctl daemon-reload

# Remove Nginx configuration
sudo rm /etc/nginx/sites-enabled/timetracker
sudo rm /etc/nginx/sites-available/timetracker
sudo systemctl restart nginx

# Backup database first!
sudo -u timetracker pg_dump timetracker > ~/timetracker_final_backup.sql

# Drop database
sudo -u postgres psql -c "DROP DATABASE timetracker;"
sudo -u postgres psql -c "DROP USER timetracker;"

# Remove application files
sudo rm -rf /opt/timetracker

# Remove system user
sudo deluser --remove-home timetracker
```

---

## Support and Documentation

### Log Files

- Application: `sudo journalctl -u timetracker`
- Nginx Access: `/var/log/nginx/timetracker_access.log`
- Nginx Error: `/var/log/nginx/timetracker_error.log`
- Backup: `/opt/timetracker/backup.log`

### Common Tasks Reference

**Restart application:**
```bash
sudo systemctl restart timetracker
```

**View live logs:**
```bash
sudo journalctl -u timetracker -f
```

**Create backup:**
```bash
sudo -u timetracker /opt/timetracker/backup.sh
```

**Check disk space:**
```bash
df -h
```

**Check memory usage:**
```bash
free -h
```

---

## Next Steps

After installation:

1. ✅ Create your first user account
2. ✅ Configure job task codes and projects
3. ✅ Start entering time entries
4. ✅ Set up automated backups
5. ✅ Configure SSL certificate
6. ✅ Test backup restoration
7. ✅ Document your specific configuration
8. ✅ Train users on the system

**Important:** Change all default passwords and keep backups in a safe location!
