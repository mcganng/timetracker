# Savant Time Tracker - Web Application

Complete self-hosted time tracking system with web interface and PostgreSQL database.

## 📋 Features

- ✅ **Dashboard** - Real-time utilization metrics, project tracking, charts
- ✅ **Time Entry** - Easy time logging with job codes and categories
- ✅ **Project Management** - Budget tracking, Active/Closed status
- ✅ **Configuration** - Manage job codes, admin codes, holidays
- ✅ **Multi-user** - Secure login with user authentication
- ✅ **Employment Information** - Track hire dates and PTO balances for all users
- ✅ **Export** - CSV export for reporting
- ✅ **Automated Backups** - Daily database backups + full on-demand backups via Admin UI
- ✅ **System Reports** - Admin dashboard for project hours and team utilization
- ✅ **System Backup UI** - Create/download/restore full backups from the browser
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

## 🚀 Quick Installation (Ubuntu 20.04+)

```bash
# 1. Download the files
git clone <your-repo> timetracker
cd timetracker

# 2. Run automated installation
sudo ./install.sh

# 3. Access application
# Open browser to: http://your-server-ip
```

The installation script will:
- Install all dependencies (Python, PostgreSQL, Nginx)
- Create database and user
- Configure application and web server
- Set up automated daily backups
- Configure firewall

## 📦 What's Included

```
timetracker/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── install.sh               # Automated installation script
├── INSTALLATION_GUIDE.md    # Detailed manual installation
├── README.md                # This file
├── database/
│   └── schema.sql           # PostgreSQL database schema
├── templates/
│   ├── base.html            # Base template
│   ├── login.html           # Login/register page
│   ├── dashboard.html       # Dashboard with metrics
│   ├── time_entry.html      # Time entry form
│   ├── projects.html        # Project management
│   └── config.html          # Configuration page
└── static/
    └── css/
        └── style.css        # Custom styling
```

## 💻 System Requirements

- **OS:** Ubuntu 20.04 LTS or later
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 10GB free space
- **Network:** Static IP or domain name

## 🔧 Manual Installation

If you prefer step-by-step installation, see `INSTALLATION_GUIDE.md` for complete instructions.

## 📊 Usage

### First Time Setup

1. **Access the application** at `http://your-server-ip`
2. **Click "Create Account"** and register your first user
   - Required: Full Name, Username, Email, Password
   - Optional: Date of Hire, Total PTO Time (hours)
3. **Log in** with your credentials
4. **Add projects** in the Projects section
5. **Start logging time** in Time Entry

### Daily Workflow

1. **Navigate to Time Entry**
2. **Select date** and job details
3. **Enter hours** and description
4. **Click "Add Entry"**
5. **View Dashboard** to see utilization metrics

### Dashboard Features

- **Summary Metrics** - Total hours, project/admin breakdown
- **Utilization Tracking** - Project and admin utilization %
- **Active Projects** - Budget tracking with progress bars
- **Charts** - Visual breakdown of project hours by task
- **Date Range Filtering** - View any time period
- **CSV Export** - Download data for external reporting

### Admin Features

Admins have access to additional management capabilities:

- **User Management** - Create, edit, deactivate users, change passwords
  - View and edit hire dates for all users
  - Manage PTO time balances for all users
- **Manage User Data** - Edit time entries for any user
- **Server Configuration** - Timezone, NTP, network settings
- **Code Editor** - Edit application files directly
- **System Reports** - View project hours and team utilization metrics
- **System Backup** - Create, download, and restore full system backups

## 🔐 Security

### Default Settings

- Database access limited to localhost only
- Application runs as dedicated system user
- Nginx reverse proxy for web access
- Session-based authentication

### Recommended Security Steps

1. **Enable HTTPS:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

2. **Strong Passwords:**
   - Use strong database password during installation
   - Enforce strong user passwords

3. **Firewall:**
```bash
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
```

4. **Regular Updates:**
```bash
sudo apt update && sudo apt upgrade -y
```

## 💾 Backup & Restore

### Option A — Admin Panel (Recommended)

