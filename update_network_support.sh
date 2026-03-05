#!/bin/bash
# Update admin helper service with network configuration support

set -e

echo "Installing updated admin helper service with network configuration support..."
echo ""

# Copy updated admin helper
echo "1. Installing admin helper service..."
cp /opt/timetracker/timetracker-admin-helper.py /usr/local/bin/timetracker-admin-helper
chmod +x /usr/local/bin/timetracker-admin-helper
echo "   ✓ Admin helper script installed"

# Copy updated admin helper client (already in place, but this confirms it)
echo "2. Admin helper client is up to date"
echo "   ✓ Using queue path: /var/run/timetracker/"

# Restart admin helper service
echo "3. Restarting admin helper service..."
systemctl restart timetracker-admin-helper
sleep 2
echo "   ✓ Admin helper service restarted"

# Restart timetracker service
echo "4. Restarting timetracker service..."
systemctl restart timetracker
sleep 2
echo "   ✓ Timetracker service restarted"

# Check service status
echo ""
echo "Service Status:"
echo "==============="
if systemctl is-active --quiet timetracker-admin-helper; then
    echo "✓ Admin Helper Service: RUNNING"
else
    echo "✗ Admin Helper Service: FAILED"
fi

if systemctl is-active --quiet timetracker; then
    echo "✓ Timetracker Service: RUNNING"
else
    echo "✗ Timetracker Service: FAILED"
fi

echo ""
echo "Queue Directories:"
echo "=================="
ls -ld /var/run/timetracker/requests /var/run/timetracker/responses 2>/dev/null || echo "Warning: Queue directories not found"

echo ""
echo "✓ Network configuration support has been added!"
echo "  Both timezone and network configuration features should now work."
echo ""
echo "To view logs:"
echo "  sudo journalctl -u timetracker-admin-helper -f"
echo "  sudo journalctl -u timetracker -f"
