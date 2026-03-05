#!/bin/bash
#
# Install Time Tracker Admin Helper Service
#
# This script installs the privileged admin helper service that allows
# the Flask app to configure timezone and NTP settings without needing sudo.
#

set -e

echo "========================================================================"
echo "Time Tracker - Admin Helper Service Installation"
echo "========================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

echo "[1/7] Copying admin helper script to /usr/local/bin..."
cp /opt/timetracker/timetracker-admin-helper.py /usr/local/bin/timetracker-admin-helper
chmod +x /usr/local/bin/timetracker-admin-helper
echo "  ✓ Script installed"

echo ""
echo "[2/7] Installing systemd service..."
cp /opt/timetracker/timetracker-admin-helper.service /etc/systemd/system/
chmod 644 /etc/systemd/system/timetracker-admin-helper.service
echo "  ✓ Service file installed"

echo ""
echo "[3/7] Queue directories will be created by the service..."
echo "  ✓ The admin helper service creates /var/run/timetracker/ at startup"

echo ""
echo "[4/7] Reloading systemd..."
systemctl daemon-reload
echo "  ✓ Systemd reloaded"

echo ""
echo "[5/7] Enabling admin helper service..."
systemctl enable timetracker-admin-helper.service
echo "  ✓ Service enabled"

echo ""
echo "[6/7] Starting admin helper service..."
systemctl start timetracker-admin-helper.service
sleep 2
echo "  ✓ Service started"

echo ""
echo "[7/7] Verifying service status..."
if systemctl is-active --quiet timetracker-admin-helper; then
    echo "  ✓ Admin helper service is running"
else
    echo "  ✗ ERROR: Admin helper service failed to start"
    echo ""
    echo "Check logs with: sudo journalctl -u timetracker-admin-helper -n 50 --no-pager"
    exit 1
fi

echo ""
echo "========================================================================"
echo "✓ Admin Helper Service Installation Complete!"
echo "========================================================================"
echo ""
echo "The admin helper service is now running and ready to process requests."
echo ""
echo "Next steps:"
echo ""
echo "1. Restart the main timetracker service:"
echo "   sudo systemctl restart timetracker"
echo ""
echo "2. Test in the web interface:"
echo "   - Log in as admin"
echo "   - Go to: Admin → Server Configuration"
echo "   - Try changing timezone"
echo "   - Try updating NTP servers"
echo ""
echo "Service management commands:"
echo "   sudo systemctl status timetracker-admin-helper   # Check status"
echo "   sudo systemctl restart timetracker-admin-helper  # Restart service"
echo "   sudo journalctl -u timetracker-admin-helper -f   # View logs"
echo ""
echo "The helper service logs to:"
echo "   /var/log/timetracker-admin-helper.log"
echo ""
