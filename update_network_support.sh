#!/bin/bash
# Update admin helper service with network configuration support

set -e

echo "Installing updated admin helper service..."

# Copy updated admin helper
cp /opt/timetracker/timetracker-admin-helper.py /usr/local/bin/timetracker-admin-helper
chmod +x /usr/local/bin/timetracker-admin-helper
echo "✓ Updated admin helper script installed"

# Restart admin helper service
systemctl restart timetracker-admin-helper
echo "✓ Admin helper service restarted"

# Restart timetracker service
systemctl restart timetracker
echo "✓ Timetracker service restarted"

# Check service status
echo ""
echo "Service status:"
systemctl status timetracker-admin-helper --no-pager -l | head -10
echo ""
systemctl status timetracker --no-pager -l | head -10

echo ""
echo "✓ Network configuration support has been added!"
echo "  The server configuration page can now modify network settings."
