# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Savant Time Tracker** is a self-hosted Flask web application for time tracking, project management, and team utilization analytics. It uses PostgreSQL for data storage and runs behind Nginx as a reverse proxy.

**Tech Stack:**
- Backend: Flask 3.0 + Gunicorn (Python 3.12)
- Database: PostgreSQL with psycopg2
- Frontend: Bootstrap 5 + Chart.js
- Web Server: Nginx reverse proxy
- Deployment: systemd service

## Architecture

### Application Structure

The entire application is a **monolithic Flask app** in a single file:
- [app.py](app.py) (3,322 lines) - All routes, business logic, and database operations
- No separate models, services, or controller layers
- Session-based authentication with decorators (`@login_required`, `@admin_required`)

### Database Access Pattern

All database operations use **direct SQL with psycopg2**:
- Connection factory: `get_db_connection()` using `DB_CONFIG` from environment
- Always use `cursor_factory=psycopg2.extras.RealDictCursor` for dict-based results
- Pattern: open connection → execute query → fetch results → close connection
- No ORM (no SQLAlchemy or similar)

### Key Decorators

- `@login_required` - Validates `session['user_id']` exists
- `@admin_required` - Additionally checks `user.role == 'admin'` from database

## Development Commands

### Running the Application

```bash
# Start the service (production)
sudo systemctl start timetracker

# Stop the service
sudo systemctl stop timetracker

# Restart after code changes
sudo systemctl restart timetracker

# View logs
sudo journalctl -u timetracker -f

# Development mode (local testing)
source venv/bin/activate
python app.py
```

### Database Operations

```bash
# Connect to database
sudo -u timetracker psql -U timetracker -d timetracker

# Run a quick query
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT COUNT(*) FROM users;"

# Database backup (manual)
sudo -u timetracker /opt/timetracker/backup.sh

# View database schema
sudo -u timetracker psql -U timetracker -d timetracker -c "\d"
```

### Testing

```bash
# Run API tests (creates test users and validates endpoints)
python test_api.py

# Run UI tests
python test_ui.py
```

## Critical File Locations

- **Application:** `/opt/timetracker/app.py`
- **Templates:** `/opt/timetracker/templates/*.html` (permission: 0640, owner: timetracker)
- **Static files:** `/opt/timetracker/static/css/style.css`
- **Environment:** `/opt/timetracker/.env` (contains DB credentials, SECRET_KEY)
- **Database schema:** `/opt/timetracker/database/schema.sql` (initial schema only)
- **Systemd service:** `/etc/systemd/system/timetracker.service`
- **Nginx config:** `/etc/nginx/sites-available/timetracker`
- **Backups:** `/opt/timetracker/backups/` (daily automated + full system backups)

## Database Schema Key Tables

- `users` - Authentication, roles (user/admin), hire dates, PTO balances
- `time_entries` - Time logs with job codes, categories (Project/Admin/PTO)
- `project_budgets` - Project metadata with allocated hours and status
- `job_task_codes` - Configurable task codes with descriptions
- `admin_job_codes` - Admin overhead categories
- `holidays` - Company holidays (affects utilization calculations)

**Important:** The schema file is only used during installation. Schema changes must be done via SQL migrations, not by editing `schema.sql`.

## Route Organization (app.py)

Routes are grouped by functionality:

1. **Authentication** (lines 71-174): `/login`, `/register`, `/logout`
2. **Dashboard** (lines 180-445): Metrics, charts, holiday lookups
3. **Time Entry** (lines 447-742): CRUD for time entries, bulk import
4. **Projects** (lines 744-1006): Project management with budget tracking
5. **Configuration** (lines 1007-1308): Job codes, admin codes, holidays
6. **Admin Panel** (lines 1310-2103): User management, server config, code editor
7. **Reports** (lines 2601-3092): System-wide analytics for admins
8. **System Backup** (lines 3094-3322): Full backup/restore functionality

## Common Development Patterns

### Adding a New Route

```python
@app.route('/api/endpoint', methods=['POST'])
@login_required  # or @admin_required
def endpoint_name():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute('SELECT ...', (params,))
        results = cur.fetchall()
        conn.commit()  # if INSERT/UPDATE/DELETE
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()
```

### Working with Templates

Templates are in `/opt/timetracker/templates/` with restricted permissions (0640). To edit:
1. Use the admin Code Editor UI (`/admin/code-editor`)
2. Or temporarily adjust permissions: `sudo chmod 644 /opt/timetracker/templates/file.html`
3. After editing via Code Editor, app.py creates automatic backups: `file.html.backup.YYYYMMDD_HHMMSS`

### Environment Variables

Located in `/opt/timetracker/.env`:
```
SECRET_KEY=<flask-session-secret>
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=<db-password>
DB_PORT=5432
```

**Never commit .env to version control.** Changes require service restart.

## Special Admin Features

