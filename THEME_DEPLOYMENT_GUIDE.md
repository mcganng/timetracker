# Dark/Light Theme Feature - Deployment Guide

This guide explains how to deploy the new dark/light theme toggle feature.

## Overview

A theme toggle has been added to the user dropdown menu (top right corner) that allows users to switch between light and dark themes. The preference is saved per user in the database.

## Changes Made

### 1. Database Schema
- **File**: `add_theme_preference.sql`
- **Changes**: Adds a `theme` column to the `users` table with values 'light' or 'dark'

### 2. Backend (app.py)
- **New Endpoint**: `/api/user/theme` (POST) - Saves user's theme preference
- **Login Update**: Modified login function to load theme preference into session
- **Location**: Lines 2022-2055 (new endpoint), Line 111 (login update)

### 3. Frontend Templates
- **File**: `templates_git/base.html`
- **Changes**:
  - Added theme toggle button to user dropdown (lines 65-68)
  - Added `dark-theme` class to body tag based on session (line 17)
  - Added JavaScript for theme switching (lines 93-146)

### 4. Styles
- **File**: `static/css/style.css`
- **Changes**:
  - Added CSS variables for light/dark themes
  - Updated all components to use CSS variables
  - Added smooth transitions between themes

## Deployment Steps

### Step 1: Copy Template to Production
```bash
sudo cp /opt/timetracker/templates_git/base.html /opt/timetracker/templates/base.html
sudo chown timetracker:timetracker /opt/timetracker/templates/base.html
sudo chmod 640 /opt/timetracker/templates/base.html
```

### Step 2: Apply Database Migration
```bash
# Option A: Using sudo to run as timetracker user
sudo -u timetracker psql -U timetracker -d timetracker -f /opt/timetracker/add_theme_preference.sql

# Option B: Using the migration script (requires .env access)
sudo bash /opt/timetracker/apply_theme_migration.sh
```

### Step 3: Restart the Service
```bash
sudo systemctl restart timetracker
```

### Step 4: Verify Deployment
1. Open the application in a browser
2. Log in with your credentials
3. Click on your username in the top right corner
4. You should see "Dark Theme" as the first option in the dropdown
5. Click it to toggle to dark theme
6. The icon should change to a sun and the text to "Light Theme"
7. Refresh the page - your theme preference should persist

## Testing Checklist

- [ ] Theme toggle appears in user dropdown menu
- [ ] Clicking toggle switches between light and dark themes
- [ ] Theme preference persists after page refresh
- [ ] Theme preference persists after logout/login
- [ ] All pages respect the theme setting
- [ ] Forms and inputs are readable in both themes
- [ ] Tables and cards display correctly in both themes
- [ ] Dropdown menus work properly in both themes
- [ ] Modals (if any) display correctly in both themes

## Rollback Instructions

If you need to rollback this feature:

### 1. Restore Original Template
```bash
# If you have a backup
sudo cp /opt/timetracker/templates/base.html.backup.* /opt/timetracker/templates/base.html

# Or use git
cd /opt/timetracker
git checkout HEAD -- templates_git/base.html
sudo cp templates_git/base.html templates/base.html
```

### 2. Remove API Endpoint (Optional)
Edit `app.py` and remove lines 2022-2055 (the `/api/user/theme` endpoint)

### 3. Remove Database Column (Optional)
```sql
ALTER TABLE users DROP COLUMN IF EXISTS theme;
```

### 4. Restart Service
```bash
sudo systemctl restart timetracker
```

## Files Modified

1. `/opt/timetracker/app.py` - Added theme endpoint and updated login
2. `/opt/timetracker/templates_git/base.html` - Added theme toggle UI and JavaScript
3. `/opt/timetracker/static/css/style.css` - Added dark theme styles
4. `/opt/timetracker/add_theme_preference.sql` - Database migration
5. `/opt/timetracker/apply_theme_migration.sh` - Migration helper script

## Technical Details

### Theme Storage
- User theme preference is stored in the `users.theme` column (VARCHAR(10))
- Default value is 'light'
- Valid values: 'light', 'dark'

### Theme Application
- Theme is loaded into session during login
- Session variable: `session['theme']`
- Applied via body class: `<body class="dark-theme">` for dark mode
- JavaScript toggles the class and saves to database via API

### CSS Implementation
- Uses CSS custom properties (variables) for theming
- All colors defined in `:root` and `body.dark-theme`
- Smooth transitions (0.3s) between theme changes
- Maintains Bootstrap's responsive classes

## Troubleshooting

### Theme Not Persisting
- Check database migration was applied: `sudo -u timetracker psql -U timetracker -d timetracker -c "\d users"`
- Should show a `theme` column
- Check browser console for API errors

### Styles Not Updating
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Verify style.css was updated correctly
- Check browser developer tools for CSS errors

### Toggle Not Appearing
- Verify base.html template was copied to production
- Check file permissions: `ls -la /opt/timetracker/templates/base.html`
- Should be: `-rw-r----- 1 timetracker timetracker`

### API Endpoint Failing
- Check app.py was saved correctly
- Verify service restarted: `sudo systemctl status timetracker`
- Check logs: `sudo journalctl -u timetracker -n 50`

## Support

For issues or questions, check:
1. Application logs: `sudo journalctl -u timetracker -f`
2. Browser console for JavaScript errors
3. Network tab in browser dev tools for API calls
