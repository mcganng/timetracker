#!/bin/bash
#
# Test Sudo Permissions for Time Tracker
# This script tests whether the timetracker user can run sudo commands
#

echo "========================================"
echo "Time Tracker - Sudo Permission Test"
echo "========================================"
echo ""

# Test 1: Check if sudoers file exists
echo "[Test 1] Checking if sudoers file exists..."
if [ -f /etc/sudoers.d/timetracker ]; then
    echo "  ✓ /etc/sudoers.d/timetracker exists"
    echo "  Permissions: $(ls -l /etc/sudoers.d/timetracker)"
else
    echo "  ✗ /etc/sudoers.d/timetracker NOT FOUND"
    echo "  You need to run: sudo /opt/timetracker/fix_server_config.sh"
    exit 1
fi

echo ""

# Test 2: Validate sudoers syntax
echo "[Test 2] Validating sudoers file syntax..."
if sudo visudo -c -f /etc/sudoers.d/timetracker > /dev/null 2>&1; then
    echo "  ✓ Sudoers file syntax is valid"
else
    echo "  ✗ Sudoers file has syntax errors!"
    exit 1
fi

echo ""

# Test 3: Check systemd service file
echo "[Test 3] Checking systemd service configuration..."
if grep -q "NoNewPrivileges=false" /etc/systemd/system/timetracker.service; then
    echo "  ✓ NoNewPrivileges=false is set correctly"
else
    echo "  ✗ NoNewPrivileges is not set to false!"
    grep "NoNewPrivileges" /etc/systemd/system/timetracker.service
    exit 1
fi

echo ""

# Test 4: Test sudo as timetracker user
echo "[Test 4] Testing sudo permissions as timetracker user..."
if sudo -u timetracker sudo -n -l > /dev/null 2>&1; then
    echo "  ✓ timetracker user can run sudo commands"
    echo ""
    echo "  Available commands:"
    sudo -u timetracker sudo -l | grep -A 10 "User timetracker"
else
    echo "  ✗ timetracker user CANNOT run sudo commands"
    echo "  This is the root cause of the problem!"
fi

echo ""

# Test 5: Test timedatectl command
echo "[Test 5] Testing timedatectl command..."
if sudo -u timetracker sudo /usr/bin/timedatectl list-timezones > /dev/null 2>&1; then
    echo "  ✓ timedatectl command works"
    echo "  Sample timezones:"
    sudo -u timetracker sudo /usr/bin/timedatectl list-timezones | head -3
else
    echo "  ✗ timedatectl command FAILED"
fi

echo ""

# Test 6: Check service status
echo "[Test 6] Checking timetracker service status..."
if systemctl is-active --quiet timetracker; then
    echo "  ✓ timetracker service is running"
else
    echo "  ✗ timetracker service is NOT running"
fi

echo ""
echo "========================================"
echo "Test Complete"
echo "========================================"
