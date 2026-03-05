#!/bin/bash
#
# Update Fresh Install with Latest Code from GitHub
# Run this on fresh install servers to get the admin helper service
#

set -e

echo "========================================================================"
echo "Time Tracker - Update from GitHub"
echo "========================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if git repo exists
if [ ! -d ~/timetracker/.git ]; then
    echo "ERROR: Git repository not found at ~/timetracker"
    echo "Please clone first: git clone https://github.com/mcganng/timetracker.git"
    exit 1
fi

echo "[1/5] Pulling latest code from GitHub..."
cd ~/timetracker
git pull origin main
echo "  ✓ Code updated"

echo ""
echo "[2/5] Copying new files to /opt/timetracker..."
cp -v admin_helper_client.py /opt/timetracker/
cp -v timetracker-admin-helper.py /opt/timetracker/
cp -v timetracker-admin-helper.service /opt/timetracker/
cp -v install_admin_helper.sh /opt/timetracker/
cp -v app.py /opt/timetracker/
echo "  ✓ Files copied"

echo ""
echo "[3/5] Setting correct ownership..."
chown timetracker:timetracker /opt/timetracker/*.py
chown timetracker:timetracker /opt/timetracker/*.sh
chmod +x /opt/timetracker/*.sh
echo "  ✓ Ownership set"

echo ""
echo "[4/5] Installing admin helper service..."
cd /opt/timetracker
bash install_admin_helper.sh
echo "  ✓ Admin helper installed"

echo ""
echo "[5/5] Restarting timetracker service..."
systemctl restart timetracker
sleep 2

if systemctl is-active --quiet timetracker; then
    echo "  ✓ Timetracker service restarted"
else
    echo "  ✗ WARNING: Timetracker service may have issues"
    systemctl status timetracker --no-pager -l
fi

echo ""
echo "========================================================================"
echo "✓ Update Complete!"
echo "========================================================================"
echo ""
echo "The timetracker application has been updated with:"
echo "  - Admin helper service for server configuration"
echo "  - Fixed app.py with dual-mode support"
echo "  - All latest fixes from GitHub"
echo ""
echo "Test the server configuration:"
echo "  1. Open browser to: http://$(hostname -I | awk '{print $1}')"
echo "  2. Login as admin"
echo "  3. Go to: Admin → Server Configuration"
echo "  4. Try setting timezone and NTP servers"
echo ""
echo "Services running:"
systemctl is-active --quiet timetracker-admin-helper && echo "  ✓ Admin helper service: Running" || echo "  ✗ Admin helper service: Not running"
systemctl is-active --quiet timetracker && echo "  ✓ Timetracker service: Running" || echo "  ✗ Timetracker service: Not running"
echo ""
