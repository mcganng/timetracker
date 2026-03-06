# Server Configuration Setup Guide

## Overview

The Time Tracker application includes a **Server Configuration** page that allows administrators to:
- View and change the server timezone
- Configure custom NTP (Network Time Protocol) servers
- View network configuration

However, these features require the `timetracker` system user to have **sudo permissions** to execute system commands.

## Why Sudo is Required

The application needs to run these system commands:
- `/usr/bin/timedatectl set-timezone <timezone>` - Change system timezone
- `/usr/local/bin/update-ntp-config` - Update NTP server configuration

By default, the `timetracker` user cannot execute these commands because:
1. It's a system user (not a login user)
2. It has no sudo privileges
3. These commands require root access

## Setup Steps

Follow these steps **after** installing the Time Tracker application.

### Step 1: Create the NTP Configuration Helper Script

This script safely updates NTP servers without giving the timetracker user full root access.

```bash
sudo tee /usr/local/bin/update-ntp-config > /dev/null << 'EOF'
#!/bin/bash
#
# NTP Configuration Helper for Time Tracker
# This script updates systemd-timesyncd NTP servers
#
# Usage: echo "server1 server2" | /usr/local/bin/update-ntp-config
#

# Read NTP servers from stdin
read -r NTP_SERVERS

# Validate input
if [ -z "$NTP_SERVERS" ]; then
    echo "Error: No NTP servers provided" >&2
    exit 1
fi

# Backup current configuration
BACKUP_FILE="/etc/systemd/timesyncd.conf.backup.$(date +%Y%m%d_%H%M%S)"
if [ -f /etc/systemd/timesyncd.conf ]; then
    cp /etc/systemd/timesyncd.conf "$BACKUP_FILE"
    echo "Backed up current config to: $BACKUP_FILE" >&2
fi

# Create new configuration
cat > /etc/systemd/timesyncd.conf << CONF
# Time Tracker - NTP Configuration
# Last updated: $(date)

[Time]
NTP=$NTP_SERVERS
FallbackNTP=time.cloudflare.com time.google.com pool.ntp.org
CONF

# Restart timesyncd service
if systemctl restart systemd-timesyncd; then
    echo "NTP servers updated successfully: $NTP_SERVERS"
    systemctl status systemd-timesyncd --no-pager --lines=0
    exit 0
else
    echo "Error: Failed to restart systemd-timesyncd" >&2
    # Restore backup if restart failed
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" /etc/systemd/timesyncd.conf
        echo "Restored previous configuration" >&2
    fi
    exit 1
fi
EOF

# Make it executable
sudo chmod +x /usr/local/bin/update-ntp-config

# Verify it was created
ls -la /usr/local/bin/update-ntp-config
```

### Step 2: Configure Sudo Permissions

Create a sudoers file specifically for the timetracker user:

```bash
sudo tee /etc/sudoers.d/timetracker > /dev/null << 'EOF'
# Sudo permissions for Time Tracker application
# This allows the timetracker user to run specific system commands

# Allow timezone changes
timetracker ALL=(ALL) NOPASSWD: /usr/bin/timedatectl

# Allow NTP configuration updates
timetracker ALL=(ALL) NOPASSWD: /usr/local/bin/update-ntp-config
EOF

# Set correct permissions (sudoers files must be 0440)
sudo chmod 0440 /etc/sudoers.d/timetracker

# Verify the file was created correctly
sudo ls -la /etc/sudoers.d/timetracker
```

### Step 3: Verify Sudo Configuration

Test that the timetracker user has the correct permissions:

```bash
# Check sudo privileges
sudo -u timetracker sudo -l

# Expected output should include:
# User timetracker may run the following commands on this host:
#     (ALL) NOPASSWD: /usr/bin/timedatectl
#     (ALL) NOPASSWD: /usr/local/bin/update-ntp-config
```

### Step 4: Test the Configuration

Test timezone changes:

```bash
# Test as timetracker user
sudo -u timetracker sudo /usr/bin/timedatectl list-timezones | head -5

# Should list timezones without prompting for a password
```

Test NTP configuration:

```bash
# Test the NTP helper script
echo "time.google.com time.cloudflare.com" | sudo -u timetracker sudo /usr/local/bin/update-ntp-config

# Check NTP status
timedatectl timesync-status
```

### Step 5: Restart the Time Tracker Service

```bash
sudo systemctl restart timetracker
```

## Verification

1. Log in to the Time Tracker web interface as an admin user
2. Navigate to **Admin** → **Server Configuration**
3. Try changing the timezone
   - Select a different timezone from the dropdown
   - Click "Set Timezone"
   - Should see success message
4. Try updating NTP servers
   - Enter one or two NTP server addresses (e.g., `time.google.com`)
   - Click "Update NTP Servers"
   - Should see success message

## Troubleshooting

### Permission Denied Errors

If you see "Permission denied" errors:

1. **Check sudoers file syntax:**
   ```bash
   sudo visudo -c -f /etc/sudoers.d/timetracker
   ```
   Should output: `parsed OK`

2. **Verify file permissions:**
   ```bash
   ls -la /etc/sudoers.d/timetracker
   # Should be: -r--r----- 1 root root ... /etc/sudoers.d/timetracker
   ```

3. **Check script permissions:**
   ```bash
   ls -la /usr/local/bin/update-ntp-config
   # Should be: -rwxr-xr-x 1 root root ... /usr/local/bin/update-ntp-config
   ```

### Timezone Changes Don't Work

Check the application logs:

```bash
sudo journalctl -u timetracker -f
```

Then try changing timezone in the UI. Look for errors in the logs.

### NTP Configuration Fails

1. **Check if systemd-timesyncd is installed:**
   ```bash
   systemctl status systemd-timesyncd
   ```

2. **Check NTP helper script logs:**
   ```bash
   # Run manually to see errors
   echo "invalid.server" | sudo /usr/local/bin/update-ntp-config
   ```

3. **Verify NTP config file:**
   ```bash
   cat /etc/systemd/timesyncd.conf
   ```

## Security Considerations

This configuration is designed with security in mind:

1. **Limited Scope:** The timetracker user can ONLY run these two specific commands
2. **No Shell Access:** The user cannot escalate to a root shell
3. **NOPASSWD:** Required because the timetracker user is a system user with no password
4. **Restricted Script:** The NTP helper script only modifies one file and has input validation
5. **Audit Trail:** All sudo commands are logged in `/var/log/auth.log`

## Viewing Sudo Logs

To see when the timetracker user uses sudo:

```bash
sudo grep "timetracker.*sudo" /var/log/auth.log | tail -20
```

## Removing Sudo Access (Optional)

If you want to disable these features:

```bash
# Remove sudo permissions
sudo rm /etc/sudoers.d/timetracker

# Remove NTP helper script
sudo rm /usr/local/bin/update-ntp-config

# Restart service
sudo systemctl restart timetracker
```

The Server Configuration page will still load, but timezone/NTP changes will fail with permission errors.

## Alternative: Manual Configuration

If you prefer not to grant sudo access, you can configure timezone and NTP manually:

**Change Timezone:**
```bash
sudo timedatectl set-timezone America/New_York
```

**Configure NTP:**
```bash
sudo nano /etc/systemd/timesyncd.conf
# Edit the NTP= line
sudo systemctl restart systemd-timesyncd
```

Then use the Time Tracker's Server Configuration page for **viewing only** (not editing).
