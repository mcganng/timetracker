#!/bin/bash
# Theme Status Diagnostic Script
# Run with: bash check_theme_status.sh

echo "=========================================="
echo "Theme Feature Diagnostic Report"
echo "=========================================="
echo ""

echo "1. Checking template files..."
echo "----------------------------"
if [ -f /opt/timetracker/templates/base.html ]; then
    echo "✓ Production template exists"
    PROD_SIZE=$(wc -l < /opt/timetracker/templates/base.html 2>/dev/null || echo "0")
    echo "  Lines: $PROD_SIZE"

    # Check if it contains theme toggle
    if grep -q "themeToggle" /opt/timetracker/templates/base.html 2>/dev/null; then
        echo "✓ Template contains theme toggle code"
    else
        echo "✗ Template does NOT contain theme toggle code"
        echo "  ACTION: Run 'sudo bash /opt/timetracker/deploy_theme.sh'"
    fi
else
    echo "✗ Production template NOT found"
fi

if [ -f /opt/timetracker/templates_git/base.html ]; then
    echo "✓ Git template exists"
    GIT_SIZE=$(wc -l < /opt/timetracker/templates_git/base.html)
    echo "  Lines: $GIT_SIZE"
fi
echo ""

echo "2. Checking database schema..."
echo "----------------------------"
sudo -u timetracker psql -U timetracker -d timetracker -c "\d users" 2>/dev/null | grep "theme" && echo "✓ Theme column exists" || echo "✗ Theme column NOT found - run migration"
echo ""

echo "3. Checking app.py for theme endpoint..."
echo "----------------------------"
if grep -q "/api/user/theme" /opt/timetracker/app.py; then
    echo "✓ Theme API endpoint found in app.py"
    grep -n "def update_user_theme" /opt/timetracker/app.py | head -1
else
    echo "✗ Theme API endpoint NOT found in app.py"
fi
echo ""

echo "4. Checking CSS for dark theme..."
echo "----------------------------"
if grep -q "dark-theme" /opt/timetracker/static/css/style.css; then
    echo "✓ Dark theme CSS found"
    grep -n "body.dark-theme" /opt/timetracker/static/css/style.css | head -1
else
    echo "✗ Dark theme CSS NOT found"
fi
echo ""

echo "5. Checking service status..."
echo "----------------------------"
if systemctl is-active --quiet timetracker; then
    echo "✓ Service is running"
    echo "  Uptime: $(systemctl show -p ActiveEnterTimestamp timetracker --value)"
else
    echo "✗ Service is NOT running"
fi
echo ""

echo "6. Recent service errors..."
echo "----------------------------"
ERRORS=$(journalctl -u timetracker --no-pager -n 100 | grep -i error | wc -l)
if [ "$ERRORS" -eq 0 ]; then
    echo "✓ No recent errors in service logs"
else
    echo "⚠ Found $ERRORS error(s) in recent logs"
    echo "  View with: journalctl -u timetracker -n 50"
fi
echo ""

echo "=========================================="
echo "Recommendations:"
echo "=========================================="

# Determine what needs to be done
NEEDS_DEPLOY=0

if ! grep -q "themeToggle" /opt/timetracker/templates/base.html 2>/dev/null; then
    echo "→ Template needs to be deployed"
    NEEDS_DEPLOY=1
fi

if ! sudo -u timetracker psql -U timetracker -d timetracker -c "\d users" 2>/dev/null | grep -q "theme"; then
    echo "→ Database migration needs to be applied"
    NEEDS_DEPLOY=1
fi

if [ "$NEEDS_DEPLOY" -eq 1 ]; then
    echo ""
    echo "Run this command to deploy:"
    echo "  sudo bash /opt/timetracker/deploy_theme.sh"
else
    echo "✓ All components appear to be deployed correctly!"
    echo ""
    echo "If theme toggle still doesn't work:"
    echo "1. Clear browser cache (Ctrl+F5 or Cmd+Shift+R)"
    echo "2. Check browser console for JavaScript errors"
    echo "3. Try logging out and back in"
fi
echo ""
