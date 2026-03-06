#!/bin/bash
# Quick template redeployment script
# Run with: sudo bash redeploy_template.sh

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run with sudo"
    exit 1
fi

echo "Copying updated template..."
cp /opt/timetracker/templates_git/base.html /opt/timetracker/templates/base.html
chown timetracker:timetracker /opt/timetracker/templates/base.html
chmod 640 /opt/timetracker/templates/base.html

echo "Restarting service..."
systemctl restart timetracker

echo "Done! Clear your browser cache (Ctrl+Shift+F5) and reload the page."
echo "Then open the browser console (F12) and click the theme toggle."
echo "You should now see debug messages in the console."
