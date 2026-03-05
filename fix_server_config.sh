#!/bin/bash
#
# Fix Server Configuration Issues
# This script fixes the server configuration functionality on fresh installs
#
# Issues fixed:
# 1. Creates missing sudoers file for timetracker user
# 2. Fixes typo in systemd service file (NoNewPrivileges=fasle -> false)
# 3. Reloads systemd and restarts the service
#

set -e  # Exit on error

echo "==================================================================="
echo "Time Tracker - Server Configuration Fix Script"
echo "==================================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

echo "[1/4] Creating sudoers file for timetracker user..."
cat > /etc/sudoers.d/timetracker << 'EOF'
# Sudo permissions for Time Tracker application
# This allows the timetracker user to run specific system commands

# Allow timezone changes
timetracker ALL=(ALL) NOPASSWD: /usr/bin/timedatectl

# Allow NTP configuration updates
timetracker ALL=(ALL) NOPASSWD: /usr/local/bin/update-ntp-config
EOF

# Set correct permissions (sudoers files must be 0440)
chmod 0440 /etc/sudoers.d/timetracker

echo "   ✓ Created /etc/sudoers.d/timetracker"

# Verify sudoers syntax
echo "[2/4] Validating sudoers file syntax..."
if visudo -c -f /etc/sudoers.d/timetracker > /dev/null 2>&1; then
    echo "   ✓ Sudoers file syntax is valid"
else
    echo "   ✗ ERROR: Sudoers file has syntax errors!"
    exit 1
fi

echo "[3/4] Fixing systemd service file typo..."
# Fix the typo: NoNewPrivileges=fasle -> false
sed -i 's/NoNewPrivileges=fasle/NoNewPrivileges=false/' /etc/systemd/system/timetracker.service

# Verify the fix
if grep -q "NoNewPrivileges=false" /etc/systemd/system/timetracker.service; then
    echo "   ✓ Fixed NoNewPrivileges typo in service file"
else
    echo "   ⚠ Warning: Could not verify fix (typo may not exist or already fixed)"
fi

echo "[4/4] Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl restart timetracker

# Wait a moment for service to start
sleep 2

# Check if service is running
if systemctl is-active --quiet timetracker; then
    echo "   ✓ Time Tracker service restarted successfully"
else
    echo "   ✗ ERROR: Time Tracker service failed to start!"
    echo ""
    echo "Check logs with: sudo journalctl -u timetracker -n 50 --no-pager"
    exit 1
fi

echo ""
echo "==================================================================="
echo "✓ Server Configuration Fix Complete!"
echo "==================================================================="
echo ""
echo "Verification:"
echo ""
echo "1. Check timetracker sudo permissions:"
echo "   sudo -u timetracker sudo -l"
echo ""
echo "2. Test timezone command:"
echo "   sudo -u timetracker sudo /usr/bin/timedatectl list-timezones | head -5"
echo ""
echo "3. Test NTP configuration:"
echo "   echo 'time.google.com' | sudo -u timetracker sudo /usr/local/bin/update-ntp-config"
echo ""
echo "4. Access the web interface and try:"
echo "   - Admin → Server Configuration"
echo "   - Change timezone"
echo "   - Update NTP servers"
echo ""
