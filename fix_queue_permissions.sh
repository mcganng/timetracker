#!/bin/bash
# Fix queue directory permissions
# This manually fixes the permissions that should have been set by the admin helper service

echo "Fixing /var/run/timetracker/ directory permissions..."

# Set ownership on parent directory
sudo chown timetracker:timetracker /var/run/timetracker/
sudo chmod 770 /var/run/timetracker/

# Set ownership on subdirectories
sudo chown timetracker:timetracker /var/run/timetracker/requests
sudo chown timetracker:timetracker /var/run/timetracker/responses
sudo chmod 770 /var/run/timetracker/requests
sudo chmod 770 /var/run/timetracker/responses

echo "Permissions fixed!"
echo ""
echo "Verifying:"
ls -la /var/run/timetracker/

echo ""
echo "Now restart the timetracker service:"
echo "  sudo systemctl restart timetracker"
