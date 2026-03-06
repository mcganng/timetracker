# Quick Start Guide

## Installation in 5 Minutes

### 1. Transfer Files to Server

```bash
# On your local computer
scp -r web_app/ username@your-server-ip:~/

# SSH into server
ssh username@your-server-ip
```

### 2. Run Installation

```bash
cd ~/web_app
sudo ./install.sh
```

The script will prompt for:
- Database password
- Domain/IP address

### 3. Access Application

Open browser to: `http://your-server-ip`

### 4. Create Account

Click "Create Account" and register your first user.

**Registration fields:**
- **Required:** Full Name, Username, Email, Password
- **Optional:** Date of Hire, Total PTO Time (in hours)

### 5. Start Using!

- Add projects in Projects section
- Log time in Time Entry section
- View metrics in Dashboard
- (Admin) Manage user employment info in User Management

---

## Default Configuration

- **Database:** PostgreSQL on localhost
- **Web Server:** Nginx on port 80
- **Application:** Flask with Gunicorn
- **Backups:** Daily at 2 AM (script), plus on-demand via Admin Panel
- **Location:** /opt/timetracker

## Admin Panel Features

Log in as an **admin** and go to **Admin** in the navigation bar to access:

| Feature | URL | Description |
|---|---|---|
| User Management | /admin/user-management | Manage accounts, passwords, hire dates, and PTO time |
| Manage User Data | /admin/manage-user-data | Edit any user's time entries |
| Server Config | /admin/server-config | Timezone, NTP, network |
| Code Editor | /admin/code-editor | Edit app files in-browser |
| System Reports | /admin/reports | Project hours & user utilization |
| System Backup | /admin/system-backup | Create/download full backups |

### User Management Features
- View all user accounts with hire dates and PTO balances
- Edit employment information (hire date, PTO time) for any user
- Change passwords for any user
- Activate/deactivate user accounts
- Delete user accounts

## Important Files

- Application: `/opt/timetracker/app.py`
- Config: `/opt/timetracker/.env`
- Backups: `/opt/timetracker/backups/`
- Full backups: `/opt/timetracker/backups/full/`
- Logs: `sudo journalctl -u timetracker`

## Backup Options

### Option A — Admin Panel (Recommended)
1. Log in as admin
2. Navigate to **Admin** → **System Backup**
3. Click **Create Full Backup**
4. Download the `.tar.gz` file to a safe location

### Option B — Command Line
```bash
sudo -u timetracker /opt/timetracker/backup.sh
```

## Essential Commands

```bash
# Restart application
sudo systemctl restart timetracker

# View logs
sudo journalctl -u timetracker -f

# Create database-only backup
sudo -u timetracker /opt/timetracker/backup.sh

# Check status
sudo systemctl status timetracker
sudo systemctl status nginx
```

## Next Steps

1. Enable HTTPS:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. Configure firewall:
   ```bash
   sudo ufw enable
   sudo ufw allow 22,80,443/tcp
   ```

3. Create your first full backup:
   - Go to **Admin** → **System Backup** in the web interface

## Troubleshooting

**Can't access web page:**
```bash
sudo systemctl status nginx
sudo systemctl status timetracker
curl http://localhost
```

**Database errors:**
```bash
sudo systemctl status postgresql
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"
```

**View detailed logs:**
```bash
sudo journalctl -u timetracker -n 100 --no-pager
```

---

That's it! You're ready to track time. See README.md for full documentation.
