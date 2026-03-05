#!/bin/bash
# Script to copy updated templates from templates_git to templates directory
# Run with: sudo bash copy_templates.sh

echo "Copying templates from templates_git to templates..."
cp -v /opt/timetracker/templates_git/*.html /opt/timetracker/templates/
chown timetracker:timetracker /opt/timetracker/templates/*.html
chmod 640 /opt/timetracker/templates/*.html
echo "Done! Templates copied and permissions set."
echo "Now restart the service with: sudo systemctl restart timetracker"