### Code Editor
- Route: `/admin/code-editor`
- Allows editing app.py, templates, CSS, .env in browser
- Auto-creates backups before saving
- Auto-restarts service when app.py is modified

### System Backup
- Route: `/admin/system-backup`
- Creates full `.tar.gz` archives containing:
  - Database dump (`database.sql`)
  - All application files (`timetracker_files.tar.gz`)
  - Restore script (`restore.sh`)
- Can download, restore, or delete backups through UI

### Server Configuration
- Route: `/admin/server-config`
- Manages timezone, NTP servers, network settings via subprocess calls
- Uses `timedatectl`, `systemd-timesyncd`, `netplan` commands

## Deployment Architecture

```
[Browser]
    ↓ HTTP/HTTPS (port 80/443)
[Nginx]
    ↓ Reverse proxy to localhost:5000
[Gunicorn]
    ↓ WSGI server with 4 workers
[Flask App (app.py)]
    ↓ psycopg2 connections
[PostgreSQL]
    localhost:5432, database: timetracker
```

### Service Management

The application runs as a systemd service:
- User: `timetracker` (dedicated system user)
- Working directory: `/opt/timetracker`
- Gunicorn with 4 workers on `127.0.0.1:5000`
- Automatically restarts on failure (`RestartSec=10`)

After modifying app.py or .env:
```bash
sudo systemctl daemon-reload  # if .service file changed
sudo systemctl restart timetracker
```

## Important Conventions

### Date Handling
- Database stores dates as DATE type (PostgreSQL)
- Frontend sends dates as `YYYY-MM-DD` strings
- Python uses `datetime.date` or `datetime.datetime` objects
- Always use parameterized queries: `cur.execute('... WHERE date = %s', (date_value,))`

### User Roles
- `role = 'user'` - Standard users (can only see own data)
- `role = 'admin'` - Admins (can see all data, manage users, edit code)
- Check role in database, not in session (session stores it but always verify)

### Time Entry Categories
- `'Project'` - Billable project work
- `'Admin'` - Non-billable overhead
- `'PTO'` - Paid time off

### File Permissions
The app runs as user `timetracker:timetracker`. Key directories:
- `/opt/timetracker/` - Main app directory (drwxrwsr-x)
- `/opt/timetracker/templates/` - Templates (drwx-wS---)
- `/opt/timetracker/database/` - Database files (drwx-wS---)
- `/opt/timetracker/backups/` - Backup storage

When adding new files, ensure proper ownership: `sudo chown timetracker:timetracker file`

## Troubleshooting

### Application won't start
1. Check logs: `sudo journalctl -u timetracker -n 50 --no-pager`
2. Verify database: `sudo systemctl status postgresql`
3. Test connection: `sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"`
4. Check .env credentials

### Import errors or missing dependencies
```bash
source /opt/timetracker/venv/bin/activate
pip install -r /opt/timetracker/requirements.txt
```

### Database schema changes
Never edit `database/schema.sql` directly for existing deployments. Instead:
1. Write migration SQL
2. Apply manually: `sudo -u timetracker psql -U timetracker -d timetracker -f migration.sql`
3. Document in migration log

### Permission errors when editing files
Templates and database directories have restrictive permissions. Either:
- Use the Code Editor UI (`/admin/code-editor`)
- Temporarily grant access: `sudo chmod 644 file` then revert after editing

## API Response Patterns

**Success:**
```json
{"success": true, "data": [...]}
```

**Error:**
```json
{"error": "Error message"}
```
HTTP status codes: 400 (bad request), 401 (unauthorized), 403 (forbidden), 500 (server error)

## Testing Strategy

When making changes:
1. Edit code
2. Restart service: `sudo systemctl restart timetracker`
3. Check logs: `sudo journalctl -u timetracker -f`
4. Test in browser or with `test_api.py`
5. For database changes, test with small dataset first
6. Create backup before major changes: `/admin/system-backup`

## Performance Notes

- Gunicorn uses 4 workers by default (tune in `/etc/systemd/system/timetracker.service`)
- Database queries are not cached; each request opens a new connection
- For large datasets (1000+ time entries), consider adding pagination to time entry endpoints
- Chart.js rendering happens client-side; large datasets may slow browser

## Security Considerations

- All passwords hashed with `werkzeug.security.generate_password_hash`
- Session-based authentication (Flask sessions with SECRET_KEY)
- Database only accessible from localhost
- Admin routes protected with `@admin_required` decorator
- Code editor creates backups before saving to prevent destructive changes
- File upload/edit paths validated to prevent directory traversal

## Backup Strategy

1. **Database backups**: Daily at 2 AM via cron (stored in `/opt/timetracker/backups/`)
2. **Full system backups**: On-demand via UI (`/admin/system-backup`)
3. **Code edit backups**: Automatic when using Code Editor (`.backup.YYYYMMDD_HHMMSS` files)

**Restore full backup:** Extract `.tar.gz` and run `sudo bash restore.sh`
