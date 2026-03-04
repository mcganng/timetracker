# Installation Checklist

Use this checklist to ensure successful installation.

## Pre-Installation

- [ ] Ubuntu 20.04 LTS or later installed
- [ ] Minimum 2GB RAM available
- [ ] Minimum 10GB disk space available
- [ ] SSH access to server
- [ ] Root/sudo access
- [ ] Internet connection available

## Installation Steps

- [ ] Files transferred to server
- [ ] Navigated to web_app directory
- [ ] Made install.sh executable (`chmod +x install.sh`)
- [ ] Ran installation script (`sudo ./install.sh`)
- [ ] Provided database password
- [ ] Provided domain/IP address
- [ ] Installation completed without errors

## Post-Installation Verification

- [ ] Application service running (`sudo systemctl status timetracker`)
- [ ] Nginx running (`sudo systemctl status nginx`)
- [ ] PostgreSQL running (`sudo systemctl status postgresql`)
- [ ] Can access web interface in browser
- [ ] Created first user account (register at /register)
  - [ ] Required fields filled (Full Name, Username, Email, Password)
  - [ ] Optional employment fields visible (Date of Hire, Total PTO Time)
- [ ] Successfully logged in
- [ ] First user promoted to admin (via Admin → User Management)

## Security Configuration

- [ ] Changed database password from default
- [ ] Enabled firewall (`sudo ufw enable`)
- [ ] Allowed necessary ports (22, 80, 443)
- [ ] Configured HTTPS/SSL certificate (optional but recommended)
- [ ] All user accounts use strong passwords

## Backup Configuration

- [ ] Script-based backup cron job configured (check with `sudo crontab -u timetracker -l`)
- [ ] Tested manual script backup (`sudo -u timetracker /opt/timetracker/backup.sh`)
- [ ] Verified database backup file created in `/opt/timetracker/backups/`
- [ ] Created first full backup via Admin → System Backup in web interface
- [ ] Downloaded full backup `.tar.gz` to an off-server location
- [ ] Verified backup archive contains `database.sql`, `timetracker_files.tar.gz`, and `restore.sh`
- [ ] Backup directory has sufficient disk space

## Admin Panel Features Verification

- [ ] Admin → User Management accessible and functional
  - [ ] User table displays Hire Date and PTO Time columns
  - [ ] Can click "Edit Employment" button on any user
  - [ ] Can update hire date for a user
  - [ ] Can update PTO time for a user
  - [ ] Can clear employment fields (set to null)
  - [ ] Changes save and display correctly in table
- [ ] Admin → Manage User Data: can view and edit other users' time entries
- [ ] Admin → Server Config: timezone and NTP settings load correctly
- [ ] Admin → Code Editor: can browse and edit templates
- [ ] Admin → System Reports: project hours and user utilization display correctly
- [ ] Admin → System Backup: can create, list, download, and delete backup bundles

## Functionality Testing

- [ ] Dashboard loads and shows metrics (project hours, utilization %)
- [ ] Can create time entries
- [ ] Can add new projects with budget hours
- [ ] Can view configuration (job task codes, holidays)
- [ ] Can export CSV
- [ ] Date range filtering works
- [ ] Charts display correctly
- [ ] System Reports shows correct YTD project hours and user utilization
- [ ] Bulk time import (CSV) works

## Employment Information Features Testing

- [ ] Registration form displays optional employment fields
  - [ ] Date of Hire field visible with date picker
  - [ ] Total PTO Time field visible with hours input
  - [ ] Can register without filling optional fields
  - [ ] Can register with employment fields filled
- [ ] User Management displays employment information
  - [ ] Hire dates display in formatted style (e.g., "Jan 15, 2024")
  - [ ] PTO time displays with hours unit (e.g., "80.0 hrs")
  - [ ] "Not set" appears for users without employment info
- [ ] Admin can edit employment information
  - [ ] Modal opens with current values pre-filled
  - [ ] Can update one field independently
  - [ ] Can update both fields together
  - [ ] Can clear fields by leaving blank
  - [ ] Success message displays after save
  - [ ] Table refreshes automatically

## Optional Enhancements

- [ ] SSL certificate installed
- [ ] Custom domain configured
- [ ] Remote access configured (if needed)
- [ ] Additional users created and tested
- [ ] Team dashboard reviewed with admin account

## Documentation

- [ ] Saved database credentials securely
- [ ] Documented server IP/domain
- [ ] Noted location of backup files (both `/opt/timetracker/backups/` and off-server copy)
- [ ] Created runbook for common tasks
- [ ] Trained users on time entry and dashboard
- [ ] Trained admin on System Reports and System Backup pages

## Monitoring Setup

- [ ] Know how to check application status
- [ ] Know how to view logs
- [ ] Know how to restart services
- [ ] Understand backup schedule (daily 2 AM script + on-demand via Admin UI)
- [ ] Have plan for updates

## Final Validation

- [ ] Application accessible from all intended devices
- [ ] All features working as expected
- [ ] System Backup created and stored off-server
- [ ] Full restore tested (or restore.sh reviewed for accuracy)
- [ ] Performance acceptable
- [ ] No errors in logs (`sudo journalctl -u timetracker -n 50`)

---

## If Something Fails

1. Check logs: `sudo journalctl -u timetracker -n 50`
2. Verify services: `sudo systemctl status timetracker nginx postgresql`
3. Test database: `sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"`
4. Check network: `curl http://localhost`
5. Review INSTALLATION_GUIDE.md for full troubleshooting section

---

**Installation Date:** _______________
**Installed By:** _______________
**Server IP/Domain:** _______________
**Database Password Location:** _______________
**First Backup Location:** _______________
**Notes:** _______________________________________________
