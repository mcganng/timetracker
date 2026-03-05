#!/bin/bash
#
# Update Time Tracker from Git Repository
#
# This script updates an existing installation with the latest code from git
# Use this after pulling the latest changes from the repository
#

set -e

echo "========================================================================"
echo "Time Tracker - Update from Git Repository"
echo "========================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

INSTALL_DIR="/opt/timetracker"

# Check if timetracker is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo "ERROR: Time Tracker does not appear to be installed at $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

echo "[1/6] Updating admin helper service..."
if [ -f "$INSTALL_DIR/timetracker-admin-helper.py" ]; then
    cp "$INSTALL_DIR/timetracker-admin-helper.py" /usr/local/bin/timetracker-admin-helper
    chmod +x /usr/local/bin/timetracker-admin-helper
    echo "  ✓ Admin helper service updated"
else
    echo "  ⚠ Warning: timetracker-admin-helper.py not found"
fi

echo ""
echo "[2/6] Updating admin helper client..."
if [ -f "$INSTALL_DIR/admin_helper_client.py" ]; then
    # File should already be in place from git pull
    echo "  ✓ Admin helper client is up to date"
else
    echo "  ⚠ Warning: admin_helper_client.py not found"
fi

echo ""
echo "[3/6] Updating systemd service files..."
if [ -f "$INSTALL_DIR/timetracker-admin-helper.service" ]; then
    cp "$INSTALL_DIR/timetracker-admin-helper.service" /etc/systemd/system/
    chmod 644 /etc/systemd/system/timetracker-admin-helper.service
    systemctl daemon-reload
    echo "  ✓ Systemd service files updated"
else
    echo "  ⚠ Warning: timetracker-admin-helper.service not found"
fi

echo ""
echo "[4/6] Restarting admin helper service..."
systemctl restart timetracker-admin-helper
sleep 2
if systemctl is-active --quiet timetracker-admin-helper; then
    echo "  ✓ Admin helper service restarted successfully"
else
    echo "  ✗ ERROR: Admin helper service failed to start"
    echo ""
    echo "Check logs: sudo journalctl -u timetracker-admin-helper -n 50"
    exit 1
fi

echo ""
echo "[5/6] Restarting timetracker service..."
systemctl restart timetracker
sleep 2
if systemctl is-active --quiet timetracker; then
    echo "  ✓ Timetracker service restarted successfully"
else
    echo "  ✗ ERROR: Timetracker service failed to start"
    echo ""
    echo "Check logs: sudo journalctl -u timetracker -n 50"
    exit 1
fi

echo ""
echo "[6/6] Verifying queue directories..."
if [ -d "/var/run/timetracker/requests" ] && [ -d "/var/run/timetracker/responses" ]; then
    echo "  ✓ Queue directories exist at /var/run/timetracker/"
    ls -ld /var/run/timetracker/requests /var/run/timetracker/responses
else
    echo "  ⚠ Warning: Queue directories not found - service may need more time to start"
fi

echo ""
echo "========================================================================"
echo "✓ Update Complete!"
echo "========================================================================"
echo ""
echo "Services updated and restarted:"
echo "  • timetracker-admin-helper (for timezone and network config)"
echo "  • timetracker (main application)"
echo ""
echo "Test the server configuration features:"
echo "  1. Log in as admin"
echo "  2. Go to: Admin → Server Configuration"
echo "  3. Try changing timezone"
echo "  4. Try modifying network settings"
echo "  5. Try updating NTP servers"
echo ""
echo "Monitor logs if issues occur:"
echo "  sudo journalctl -u timetracker-admin-helper -f"
echo "  sudo journalctl -u timetracker -f"
echo ""
