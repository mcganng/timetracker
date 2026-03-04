# Database Migration Guide

## For Existing Installations

If you installed the Time Tracker application **before** the schema was fixed, you need to manually add the missing columns to your database.

### Quick Check

To see if you need this migration, run:

```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "\d users"
```

If you **don't see** `hire_date` or `pto_time` columns, follow the migration steps below.

## Migration Steps

### Option 1: Using psql Command Line (Recommended)

```bash
# Connect to the database
sudo -u timetracker psql -U timetracker -d timetracker

# Run the migration SQL
ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date date;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pto_time numeric(10,2) DEFAULT 0;

# Verify the columns were added
\d users

# You should see:
#  hire_date    | date             |           |          |
#  pto_time     | numeric(10,2)    |           | not null | 0

# Exit
\q
```

### Option 2: One-Line Command

```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date date; ALTER TABLE users ADD COLUMN IF NOT EXISTS pto_time numeric(10,2) DEFAULT 0;"
```

### Option 3: Using SQL File

Create a migration file:

```bash
cat > /tmp/migrate_users.sql << 'EOF'
-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date date;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pto_time numeric(10,2) DEFAULT 0;

-- Verify
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name IN ('hire_date', 'pto_time');
EOF

# Run the migration
sudo -u timetracker psql -U timetracker -d timetracker -f /tmp/migrate_users.sql

# Clean up
rm /tmp/migrate_users.sql
```

## Verification

After running the migration, verify it worked:

```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT COUNT(*) as total_users, COUNT(hire_date) as users_with_hire_date, COUNT(pto_time) as users_with_pto FROM users;"
```

Expected output:
```
 total_users | users_with_hire_date | users_with_pto
-------------+----------------------+----------------
           1 |                    0 |              1
```

## Test the Application

After migration, test these pages:

1. **User Management** (`/admin/user-management`)
   - Should show all users without errors
   - Should display "Not Set" for hire dates
   - Should display "0.00" for PTO balances

2. **Manage User Data** (`/admin/manage-user-data`)
   - Should load without errors
   - Should allow setting hire dates and PTO time

## Rollback (If Needed)

If something goes wrong, you can remove the columns:

```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "ALTER TABLE users DROP COLUMN IF EXISTS hire_date; ALTER TABLE users DROP COLUMN IF EXISTS pto_time;"
```

**Note:** This will delete any hire date or PTO data you've entered!

## For Fresh Installations

If you're installing the Time Tracker application **after** commit `52eb7ab`, the schema is already correct and you don't need to run any migrations. The columns will be created automatically during installation.
