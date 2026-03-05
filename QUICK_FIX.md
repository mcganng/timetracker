# Quick Fix for Server Configuration Errors

## Problem
After fresh install from GitHub, timezone and NTP configuration fail with errors:
- `Error: Command '['/usr/bin/sudo', '/usr/bin/timedatectl'...]' returned non-zero exit status 1`
- `sudo: The "no new privileges" flag is set, which prevents sudo from running as root`

## Solution (2 commands)

Run these commands **exactly as shown**:

```bash
cd /opt/timetracker
sudo bash fix_server_config.sh
```

That's it! The script will:
1. Create the sudoers configuration file
2. Fix the systemd service typo
3. Restart the service properly
4. Verify everything works

## Verify It Worked

```bash
cd /opt/timetracker
sudo bash test_sudo_permissions.sh
```

All tests should pass with ✓ marks.

## Test in Web UI

1. Log in as admin
2. Go to: **Admin → Server Configuration**
3. Change timezone to `America/Chicago`
4. Update NTP servers to `time.google.com`

Both should work without errors now!

## Troubleshooting

If you still get errors:

1. Check the NoNewPrivileges setting:
   ```bash
   systemctl show timetracker | grep NoNewPrivileges
   ```
   Should show: `NoNewPrivileges=no` (not `yes`)

2. Check service status:
   ```bash
   sudo systemctl status timetracker
   ```

3. View recent logs:
   ```bash
   sudo journalctl -u timetracker -n 50 --no-pager
   ```

## Why This Happens

Fresh installs from GitHub have:
- A typo in the systemd service file (`NoNewPrivileges=fasle`)
- Missing sudoers configuration for the timetracker user

The fix script corrects both issues and properly restarts the service.
