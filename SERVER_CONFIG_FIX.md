# Server Configuration Fix for Fresh Installs

## Problem

On fresh installations from git, the **Server Configuration** page (Admin → Server Configuration) fails when trying to:
- Set timezone
- Update NTP servers

## Root Cause

Two issues prevent server configuration from working:

### 1. Missing Sudoers File

The timetracker system user needs sudo permissions to run specific system commands, but the sudoers file is missing.

**Required file:** `/etc/sudoers.d/timetracker`

**Error in logs:**
```
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
```

### 2. Typo in Systemd Service File

The service file contains a typo that prevents proper privilege handling:

**File:** `/etc/systemd/system/timetracker.service`

**Line 18 has:**
```ini
NoNewPrivileges=fasle
```

**Should be:**
```ini
NoNewPrivileges=false
```

## Solution

Run the automated fix script:

```bash
sudo bash /opt/timetracker/fix_server_config.sh
```

This script will:
1. ✓ Create the missing sudoers file with correct permissions
2. ✓ Fix the typo in the systemd service file
3. ✓ Reload systemd daemon
4. ✓ Restart the timetracker service
5. ✓ Verify the service is running

## Manual Fix (Alternative)

If you prefer to fix manually:

### Step 1: Create Sudoers File

```bash
sudo tee /etc/sudoers.d/timetracker > /dev/null << 'EOF'
# Sudo permissions for Time Tracker application
# This allows the timetracker user to run specific system commands

# Allow timezone changes
timetracker ALL=(ALL) NOPASSWD: /usr/bin/timedatectl

# Allow NTP configuration updates
timetracker ALL=(ALL) NOPASSWD: /usr/local/bin/update-ntp-config
EOF

sudo chmod 0440 /etc/sudoers.d/timetracker
```

### Step 2: Fix Systemd Service File

```bash
sudo sed -i 's/NoNewPrivileges=fasle/NoNewPrivileges=false/' /etc/systemd/system/timetracker.service
```

### Step 3: Reload and Restart

```bash
sudo systemctl daemon-reload
sudo systemctl restart timetracker
```

## Verification

After running the fix:

### 1. Check Sudo Permissions

```bash
sudo -u timetracker sudo -l
```

Expected output:
```
User timetracker may run the following commands on this host:
    (ALL) NOPASSWD: /usr/bin/timedatectl
    (ALL) NOPASSWD: /usr/local/bin/update-ntp-config
```

### 2. Test Timezone Command

```bash
sudo -u timetracker sudo /usr/bin/timedatectl list-timezones | head -5
```

Should list timezones without errors.

### 3. Test NTP Configuration

```bash
echo 'time.google.com' | sudo -u timetracker sudo /usr/local/bin/update-ntp-config
```

Should show:
```
Backed up current config to: /etc/systemd/timesyncd.conf.backup.YYYYMMDD_HHMMSS
NTP servers updated successfully: time.google.com
```

### 4. Test in Web Interface

1. Log in as admin user
2. Navigate to **Admin** → **Server Configuration**
3. Try changing the timezone - should succeed
4. Try updating NTP servers - should succeed

## Why This Happened

These setup steps are documented in [SERVER_CONFIG_SETUP.md](SERVER_CONFIG_SETUP.md) but are **manual post-installation steps** that must be performed after cloning the repository.

The files are not included in git because:
- `/etc/sudoers.d/timetracker` - System configuration file (security-sensitive)
- Service file typo was a bug that needs to be fixed in the repository

## Logs to Check

If issues persist:

```bash
# Check service status
sudo systemctl status timetracker

# View recent logs
sudo journalctl -u timetracker -n 100 --no-pager

# Watch logs in real-time
sudo journalctl -u timetracker -f
```

## Security Notes

The sudoers configuration is intentionally restrictive:
- ✓ timetracker user can ONLY run two specific commands
- ✓ Cannot escalate to root shell
- ✓ Cannot run arbitrary commands
- ✓ All sudo usage is logged in `/var/log/auth.log`

## Related Documentation

- [SERVER_CONFIG_SETUP.md](SERVER_CONFIG_SETUP.md) - Complete setup guide
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Full installation instructions
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) - Known issues and workarounds