Log in as admin and navigate to **Admin → System Backup** to:
- Create a full backup (database + all app files) with one click
- Download the `.tar.gz` archive to store off-server
- Manage and delete old backups

Each backup bundle contains:
- `database.sql` — Full PostgreSQL dump
- `timetracker_files.tar.gz` — All application files  
- `restore.sh` — One-command restore script for a new Ubuntu server

### Option B — Command Line (Database only)

```bash
# Automated: Daily at 2 AM
# Backups stored in: /opt/timetracker/backups/
# Format: db_backup_YYYYMMDD_HHMMSS.sql.gz

# Manual:
sudo -u timetracker /opt/timetracker/backup.sh
```

### Restoring to a New Server (from Full Backup)

```bash
# 1. Copy the backup to the new server
scp timetracker_backup_YYYYMMDD_HHMMSS.tar.gz user@new-server:~

# 2. On the new server, extract and restore
tar xzf timetracker_backup_YYYYMMDD_HHMMSS.tar.gz
sudo bash restore.sh
```

The restore script installs all dependencies, creates the database, and starts the service automatically.

### Legacy Database-Only Restore

```bash
sudo systemctl stop timetracker
gunzip -c /opt/timetracker/backups/db_backup_XXXXXXXX.sql.gz | \
  sudo -u timetracker psql -U timetracker timetracker
sudo systemctl start timetracker
```

## 🔍 Monitoring & Maintenance

### Check Application Status

```bash
# View service status
sudo systemctl status timetracker

# View live logs
sudo journalctl -u timetracker -f

# Check database connection
sudo -u timetracker psql -U timetracker timetracker -c "SELECT COUNT(*) FROM time_entries;"
```

### Common Commands

```bash
# Restart application
sudo systemctl restart timetracker

# View Nginx logs
sudo tail -f /var/log/nginx/timetracker_access.log
sudo tail -f /var/log/nginx/timetracker_error.log

# Check disk space
df -h

# Check memory usage
free -h

# View database size
sudo -u timetracker psql -U timetracker timetracker \
  -c "SELECT pg_size_pretty(pg_database_size('timetracker'));"
```

## 🆘 Troubleshooting

### Application Won't Start

```bash
# Check logs for errors
sudo journalctl -u timetracker -n 50 --no-pager

# Common issues:
# 1. Database connection - check /opt/timetracker/.env
# 2. Port in use - check: sudo netstat -tlnp | grep 5000
# 3. Python errors - check dependencies
```

### Can't Access Web Interface

```bash
# Check Nginx status
sudo systemctl status nginx

# Check if app is running
sudo systemctl status timetracker

# Check firewall
sudo ufw status

# Test locally
curl http://localhost
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"

# Reset database password if needed
sudo -u postgres psql
ALTER USER timetracker WITH PASSWORD 'new_password';
\q

# Update .env file
sudo nano /opt/timetracker/.env
```

## 📈 Performance Tuning

### For 4GB RAM Server

Edit `/etc/systemd/system/timetracker.service`:
```ini
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 8 --bind 127.0.0.1:5000 app:app
```

Edit PostgreSQL config `/etc/postgresql/*/main/postgresql.conf`:
```ini
shared_buffers = 1GB
effective_cache_size = 3GB
```

Restart services:
```bash
sudo systemctl daemon-reload
sudo systemctl restart timetracker
sudo systemctl restart postgresql
```

## 🌐 Remote Access

### Access from Local Network

Find server IP:
```bash
ip addr show | grep inet
```

Access from other computers: `http://server-ip-address`

### Access from Internet

1. Configure port forwarding on router (ports 80, 443)
2. Use dynamic DNS if you don't have static IP
3. **IMPORTANT:** Enable HTTPS before exposing to internet

## 📱 Mobile Access

The interface is fully responsive and works on:
- Smartphones (iOS, Android)
- Tablets (iPad, Android tablets)
- Desktop browsers (Chrome, Firefox, Safari, Edge)

## 🔄 Migrating from Excel

To import existing Excel data:

