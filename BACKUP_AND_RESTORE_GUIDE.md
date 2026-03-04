# Savant Time Tracker - Backup & Restore Guide

## Quick Summary

The Time Tracker has a **comprehensive full system backup** feature that captures everything needed to restore the application on a fresh Ubuntu server with a single command.

### What's Included in Backups

✅ **Complete PostgreSQL Database** - All data including:
- Users table (with new `hire_date` and `pto_time` fields)
- Time entries (all hours tracked: Project, Admin, PTO, Holiday)
- Projects and project mappings
- Job task codes and categories
- Company holidays
- System configuration and preferences
- All relationships and constraints

✅ **All Application Files**:
- Python application code (`app.py`)
- All HTML templates (dashboard, time entry, bulk import, admin panels, etc.)
- Static files (CSS, JavaScript, images)
- Configuration files
- Requirements.txt for dependencies

✅ **Auto-Generated Restore Script** (`restore.sh`):
- Automated setup script that handles complete installation
- Installs all system dependencies (PostgreSQL, Python, Nginx, etc.)
- Creates system user and service
- Restores database with new credentials
- Sets up Python virtual environment
- Configures systemd service
- No manual configuration needed!

### What's Excluded from Backups

❌ Python virtual environment (`venv/`) - Recreated during restore
❌ Compiled Python files (`__pycache__/`) - Not needed
❌ Existing backup files - Prevents recursive backups
❌ Test files (`test_api.py`, `test_ui.py`) - Development files
❌ Network configuration backups - Server-specific
❌ Git repository data (`.git/`) - Not needed for restore

---

## How to Create a Backup

### Via Web Interface (Recommended)

1. **Login as Admin**
2. **Navigate to Admin Panel** → Click "System Backup"
3. **Click "Create Full Backup"** button
4. Wait 30-60 seconds while the system creates the backup
5. **Download the backup** from the "Available Backups" table

### Backup File Location

- **Storage Path**: `/opt/timetracker/backups/full/`
- **Filename Format**: `timetracker_backup_YYYYMMDD_HHMMSS.tar.gz`
- **Example**: `timetracker_backup_20260228_143025.tar.gz`

### Backup File Contents

When you extract a backup file, you'll find:

```
timetracker_backup_20260228_143025/
├── database.sql                    # Complete PostgreSQL dump
├── timetracker_files.tar.gz        # All application files
└── restore.sh                      # Automated restore script
```

---

## How to Restore a Backup

### Prerequisites

- Fresh Ubuntu 20.04/22.04/24.04 server
- Root access or sudo privileges
- Internet connection (for downloading dependencies)
- At least 2GB RAM recommended
- At least 10GB disk space

### Restore Process (Simple Method)

1. **Copy backup to new server**:
   ```bash
   scp timetracker_backup_20260228_143025.tar.gz user@new-server:~
   ```

2. **SSH into the new server**:
   ```bash
   ssh user@new-server
   ```

3. **Extract and run restore script**:
   ```bash
   tar xzf timetracker_backup_20260228_143025.tar.gz
   cd timetracker_backup_20260228_143025
   sudo bash restore.sh
   ```

4. **Wait for completion** (5-10 minutes)
   - The script will install all dependencies
   - Create database and restore data
   - Install Python packages
   - Configure and start the service

5. **Configure Nginx** (final step):
   ```bash
   sudo nano /etc/nginx/sites-available/timetracker
   ```

   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

6. **Access the application**:
   - Open browser to `http://your-server-ip`
   - Login with your existing credentials
   - All data, users, and settings are restored!

---

## What the Restore Script Does (Step-by-Step)

The `restore.sh` script automates the following 7 steps:

### [1/7] Installing System Packages
- Updates apt package lists
- Installs PostgreSQL database server
- Installs Python 3 and pip
- Installs Nginx web server
- Installs curl and other utilities

### [2/7] Creating System User
- Creates `timetracker` system user
- Sets up proper permissions
- Creates home directory at `/opt/timetracker`

### [3/7] Setting Up PostgreSQL Database
- Starts PostgreSQL service
- Generates a new random database password (16-character hex)
- Creates `timetracker` database user
- Creates `timetracker` database
- Grants all privileges

### [4/7] Restoring Application Files
- Extracts `timetracker_files.tar.gz` to `/opt/timetracker`
- Sets ownership to `timetracker:timetracker`
- Preserves file permissions

