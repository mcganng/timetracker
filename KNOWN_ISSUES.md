# Known Issues and Fixes

This document tracks known issues discovered during fresh installations and their solutions.

## 🔥 QUICK FIX for Fresh Installs

**If you just installed from GitHub and Server Configuration isn't working:**

```bash
cd /opt/timetracker
sudo bash fix_server_config.sh
```

See [QUICK_FIX.md](QUICK_FIX.md) or Issue #3 below for details.

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

### 3. Server Configuration - Timezone/NTP Updates ⚠️ CRITICAL
**Problem:** Server Configuration page cannot update timezone or NTP servers on fresh git installs

**Error Messages You'll See:**

1. **When setting timezone:**
   ```
   Error: Command '['/usr/bin/sudo', '/usr/bin/timedatectl', 'set-timezone', 'America/Chicago']'
   returned non-zero exit status 1.
   ```

2. **When setting NTP server:**
   ```
   Error: Failed to set NTP servers: sudo: The "no new privileges" flag is set, which prevents
   sudo from running as root.
   sudo: If sudo is running in a container, you may need to adjust the container configuration
   to disable the flag.
   ```

**Root Causes:**
1. **Typo in systemd service file:** Line 18 has `NoNewPrivileges=fasle` (should be `false`)
2. **Missing sudoers configuration:** `/etc/sudoers.d/timetracker` file doesn't exist
3. The `timetracker` user needs sudo permissions to run system commands:
   - `/usr/bin/timedatectl` (for timezone changes)
   - `/usr/local/bin/update-ntp-config` (for NTP server updates)

**Quick Fix:**

Run the automated fix script (make sure you're in the correct directory):
```bash
cd /opt/timetracker
sudo bash fix_server_config.sh
```

**Note:** Use `bash` instead of just the path to ensure the script runs correctly.

This script will:
- Create `/etc/sudoers.d/timetracker` with proper permissions
- Fix the `NoNewPrivileges` typo in the systemd service file
- **Properly stop and restart** the service to apply the changes
- Verify the security settings are applied correctly

**IMPORTANT:** The service MUST be fully restarted (not just reloaded) for the `NoNewPrivileges=false` setting to take effect. The fix script handles this automatically.

**Manual Fix (if needed):**

1. Fix the systemd service file typo:
```bash
sudo sed -i 's/NoNewPrivileges=fasle/NoNewPrivileges=false/' /etc/systemd/system/timetracker.service
```

2. Create sudoers configuration:
```bash
sudo tee /etc/sudoers.d/timetracker > /dev/null << 'EOF'
# Allow timetracker user to run specific system commands without password
timetracker ALL=(ALL) NOPASSWD: /usr/bin/timedatectl
timetracker ALL=(ALL) NOPASSWD: /usr/local/bin/update-ntp-config
EOF

sudo chmod 0440 /etc/sudoers.d/timetracker
```

3. Reload and **fully restart** the service:
```bash
sudo systemctl daemon-reload
sudo systemctl stop timetracker
sudo systemctl start timetracker
```

**Note:** You MUST stop and start (not just `restart`) to ensure the NoNewPrivileges setting takes effect.

4. Verify the setting is applied:
```bash
systemctl show timetracker | grep NoNewPrivileges
# Should show: NoNewPrivileges=no (yes=blocked, no=allowed)
```

5. Verify sudo permissions:
```bash
sudo -u timetracker sudo -l
```

**Testing:**

Run the diagnostic script:
```bash
cd /opt/timetracker
sudo bash test_sudo_permissions.sh
```

Or test manually:
```bash
# Test timezone command
sudo -u timetracker sudo /usr/bin/timedatectl list-timezones | head -5

# Test NTP configuration
echo 'time.google.com' | sudo -u timetracker sudo /usr/local/bin/update-ntp-config
```

**Common Issues After Fix:**

If you still get "no new privileges" errors after running the fix script:
1. Verify the service was **fully restarted** (stop then start, not just restart)
2. Check the NoNewPrivileges setting: `systemctl show timetracker | grep NoNewPrivileges`
3. It should show `NoNewPrivileges=no` (not `yes`)
4. If it shows `yes`, the service wasn't restarted properly - run the fix script again

**Status:** Fixed by running `fix_server_config.sh` after installation (updated version ensures proper restart)

**Reference:** See [SERVER_CONFIG_SETUP.md](SERVER_CONFIG_SETUP.md) for detailed documentation

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

- [ ] **Run server config fix:** `sudo /opt/timetracker/fix_server_config.sh` (see issue #3)
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
