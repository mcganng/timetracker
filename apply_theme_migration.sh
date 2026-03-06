#!/bin/bash
# Apply theme migration to database
# Run this script as the administrator user with: bash apply_theme_migration.sh

echo "Applying theme preference migration..."

# Load database credentials
source /opt/timetracker/.env

# Apply migration
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /opt/timetracker/add_theme_preference.sql

if [ $? -eq 0 ]; then
    echo "Migration applied successfully!"
    echo "Theme column has been added to users table."
else
    echo "Migration failed. Please check the error messages above."
    exit 1
fi