### [5/7] Installing Python Dependencies
- Creates Python virtual environment at `/opt/timetracker/venv`
- Installs all packages from `requirements.txt`:
  - Flask (web framework)
  - psycopg2-binary (PostgreSQL driver)
  - gunicorn (WSGI server)
  - python-dotenv (environment management)
  - Other dependencies

### [6/7] Restoring Database
- Connects to PostgreSQL using new credentials
- Imports complete database dump from `database.sql`
- Restores all tables, indexes, and constraints
- **ALL NEW FEATURES INCLUDED**:
  - User `hire_date` and `pto_time` columns
  - PTO tracking calculations
  - All time entries and projects
  - Company holidays
  - System preferences

### [7/7] Registering and Starting Service
- Creates systemd service file at `/etc/systemd/system/timetracker.service`
- Configures service to:
  - Start automatically on boot
  - Restart on failure
  - Run as `timetracker` user
  - Use 4 Gunicorn workers
  - Bind to `127.0.0.1:5000`
- Enables and starts the service

---

## Verification After Restore

### Check Service Status
```bash
sudo systemctl status timetracker
```

Expected output:
```
● timetracker.service - Savant Time Tracker
     Loaded: loaded (/etc/systemd/system/timetracker.service; enabled)
     Active: active (running) since ...
```

### Check Database Connection
```bash
sudo -u timetracker /opt/timetracker/venv/bin/python3 -c "
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv('/opt/timetracker/.env')
conn = psycopg2.connect(
    host='localhost',
    database='timetracker',
    user='timetracker',
    password=os.getenv('DB_PASSWORD')
)
print('✓ Database connection successful')
conn.close()
"
```

### Check Application Logs
```bash
sudo journalctl -u timetracker -f
```

### Test Web Interface
```bash
curl http://127.0.0.1:5000
```

Should return HTML content (login page).

---

## New Features Included in Backups

All recent feature additions are automatically included in backups:

### ✅ Employment Information
- User `hire_date` column (DATE)
- User `pto_time` column (DECIMAL)
- Optional fields on registration form
- Admin user management for employment data

### ✅ PTO Tracking & Dashboard
- Anniversary-based PTO year calculations
- PTO remaining hours
- PTO reset date (hire date anniversary)
- Days until PTO reset
- Enhanced dashboard PTO card with all calculations

### ✅ Admin Panel Color Scheme
- Unique colors for each admin section
- Purple for System Reports
- Teal for System Backup
- Custom CSS classes

### ✅ Bulk Import from Savant
- Tab-separated paste import
- 13-column format support
- Auto-detection of task categories
- Monday date selection

### ✅ All User Data
- User accounts and credentials
- Full names and email addresses
- Roles (user/admin)
- Last login timestamps
- Active/inactive status

### ✅ All Time Tracking Data
- Time entries with hours
- Categories (Project, Admin, PTO, Holiday)
- Job numbers and task codes
- Customer names and descriptions
- Entry dates and timestamps

### ✅ Project Configuration
- Project definitions
- Project-to-job mappings
- Task code definitions
- Category assignments

### ✅ System Configuration
- Company holidays
- System preferences
- Database schema and constraints
- Indexes and relationships

---

## Backup Management

### Via Web Interface

**Access**: Admin Panel → System Backup

**Operations**:
- **Create Backup**: Click "Create Full Backup" button
- **Download Backup**: Click download icon next to any backup
- **Delete Backup**: Click trash icon (requires confirmation)
- **Refresh List**: Click "Refresh" button to reload backup list

### Via Command Line

**List all backups**:
```bash
ls -lh /opt/timetracker/backups/full/
```

**Create manual backup** (alternative method):
```bash
# Backup database only
sudo -u postgres pg_dump -U timetracker timetracker > /tmp/timetracker_db_backup.sql

# Backup files only
sudo tar -czf /tmp/timetracker_files_backup.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='backups' \
    /opt/timetracker/
```

**Download backup**:
```bash
# From web interface
curl -O -J -L http://your-server/api/admin/download-backup/timetracker_backup_20260228_143025.tar.gz

# Direct file copy
scp user@server:/opt/timetracker/backups/full/timetracker_backup_20260228_143025.tar.gz .
```

---

## Best Practices

