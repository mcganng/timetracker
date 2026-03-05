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
echo "   ✓ Systemd daemon reloaded"

# Stop the service first to ensure clean restart
systemctl stop timetracker
sleep 1

# Start the service
systemctl start timetracker

# Wait for service to fully start
sleep 3

# Check if service is running
if systemctl is-active --quiet timetracker; then
    echo "   ✓ Time Tracker service restarted successfully"

    # Verify the NoNewPrivileges setting is active
    echo ""
    echo "[5/5] Verifying service security settings..."
    if systemctl show timetracker | grep -q "NoNewPrivileges=no"; then
        echo "   ✓ NoNewPrivileges is correctly set to 'no' (allows sudo)"
    else
        echo "   ⚠ WARNING: NoNewPrivileges may not be applied correctly"
        echo "   Current value:"
        systemctl show timetracker | grep "NoNewPrivileges" | sed 's/^/     /'
    fi
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
echo "IMPORTANT: The application has been restarted with new settings."
echo ""
echo "Next Steps:"
echo ""
echo "1. Run the test script to verify everything works:"
echo "   chmod +x /opt/timetracker/test_sudo_permissions.sh"
echo "   sudo /opt/timetracker/test_sudo_permissions.sh"
echo ""
echo "2. If tests pass, access the web interface:"
echo "   - Log in as admin"
echo "   - Go to: Admin → Server Configuration"
echo "   - Try changing timezone (e.g., to America/Chicago)"
echo "   - Try updating NTP servers (e.g., time.google.com)"
echo ""
echo "3. If you still get errors, check the service status:"
echo "   sudo systemctl status timetracker"
echo "   sudo journalctl -u timetracker -n 50 --no-pager"
echo ""
echo "4. Verify NoNewPrivileges is set correctly:"
echo "   systemctl show timetracker | grep NoNewPrivileges"
echo "   (Should show: NoNewPrivileges=no)"
echo ""
