#!/bin/bash
# Complete Theme Deployment Script
# Run with: sudo bash deploy_theme.sh

set -e  # Exit on error

echo "=========================================="
echo "Dark/Light Theme Deployment Script"
echo "=========================================="
echo ""

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash deploy_theme.sh"
    exit 1
fi

echo "Step 1: Copying base.html template to production..."
cp /opt/timetracker/templates_git/base.html /opt/timetracker/templates/base.html
chown timetracker:timetracker /opt/timetracker/templates/base.html
chmod 640 /opt/timetracker/templates/base.html
echo "✓ Template copied successfully"
echo ""

echo "Step 2: Applying database migration..."
# Apply migration as timetracker user
sudo -u timetracker psql -U timetracker -d timetracker -f /opt/timetracker/add_theme_preference.sql 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Database migration applied successfully"
else
    echo "⚠ Warning: Database migration may have already been applied"
fi
echo ""

echo "Step 3: Verifying database schema..."
sudo -u timetracker psql -U timetracker -d timetracker -c "\d users" | grep -q "theme"
if [ $? -eq 0 ]; then
    echo "✓ Theme column exists in users table"
else
    echo "✗ Theme column NOT found in users table"
    exit 1
fi
echo ""

echo "Step 4: Restarting timetracker service..."
systemctl restart timetracker
sleep 3  # Give it time to start

if systemctl is-active --quiet timetracker; then
    echo "✓ Service restarted successfully"
else
    echo "✗ Service failed to start!"
    echo "Check logs with: journalctl -u timetracker -n 50"
    exit 1
fi
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open your browser and log into the application"
echo "2. Click your username in the top right corner"
echo "3. You should see 'Dark Theme' as the first menu option"
echo "4. Click it to toggle between light and dark themes"
echo ""
echo "If you don't see the theme toggle:"
echo "- Clear your browser cache (Ctrl+F5 or Cmd+Shift+R)"
echo "- Check browser console for JavaScript errors"
echo "- Review logs: journalctl -u timetracker -n 50"
echo ""