### Backup Frequency
- **Daily**: For production systems with active use
- **Weekly**: For smaller teams or testing environments
- **Before major changes**: Always backup before updates or configuration changes
- **Before migrations**: Backup before moving to new hardware

### Backup Storage
- **Keep 3+ recent backups**: Maintain at least 3 backup copies
- **Off-server storage**: Copy backups to a different physical location
- **Cloud storage**: Upload to AWS S3, Google Drive, or similar
- **Verify backups**: Periodically test restore process

### Security
- **Protect backup files**: Contain database credentials and user data
- **Encrypt backups**: Use GPG or similar for sensitive data
- **Secure transfer**: Use SCP/SFTP, not FTP or HTTP
- **Access control**: Limit who can create/download backups (admin only)

### Automation
Create a cron job for automatic daily backups:

```bash
# Add to /etc/cron.d/timetracker-backup
0 2 * * * timetracker curl -X POST http://localhost:5000/api/admin/create-full-backup
```

---

## Troubleshooting

### Restore Script Fails at Step 3 (PostgreSQL)

**Problem**: Database creation fails

**Solutions**:
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check PostgreSQL version
psql --version

# Reset PostgreSQL if needed
sudo systemctl restart postgresql
```

### Restore Script Fails at Step 6 (Database Import)

**Problem**: Database restore has errors

**Solutions**:
```bash
# Check database exists
sudo -u postgres psql -c "\l" | grep timetracker

# Manually restore with verbose output
sudo -u postgres psql timetracker < database.sql 2>&1 | tee restore.log

# Check for schema conflicts
sudo -u postgres psql -d timetracker -c "\dt"
```

### Application Won't Start After Restore

**Problem**: Service fails to start

**Solutions**:
```bash
# Check service status
sudo systemctl status timetracker

# View detailed logs
sudo journalctl -u timetracker -n 50

# Check .env file exists
ls -la /opt/timetracker/.env

# Verify Python dependencies
/opt/timetracker/venv/bin/pip list

# Test app manually
cd /opt/timetracker
source venv/bin/activate
python3 app.py
```

### Permission Errors

**Problem**: Application can't access files

**Solutions**:
```bash
# Fix ownership
sudo chown -R timetracker:timetracker /opt/timetracker

# Fix permissions
sudo chmod 755 /opt/timetracker
sudo chmod 644 /opt/timetracker/app.py
sudo chmod 600 /opt/timetracker/.env

# Check SELinux (if enabled)
sudo setenforce 0  # Temporarily disable to test
```

### Database Connection Errors

**Problem**: Can't connect to database

**Solutions**:
```bash
# Check .env file has correct credentials
sudo cat /opt/timetracker/.env

# Test PostgreSQL connection
sudo -u postgres psql -d timetracker

# Check PostgreSQL is listening
sudo netstat -tulpn | grep 5432

# Verify pg_hba.conf allows local connections
sudo cat /etc/postgresql/*/main/pg_hba.conf
```

---

## Summary

### Backup Process
1. Login as admin
2. Go to Admin → System Backup
3. Click "Create Full Backup"
4. Download the `.tar.gz` file
5. Store safely off-server

### Restore Process
1. Copy backup to new Ubuntu server
2. Extract: `tar xzf timetracker_backup_*.tar.gz`
3. Run: `sudo bash restore.sh`
4. Configure Nginx proxy
5. Access application

### What's Backed Up
✅ Complete database (all new features included)
✅ All application code and templates
✅ Configuration files
✅ Python dependencies list
✅ Auto-restore script

### What's NOT Backed Up
❌ Virtual environment (recreated)
❌ Log files
❌ Temporary files
❌ Server-specific configs (network, etc.)

---

## Support

**Documentation**: See `/opt/timetracker/COMPLETE_TIMETRACKER_SYSTEM_DOCUMENTATION.md`

**Logs**: `sudo journalctl -u timetracker -f`

**Service Management**:
- Start: `sudo systemctl start timetracker`
- Stop: `sudo systemctl stop timetracker`
- Restart: `sudo systemctl restart timetracker`
- Status: `sudo systemctl status timetracker`

**Database Access**:
```bash
# As timetracker user
sudo -u timetracker psql

# View .env for credentials
sudo cat /opt/timetracker/.env
```

---

**Generated**: 2026-02-28
**System**: Savant Time Tracker v2.0
**Backup System Version**: Full System Backup with Auto-Restore
