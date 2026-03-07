# Dark/Light Theme Setup for Fresh Installations

If you've installed Savant Time Tracker from GitHub and the dark theme doesn't persist across page navigation, follow these steps:

## Problem

- Theme toggle appears and works
- Theme changes on current page
- But theme resets to light when navigating to other pages
- Theme preference doesn't persist after refresh

## Root Cause

The database is missing the `theme` column in the `users` table. This happens on fresh installs because the migration needs to be applied manually.

## Solution

Run these commands to add theme support:

### Step 1: Apply Database Migration

```bash
sudo -u timetracker psql -U timetracker -d timetracker -f /opt/timetracker/add_theme_preference.sql
```

**Expected Output:**
```
ALTER TABLE
ALTER TABLE
CREATE INDEX
```

If you see errors about the column already existing, that's okay - it means it's already there.

### Step 2: Verify Database Schema

Check that the theme column was added:

```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "\d users" | grep theme
```

**Expected Output:**
```
 theme         | character varying(10)       |           | not null | 'light'::character varying
```

### Step 3: Restart the Service

```bash
sudo systemctl restart timetracker
```

### Step 4: Test

1. Log out and log back in
2. Switch to dark theme
3. Navigate to different pages (Dashboard → Time Entry → Projects)
4. Theme should now persist!

## Automated Setup Script

Or use the automated deployment script:

```bash
sudo bash /opt/timetracker/deploy_theme.sh
```

This will:
- Copy the latest template to production
- Apply the database migration
- Restart the service
- Verify everything is working

## For Fresh GitHub Clones

If you're setting up a completely new installation from GitHub:

### 1. Ensure Migration File Exists

Check if the migration file is present:

```bash
ls -la /opt/timetracker/add_theme_preference.sql
```

If missing, create it:

```bash
cat > /opt/timetracker/add_theme_preference.sql << 'EOF'
-- Migration: Add theme preference to users table
-- Date: 2026-03-06
-- Description: Adds a theme column to store user's preferred theme (light/dark)

ALTER TABLE users
ADD COLUMN IF NOT EXISTS theme VARCHAR(10) DEFAULT 'light' NOT NULL;

-- Add a constraint to ensure only valid theme values
ALTER TABLE users
ADD CONSTRAINT check_theme_valid CHECK (theme IN ('light', 'dark'));

-- Create an index for faster theme lookups
CREATE INDEX IF NOT EXISTS idx_users_theme ON users(theme);
EOF
```

### 2. Apply Migration

```bash
sudo -u timetracker psql -U timetracker -d timetracker -f /opt/timetracker/add_theme_preference.sql
```

### 3. Restart

```bash
sudo systemctl restart timetracker
```

## Verification Checklist

After setup, verify everything works:

- [ ] Can see "Dark Theme" option in user dropdown
- [ ] Clicking toggle switches theme immediately
- [ ] Theme persists when navigating between pages
- [ ] Theme persists after browser refresh
- [ ] Theme persists after logout/login
- [ ] No console errors in browser DevTools (F12)

## Troubleshooting

### Theme Still Not Persisting

**Check if migration was applied:**
```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "\d users" | grep theme
```

If you don't see the `theme` column, the migration didn't apply. Try running it again.

**Check for errors in service logs:**
```bash
journalctl -u timetracker -n 50 | grep -i error
```

**Check database connection:**
```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT username, theme FROM users LIMIT 1;"
```

### API Endpoint Not Working

**Verify endpoint exists in app.py:**
```bash
grep -n "def update_user_theme" /opt/timetracker/app.py
```

Should show line number (around 2025).

**Check if login loads theme:**
```bash
grep "session\['theme'\]" /opt/timetracker/app.py
```

Should show 2 occurrences (in login and in update_user_theme functions).

### Browser Cache Issues

Clear browser cache completely:
- Chrome/Edge: Ctrl+Shift+Delete → Clear cached images and files
- Firefox: Ctrl+Shift+Delete → Cache
- Or use Ctrl+Shift+F5 for hard refresh

### Service Not Restarting

```bash
# Check service status
sudo systemctl status timetracker

# If failed, check logs
sudo journalctl -u timetracker -n 100

# Force restart
sudo systemctl stop timetracker
sleep 2
sudo systemctl start timetracker
```

## Integration with schema.sql

**Important:** For future fresh installations, the theme support should be added to the base `schema.sql` file.

To update `database_git/schema.sql` to include theme support by default:

```sql
-- Find the users table definition and modify it:
CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    role character varying(20) DEFAULT 'user'::character varying,
    is_active boolean DEFAULT true NOT NULL,
    hire_date date,
    pto_time numeric(10,2) DEFAULT 0,
    theme character varying(10) DEFAULT 'light'::character varying NOT NULL,
    CONSTRAINT check_theme_valid CHECK (theme IN ('light', 'dark'))
);

-- And add the index:
CREATE INDEX idx_users_theme ON public.users USING btree (theme);
```

## Summary

Fresh installations need:
1. ✅ Code from GitHub (includes theme UI + API)
2. ✅ Database migration (adds theme column)
3. ✅ Service restart

Without the database migration, the theme toggle will work temporarily (client-side only) but won't persist because the database can't store the preference.

---

**Last Updated:** 2026-03-06
