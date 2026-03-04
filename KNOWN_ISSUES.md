# Known Issues and Fixes

This document tracks known issues discovered during fresh installations and their solutions.

## Fixed Issues

### 1. Missing PyYAML Dependency ✅ FIXED
**Problem:** Application failed to start with `ModuleNotFoundError: No module named 'yaml'`

**Solution:** Added `PyYAML==6.0.1` to [requirements.txt](requirements.txt)

**Status:** Fixed in commit 6fb365a

### 2. Missing Database Columns ✅ FIXED
**Problem:** User Management and Manage User Data pages showed error:
```
Error loading users: column "hire_date" does not exist
```

**Solution:** Added missing columns to users table in [database_git/schema.sql](database_git/schema.sql):
- `hire_date date`
- `pto_time numeric(10,2) DEFAULT 0`

**Status:** Fixed in this commit

## Remaining Issues (Require Additional Configuration)

### 3. Server Configuration - Timezone/NTP Updates
**Problem:** Server Configuration page cannot update timezone or NTP servers

**Root Cause:** The `timetracker` user needs sudo permissions to run system commands:
- `/usr/bin/timedatectl` (for timezone changes)
- `/usr/local/bin/update-ntp-config` (for NTP server updates)

**Solution Required:**

1. Create the NTP helper script:
```bash
sudo tee /usr/local/bin/update-ntp-config > /dev/null << 'EOF'
#!/bin/bash
# NTP Configuration Helper for Time Tracker
# This script updates systemd-timesyncd NTP servers

read -r NTP_SERVERS

if [ -z "$NTP_SERVERS" ]; then
    echo "Error: No NTP servers provided"
    exit 1
fi

# Backup current config
cp /etc/systemd/timesyncd.conf /etc/systemd/timesyncd.conf.backup.$(date +%Y%m%d_%H%M%S)

# Update NTP configuration
cat > /etc/systemd/timesyncd.conf << CONF
[Time]
NTP=$NTP_SERVERS
FallbackNTP=time.cloudflare.com time.google.com
CONF

# Restart timesyncd
systemctl restart systemd-timesyncd

echo "NTP servers updated to: $NTP_SERVERS"
exit 0
EOF

sudo chmod +x /usr/local/bin/update-ntp-config
```

2. Configure sudo permissions:
```bash
sudo tee /etc/sudoers.d/timetracker > /dev/null << 'EOF'
# Allow timetracker user to run specific system commands without password
timetracker ALL=(ALL) NOPASSWD: /usr/bin/timedatectl
timetracker ALL=(ALL) NOPASSWD: /usr/local/bin/update-ntp-config
EOF

sudo chmod 0440 /etc/sudoers.d/timetracker
```

3. Verify permissions:
```bash
sudo -u timetracker sudo -l
```

**Status:** Requires manual server configuration

### 4. System Backup Page - Internal Server Error
**Problem:** System Backup page shows "Internal Server Error"

**Root Cause:** Missing template file `system_backup.html`

**Impact:** The `/admin/system-backup` route expects this template but it's not in the repository

**Solution Required:**
- Create the missing `system_backup.html` template
- OR remove the route if this feature is not needed

**Status:** Template needs to be created or route needs to be removed

## Post-Installation Checklist

After running the install script on a fresh server, complete these additional steps:

- [ ] Configure sudo permissions for timetracker user (see issue #3)
- [ ] Create NTP helper script (see issue #3)
- [ ] Verify timezone changes work: Test in Server Configuration page
- [ ] Verify NTP updates work: Test in Server Configuration page
- [ ] Decide on System Backup feature: Create template or remove route
- [ ] Test all admin features: User Management, Manage User Data, Server Config
- [ ] Set up SSL certificate (optional but recommended)

## Testing Fresh Installation

To verify a clean installation:

```bash
# 1. Clone and install
git clone https://github.com/mcganng/timetracker.git
cd timetracker
sudo bash install.sh

# 2. Check service status
sudo systemctl status timetracker
sudo journalctl -u timetracker -n 50

# 3. Test login
# Navigate to http://YOUR_IP
# Login: Admin / admin123

# 4. Test each admin page:
# - Dashboard (should work)
# - Time Entry (should work)
# - Projects (should work)
# - Configuration (should work)
# - User Management (should work after schema fix)
# - Manage User Data (should work after schema fix)
# - Server Configuration (works for viewing, requires sudo for updates)
# - System Backup (requires template creation)
# - Reports (should work)
```

## Database Migration for Existing Installations

If you have an existing installation without the new columns, run this SQL:

```sql
-- Connect as timetracker user
sudo -u timetracker psql -U timetracker -d timetracker

-- Add missing columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date date;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pto_time numeric(10,2) DEFAULT 0;

-- Verify
\d users

-- Exit
\q
```