```python
# migrate_excel.py
import pandas as pd
import psycopg2

df = pd.read_excel('savant_time_tracker.xlsx', sheet_name='Master Log', header=1)
conn = psycopg2.connect(
    host='localhost',
    database='timetracker',
    user='timetracker',
    password='your_password'
)
cur = conn.cursor()

for _, row in df.iterrows():
    cur.execute('''
        INSERT INTO time_entries 
        (user_id, entry_date, job_number, job_task_code, description, 
         hours, category, customer_name, job_description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (1, row['Date'], row['Job Number'], row['Job Task No'],
          row['Description'], row['Hours'], row['Category'],
          row['Customer Name'], row['Job Description']))

conn.commit()
```

Run: `python3 migrate_excel.py`

## 🛠️ Development

### Local Development Setup

```bash
# Clone repository
git clone <repo> timetracker
cd timetracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (using defaults)
sudo -u postgres psql
CREATE DATABASE timetracker;
CREATE USER timetracker WITH PASSWORD 'timetracker';
GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;
\q

# Load schema
psql -U timetracker -d timetracker -f database/schema.sql

# Create .env file
cat > .env << ENV
SECRET_KEY=dev-secret-key
FLASK_ENV=development
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=timetracker
DB_PORT=5432
ENV

# Run development server
python app.py
```

Access at: `http://localhost:5000`

## 📝 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration (with optional hire_date and pto_time)
- `GET /logout` - User logout

### Dashboard
- `GET /api/dashboard/metrics?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get dashboard metrics

### Time Entries
- `GET /api/time-entries?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get time entries
- `POST /api/time-entries` - Create time entry
- `PUT /api/time-entries/{id}` - Update time entry
- `DELETE /api/time-entries/{id}` - Delete time entry

### Projects
- `GET /api/projects?status=Active|Closed` - Get projects
- `POST /api/projects` - Create project
- `PUT /api/projects/{id}` - Update project

### Configuration
- `GET /api/config/job-task-codes` - Get job task codes
- `GET /api/config/admin-codes` - Get admin codes
- `GET /api/config/holidays` - Get holidays

### Export
- `GET /api/export/csv?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Export CSV

### Admin - User Management
- `GET /api/admin/get-users` - Get all users with hire dates and PTO time
- `POST /api/admin/update-user-employment` - Update user hire date and PTO time
- `POST /api/admin/change-user-password` - Change user password
- `POST /api/admin/toggle-user-active` - Activate/deactivate user
- `DELETE /api/admin/delete-user` - Delete user account

## 🤝 Support

For issues or questions:

1. Check the `INSTALLATION_GUIDE.md` for detailed instructions
2. Review logs: `sudo journalctl -u timetracker -f`
3. Check database status: `sudo systemctl status postgresql`

## 📄 License

This project is provided as-is for time tracking purposes.

## 🎯 Roadmap

Future enhancements:
- [ ] PTO tracking and usage history
- [ ] Automatic PTO accrual based on hire date
- [ ] Work anniversary and birthday notifications
- [ ] Email notifications for project budget thresholds
- [ ] Advanced reporting with graphs
- [ ] Team management and permissions
- [ ] Calendar view for time entries
- [ ] Mobile apps (iOS/Android)
- [ ] Integration with project management tools

## ✅ Checklist After Installation

- [ ] Access application in browser
- [ ] Create first user account
- [ ] Add initial projects
- [ ] Log test time entries
- [ ] View dashboard metrics
- [ ] Test backup script
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set strong passwords
- [ ] Document your configuration
- [ ] Train users on system

## 📞 Quick Commands Reference

```bash
# Application
sudo systemctl start|stop|restart|status timetracker

# Logs
sudo journalctl -u timetracker -f

# Database
sudo -u timetracker psql -U timetracker timetracker

# Backup
sudo -u timetracker /opt/timetracker/backup.sh

# Nginx
sudo systemctl restart nginx
sudo nginx -t

# Firewall
sudo ufw status
sudo ufw allow 80/tcp
```

---

**Ready to get started?** Run `sudo ./install.sh` and you'll be tracking time in minutes!
