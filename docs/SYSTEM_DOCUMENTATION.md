# Savant Time Tracker - Complete System Documentation
## Comprehensive Reference for All Features, Configuration, and Settings

**Version:** 1.0
**Generated:** 2026-02-26
**Application:** Savant Time Tracker
**Type:** Self-hosted Flask Web Application

---

## 📋 Table of Contents

### Part 1: System Overview
1. [Introduction](#introduction)
2. [System Architecture](#architecture)
3. [Technology Stack](#tech-stack)
4. [File Structure](#file-structure)

### Part 2: Features & Functionality
5. [User Authentication](#authentication)
6. [Dashboard & Metrics](#dashboard)
7. [Time Entry System](#time-entry)
8. [Project Management](#projects)
9. [Bulk Import](#bulk-import)
10. [Configuration Management](#configuration)
11. [Employment Information](#employment)
12. [Admin Panel](#admin-panel)

### Part 3: Admin Features
13. [User Management](#user-management)
14. [Manage User Data](#manage-user-data)
15. [Server Configuration](#server-config)
16. [Code Editor](#code-editor)
17. [System Reports](#system-reports)
18. [System Backup](#system-backup)
19. [Team Dashboard](#team-dashboard)

### Part 4: Technical Reference
20. [Complete API Reference](#api-reference)
21. [Database Schema](#database-schema)
22. [UI Templates](#ui-templates)
23. [Configuration Files](#config-files)

### Part 5: Installation & Deployment
24. [Installation Guide](#installation)
25. [Configuration Options](#configuration-options)
26. [Security](#security)
27. [Backup & Restore](#backup-restore)
28. [Troubleshooting](#troubleshooting)

---

# Part 1: System Overview

## Introduction {#introduction}

**Savant Time Tracker** is a comprehensive, self-hosted web application for tracking work hours, managing projects, and analyzing team utilization. Built with Flask and PostgreSQL, it provides:

- **Multi-user time tracking** with secure authentication
- **Project budget management** with real-time tracking
- **PTO and holiday tracking** with anniversary-based resets
- **Comprehensive reporting** for admins and managers
- **Flexible configuration** for job codes, admin codes, and holidays
- **System administration** including backups, user management, and server configuration

### Key Capabilities

✅ **For Users:**
- Log time against projects and admin codes
- Track PTO usage and remaining balance
- View personal utilization metrics
- Manage projects and budgets
- Export data to CSV

✅ **For Admins:**
- Manage all user accounts
- Edit any user's time entries
- Configure system settings (timezone, NTP, network)
- Generate team-wide reports
- Create and restore full system backups
- Edit application code in-browser

---

## System Architecture {#architecture}

### Application Stack

```
┌─────────────────────────────────────────┐
│         User Browser (Client)           │
│     HTML5 + Bootstrap 5 + Chart.js      │
└─────────────────────────────────────────┘
                    ↓ HTTP/HTTPS
┌─────────────────────────────────────────┐
│          Nginx (Reverse Proxy)          │
│         Port 80/443 → Port 5000         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       Flask Application (Python)        │
│      Gunicorn WSGI Server (4 workers)   │
│           Port 5000 (internal)          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      PostgreSQL Database Server         │
│        Port 5432 (localhost only)       │
└─────────────────────────────────────────┘
```

### Process Flow

1. **User Request** → Nginx → Flask Application
2. **Authentication** → Session-based with Flask sessions
3. **Database Query** → PostgreSQL via psycopg2
4. **Response** → JSON (API) or HTML (Pages)
5. **Client Rendering** → Bootstrap + Vanilla JavaScript

---

## Technology Stack {#tech-stack}

### Backend
- **Language:** Python 3.8+
- **Framework:** Flask 2.x
- **WSGI Server:** Gunicorn
- **Database:** PostgreSQL 12+
- **Database Driver:** psycopg2

### Frontend
- **HTML:** HTML5
- **CSS:** Bootstrap 5.3
- **JavaScript:** Vanilla JS (ES6+)
- **Charts:** Chart.js 4.4
- **Icons:** Bootstrap Icons

### Server
- **OS:** Ubuntu 20.04 LTS or later
- **Web Server:** Nginx
- **Process Manager:** systemd
- **Backup:** pg_dump + tar

### Python Dependencies
```
Flask==2.3.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.6
Werkzeug==2.3.0
gunicorn==21.2.0
```

---

## File Structure {#file-structure}

```
/opt/timetracker/
├── app.py                    # Main Flask application (2,947 lines)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (DB config, etc.)
├── install.sh               # Automated installation script
├── backup.sh                # Database backup script
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html           # Base template with navigation
│   ├── login.html          # Login & registration
│   ├── dashboard.html      # Main dashboard with metrics
│   ├── time_entry.html     # Time entry form
│   ├── projects.html       # Project management
│   ├── bulk_import.html    # CSV bulk import
│   ├── config.html         # Configuration page
│   ├── admin.html          # Admin panel home
│   ├── user_management.html    # User management
│   ├── manage_user_data.html   # Edit user time entries
│   ├── server-config.html      # Server configuration
│   ├── code_editor.html        # In-browser code editor
│   ├── reports.html            # System reports
│   ├── system_backup.html      # Backup management
│   ├── team_dashboard.html     # Team metrics (admin)
│   └── change_password.html    # Password change form
│
├── static/                  # Static assets (CSS, JS, images)
│   └── css/
│       └── style.css       # Custom styles
│
├── backups/                # Automated daily backups
│   ├── db_backup_*.sql.gz  # Database backups
│   └── full/               # Full system backups
│       └── timetracker_backup_*.tar.gz
│
├── venv/                   # Python virtual environment
├── __pycache__/           # Python compiled files
├── database/              # Database-related files (if any)
├── netplan-backups/       # Network config backups
└── ntp-backups/           # NTP config backups
```

---

# Part 2: Features & Functionality

## User Authentication {#authentication}

### Login System
- **Session-based authentication** using Flask sessions
- **Password hashing** with Werkzeug's generate_password_hash
- **Role-based access control** (user vs admin)
- **Account activation/deactivation** by admins

### User Roles

**User:**
- Log time entries
- View own dashboard
- Manage own projects
- View configuration
- Change own password

**Admin:**
- All user capabilities
- Manage all users
- Edit any user's data
- Configure system settings
- Access admin panel
- Create backups

### Routes

```python
GET  /                     # Home (redirects to login or dashboard)
POST /login                # User login
GET  /logout               # User logout
POST /register             # User registration (with optional hire_date, pto_time)
GET  /user/change-password-page   # Password change form
POST /api/user/change-password    # Update own password
```

### Registration Fields

**Required:**
- Username (unique)
- Email (unique)
- Password (min 8 characters)
- Full Name

**Optional:**
- Date of Hire (for PTO tracking)
- Total PTO Time (hours allocated annually)

---

## Dashboard & Metrics {#dashboard}

### Overview
The dashboard provides real-time metrics, charts, and project tracking for the selected date range.

### Metric Cards

1. **Total Hours**
   - Sum of all hours logged (excluding holidays)
   - Shows weeks in period and available hours (40 hrs/week)

2. **Project Hours**
   - Sum of hours logged against projects
   - Project utilization % (project hours / available hours)

3. **Admin Hours**
   - Sum of hours logged against admin codes
   - Admin utilization % (admin hours / available hours)

4. **PTO Hours** (Enhanced)
   - PTO hours taken (in selected range)
   - Holiday hours taken (in selected range)
   - **PTO Remaining** (if configured)
   - **Total PTO Allowed** (if configured)
   - **Reset Date** (hire date anniversary)
   - **Days Until Reset**
   - Color-coded balance (green/yellow/red)

5. **Upcoming Holidays**
   - Shows next 3 upcoming company holidays
   - Date and holiday name

### Features

**Active Projects Budget Tracking:**
- Table of all active projects
- Budget hours, hours used, hours remaining
- % budget used with color-coded progress bar
- Sortable columns
- Total row with sum of all projects

**Project Hours by Task:**
- Breakdown of project hours by task code
- Task name and hours logged
- Total project hours

**Historical Utilization Chart:**
- Line chart showing last 12 weeks
- Project utilization % trend
- Admin utilization % trend
- Powered by Chart.js

### Understanding Utilization Calculations

The dashboard uses **two different utilization calculation methods** for different purposes. Understanding the difference is important for interpreting your metrics correctly.

#### Method 1: Dashboard Metric Cards (Capacity-Based)

**Used in:** Project Hours and Admin Hours metric cards

**Formula:**
```
Project Utilization % = (Project Hours / Available Hours) × 100
Admin Utilization % = (Admin Hours / Available Hours) × 100

Where:
  Available Hours = (Number of Weeks in Date Range) × 40 hours/week
```

**Purpose:** Measures how much of your **available work capacity** you used for billable vs non-billable work.

**Example:**
- Date range: 2 weeks (14 days)
- Available hours: 2 weeks × 40 = 80 hours
- Logged: 50 hours Project, 10 hours Admin
- **Project Utilization: (50 / 80) × 100 = 62.5%**
- **Admin Utilization: (10 / 80) × 100 = 12.5%**

**Key Characteristic:** These percentages typically **do not add up to 100%** because they're measured against your total available time (which may include unlogged hours, PTO, etc.).

#### Method 2: Historical Utilization Chart (Proportion-Based)

**Used in:** Historical Utilization Over Time chart (past 12 weeks)

**Formula:**
```
Project Utilization % = (Project Hours / Total Logged Hours) × 100
Admin Utilization % = (Admin Hours / Total Logged Hours) × 100

Where:
  Total Logged Hours = Project Hours + Admin Hours + PTO Hours
```

**Purpose:** Shows the **proportion** of your actual logged time that was billable vs non-billable work.

**Example:**
- Week of 02/17: Logged 50 hours Project, 10 hours Admin
- Total logged: 60 hours
- **Project Utilization: (50 / 60) × 100 = 83.3%**
- **Admin Utilization: (10 / 60) × 100 = 16.7%**

**Key Characteristic:** Project % + Admin % will often **add up close to 100%** (assuming minimal PTO that week), because you're dividing by actual logged time.

#### Why Two Different Methods?

| Metric Cards (Capacity-Based) | Historical Chart (Proportion-Based) |
|-------------------------------|-------------------------------------|
| Answers: "How much of my available time did I use?" | Answers: "Of the time I worked, how much was billable?" |
| Shows absolute productivity | Shows work composition |
| Includes impact of time off, unlogged hours | Only considers logged work |
| Better for capacity planning | Better for billing analysis |
| Can be low if you took PTO or didn't log all hours | Always accounts for 100% of logged time |

#### Practical Example Comparing Both Methods

**Scenario:** You worked 2 weeks and logged the following:
- Project work: 60 hours
- Admin work: 15 hours
- PTO: 5 hours
- **Total logged: 80 hours**

**Dashboard Metric Cards show:**
- Available: 2 weeks × 40 = 80 hours
- Project Utilization: (60 / 80) × 100 = **75%**
- Admin Utilization: (15 / 80) × 100 = **18.75%**

**Historical Chart shows:**
- Total logged: 80 hours
- Project Utilization: (60 / 80) × 100 = **75%**
- Admin Utilization: (15 / 80) × 100 = **18.75%**

*In this case they match because you logged exactly 80 hours!*

**But if you only logged 60 hours total (Project: 50, Admin: 10):**

**Dashboard Metric Cards:**
- Project Utilization: (50 / 80) × 100 = **62.5%** ← vs. available time
- Admin Utilization: (10 / 80) × 100 = **12.5%** ← vs. available time

**Historical Chart:**
- Project Utilization: (50 / 60) × 100 = **83.3%** ← of logged time
- Admin Utilization: (10 / 60) × 100 = **16.7%** ← of logged time

**Interpretation:**
- You used 62.5% of your available capacity on projects (dashboard)
- But 83.3% of your actual work time was billable (chart)
- This indicates you either took time off or didn't log 20 hours

### Routes

```python
GET /dashboard                        # Dashboard page
GET /api/dashboard/metrics            # Get metrics for date range
GET /api/dashboard/utilization-history  # Get historical chart data
GET /api/dashboard/upcoming-holidays    # Get next 3 holidays
```

### PTO Year Calculation

PTO resets annually on the user's hire date anniversary:
- Current PTO Year = Last hire date anniversary → Next anniversary
- PTO Remaining = Total PTO Allowed - PTO used since last anniversary
- Reset Date = Next hire date anniversary
- Days Until Reset = Reset Date - Today

**Example:**
- Hire Date: March 15, 2024
- Today: February 20, 2027
- PTO Year: March 15, 2026 → March 14, 2027
- Reset Date: March 15, 2027
- Days Until Reset: 23 days

---

## Time Entry System {#time-entry}

### Overview
The time entry system allows users to log hours against projects or admin codes.

### Features

**Log Time:**
- Select date
- Choose category (Project, Admin, PTO, Holiday)
- Select job number (projects) or admin code
- Select task code (for projects)
- Enter hours worked
- Add description

**Manage Entries:**
- View all time entries in table
- Filter by date range
- Edit existing entries
- Delete entries
- Inline editing

**Validation:**
- Date required
- Hours must be positive
- Category required
- Job number/admin code required based on category
- Task code required for projects

### Categories

1. **Project** - Work on customer projects
   - Requires job number
   - Requires task code
   - Counts toward project utilization

2. **Admin** - Administrative/overhead work
   - Requires admin code
   - Counts toward admin utilization
   - Examples: Meetings, Training, General Admin

3. **PTO** - Paid Time Off
   - Does not require job/admin code
   - Deducts from PTO balance
   - Resets on hire date anniversary

4. **Holiday** - Company holidays
   - Does not require job/admin code
   - Does not count against PTO
   - Typically matches company holidays configuration

### Routes

```python
GET    /time-entry                    # Time entry page
GET    /api/time-entries              # Get time entries (filtered by user)
POST   /api/time-entries              # Create time entry
PUT    /api/time-entries/<id>         # Update time entry
DELETE /api/time-entries/<id>         # Delete time entry
```

### API Examples

**Create Time Entry:**
```json
POST /api/time-entries
{
  "entry_date": "2027-02-25",
  "category": "Project",
  "job_number": "24-001",
  "job_task_code": "100",
  "hours": 8.0,
  "description": "Developed new feature"
}
```

**Get Time Entries:**
```
GET /api/time-entries?start_date=2027-02-01&end_date=2027-02-28
```

---

## Project Management {#projects}

### Overview
Manage project budgets and track hours against active and closed projects.

### Project Fields

- **Job Number** (unique) - Project identifier
- **Customer Name** - Client name
- **Project Description** - Optional description
- **Budget Hours** - Total hours allocated
- **Start Date** - Optional project start
- **End Date** - Optional project end
- **Status** - Active or Closed
- **User Assignment** - Which user owns this project

### Features

**View Projects:**
- List all active projects
- List all closed projects
- View budget vs actual hours
- See % budget used

**Create Project:**
- Add new project with budget
- Set active/closed status
- Assign to user

**Edit Project:**
- Update budget hours
- Change status
- Modify dates and description

**Delete Project:**
- Remove project (admin only)
- Warning if time entries exist

**Project Lookup:**
- Quick lookup by job number
- Returns customer name and description
- Used by time entry form

### Routes

```python
GET    /projects                      # Projects page
GET    /api/projects                  # Get projects (filtered by user/status)
POST   /api/projects                  # Create project
PUT    /api/projects/<id>             # Update project
DELETE /api/projects/<id>             # Delete project
GET    /api/projects/lookup/<job_number>  # Lookup project details
GET    /api/projects/with-usage       # Projects with usage stats
```

### Budget Tracking

Projects show real-time budget consumption:
- **Budget Hours:** Total allocated
- **Hours Used:** Sum of time entries
- **Hours Remaining:** Budget - Used
- **% Used:** (Used / Budget) × 100

Color coding:
- 🟢 Green: < 80% used
- 🟡 Yellow: 80-99% used
- 🔴 Red: ≥ 100% used (over budget)

---

## Bulk Import {#bulk-import}

### Overview
Import multiple time entries from CSV file (Savant format with tab separators).

### Features

**Upload CSV:**
- Tab-separated values (TSV)
- Specific column format expected
- Validates all entries before import

**Preview:**
- Shows all entries to be imported
- Displays warnings/errors
- Confirms before importing

**Import:**
- Batch insert all valid entries
- Skips invalid entries
- Reports success/failure count

### Expected CSV Format

```
Date    Job Number    Job Task No    Description    Hours    Category    Customer Name    Job Description
2027-02-25    24-001    100    Development work    8.0    Project    Acme Corp    Website Redesign
2027-02-25    ADMIN    001    Team meeting    1.5    Admin    N/A    N/A
```

**Columns:**
1. Date (YYYY-MM-DD)
2. Job Number
3. Job Task No (code)
4. Description
5. Hours
6. Category (Project, Admin, PTO, Holiday)
7. Customer Name
8. Job Description

### Routes

```python
GET  /bulk-import                     # Bulk import page
POST /api/bulk-import/process         # Process CSV file
```

### Validation Rules

- Date must be valid format
- Hours must be numeric
- Category must be valid
- Job number required for projects
- Task code required for projects
- All required fields present

---

## Configuration Management {#configuration}

### Overview
Centralized configuration for job task codes, admin codes, and company holidays.

### Job Task Codes

**Purpose:** Define tasks that can be billed to projects

**Examples:**
- 100: Engineering
- 200: Design
- 300: Testing
- 400: Project Management

**Operations:**
- View all task codes
- Add new task code
- Edit task code name
- Delete task code

### Admin Codes

**Purpose:** Define administrative/overhead categories

**Examples:**
- 001: General Admin
- 002: Meetings
- 003: Training
- 004: Vacation

**Operations:**
- View all admin codes
- Add new admin code
- Edit admin code name
- Delete admin code

### Company Holidays

**Purpose:** Define company holidays for the year

**Fields:**
- Holiday Date
- Holiday Name
- Description (optional)

**Features:**
- Add holidays
- Edit holiday details
- Delete holidays
- Used in upcoming holidays display
- Holiday category in time entries

### Routes

```python
GET    /config                        # Configuration page
GET    /api/config/job-task-codes     # Get all job task codes
POST   /api/config/job-task-codes     # Create job task code
PUT    /api/config/job-task-codes/<code>   # Update task code
DELETE /api/config/job-task-codes/<code>   # Delete task code

GET    /api/config/admin-codes        # Get all admin codes
GET    /api/config/admin-job-codes    # Get admin job codes
POST   /api/config/admin-job-codes    # Create admin code
PUT    /api/config/admin-job-codes/<id>    # Update admin code
DELETE /api/config/admin-job-codes/<id>    # Delete admin code

GET    /api/config/holidays           # Get all holidays
POST   /api/config/holidays           # Create holiday
PUT    /api/config/holidays/<id>      # Update holiday
DELETE /api/config/holidays/<id>      # Delete holiday
```

---

## Employment Information {#employment}

### Overview
Track employee hire dates and PTO allocations for anniversary-based PTO management.

### Features

**User Registration:**
- Optional hire date field
- Optional total PTO time field
- Both can be left blank

**Admin Management:**
- View hire dates for all users
- View PTO allocations for all users
- Edit employment info via modal
- Clear employment fields

**PTO Tracking:**
- Anniversary-based PTO years
- Automatic calculation of remaining PTO
- Reset date display
- Days until reset countdown

### Fields

**hire_date** (DATE)
- When user was hired
- Determines PTO year boundaries
- Optional field

**pto_time** (DECIMAL)
- Total PTO hours allocated annually
- Example: 80.0 hours
- Optional field

### PTO Calculations

**PTO Year:**
```
Start: Most recent hire date anniversary
End: Next hire date anniversary
```

**PTO Remaining:**
```
Remaining = Total Allocated - PTO Used This Year
```

**Color Coding:**
- Green: > 25% remaining
- Yellow: < 25% remaining
- Red: Negative (over-used)

### Routes

```python
POST /register                        # Register with optional employment fields
GET  /api/admin/get-users             # Returns hire_date and pto_time
POST /api/admin/update-user-employment  # Update employment info
```

---

# Part 3: Admin Features

## Admin Panel {#admin-panel}

### Overview
Central hub for administrative functions, accessible only to users with admin role.

### Admin Panel Home

**Navigation Cards:**
Each admin function has a uniquely colored card:

1. **User Management** (Blue)
   - Manage accounts, passwords, hire dates, PTO

2. **Manage User Data** (Red)
   - Edit any user's time entries

3. **Server Config** (Green)
   - Timezone, NTP, network settings

4. **Code Editor** (Yellow/Orange)
   - Edit application files in-browser

5. **System Reports** (Purple)
   - Project hours & team utilization

6. **System Backup** (Teal)
   - Create/download/restore backups

7. **My Dashboard** (Cyan)
   - Return to personal dashboard

### Routes

```python
GET /admin                            # Admin panel home
```

---

## User Management {#user-management}

### Overview
Complete user account management including creation, modification, and deletion.

### Features

**View Users:**
- List all user accounts
- Show username, full name, role, active status
- Display hire date and PTO time
- Show last login date

**Edit Employment:**
- Update hire date
- Update PTO time allocation
- Clear employment fields
- Color-coded display

**Change Password:**
- Admin can change any user's password
- No need for old password
- Minimum 8 characters

**Activate/Deactivate:**
- Toggle user active status
- Deactivated users cannot login
- Cannot deactivate own account

**Delete User:**
- Permanently delete user account
- Deletes all associated time entries
- Warning prompt before deletion

### User Table Columns

- Username
- Full Name
- Role (Admin/User badge)
- Active Status (Active/Inactive badge)
- Hire Date (formatted or "Not set")
- PTO Time (with hours unit or "Not set")
- Last Login
- Actions (vertical button group)

### Routes

```python
GET    /admin/user-management         # User management page
GET    /api/admin/get-users            # Get all users with employment info
POST   /api/admin/change-user-password  # Change user password
POST   /api/admin/toggle-user-active    # Activate/deactivate user
DELETE /api/admin/delete-user           # Delete user account
POST   /api/admin/update-user-employment  # Update hire date & PTO
```

---

## Manage User Data {#manage-user-data}

### Overview
Edit, add, or delete time entries for any user. Useful for corrections and admin adjustments.

### Features

**Select User:**
- Dropdown of all users
- Load user's projects and time entries

**View Time Entries:**
- Table of all time entries for selected user
- Filterable by date range
- Shows all entry details

**Edit Entry:**
- Modify any field (date, hours, description, etc.)
- Inline editing
- Validation applied

**Delete Entry:**
- Remove time entry
- Confirmation prompt

**Add Entry:**
- Create time entry for any user
- All fields available
- Same validation as normal time entry

### Use Cases

- Fix data entry errors
- Adjust PTO/holiday entries
- Add missing time for users
- Administrative corrections
- Historical data cleanup

### Routes

```python
GET    /admin/manage-user-data        # Manage user data page
GET    /api/admin/user-projects/<user_id>  # Get user's projects
GET    /api/admin/user-time-entries/<user_id>  # Get user's time entries
PUT    /api/admin/update-time-entry/<entry_id>  # Update time entry
DELETE /api/admin/delete-time-entry/<entry_id>  # Delete time entry
POST   /api/admin/add-time-entry       # Add time entry for user
```

---

## Server Configuration {#server-config}

### Overview
System-level configuration including timezone, NTP servers, and network settings.

### Features

**Timezone Configuration:**
- View current timezone
- Select new timezone from list
- Apply immediately via timedatectl

**NTP Server Configuration:**
- View current NTP servers
- Set primary and secondary NTP servers
- Sync time immediately
- Uses chrony or systemd-timesyncd

**Server Information:**
- Hostname
- IP address
- Operating system
- Uptime
- Current date/time

**Network Configuration:**
- View current network settings
- Configure static IP or DHCP
- Set DNS servers
- Apply netplan configuration

### Routes

```python
GET  /admin/server-config              # Server configuration page
GET  /api/admin/get-timezone           # Get current timezone
POST /api/admin/set-timezone           # Set timezone
POST /api/admin/set-ntp-servers        # Configure NTP servers
POST /api/admin/sync-ntp               # Sync time now
GET  /api/admin/get-server-info        # Get server details
GET  /api/admin/get-network-config     # Get network configuration
POST /api/admin/set-network-config     # Set network configuration
```

### Timezone Selection

Supports standard timezone identifiers:
- America/New_York
- America/Chicago
- America/Denver
- America/Los_Angeles
- Europe/London
- Asia/Tokyo
- etc.

---

## Code Editor {#code-editor}

### Overview
In-browser code editor for editing application templates and files.

### Features

**File Browser:**
- List all template files
- Show file sizes and modification dates
- Navigate folder structure

**Code Editor:**
- Syntax-highlighted editor
- Edit HTML templates
- Edit Python files (with caution)
- Edit CSS files

**Save Changes:**
- Save edited files back to disk
- Automatic backup before save
- Validation warnings

**Restore from Backup:**
- List available backup files
- Restore previous versions
- Timestamp-based backups

### Supported File Types

- `.html` - Jinja2 templates
- `.py` - Python application files
- `.css` - Stylesheets
- `.js` - JavaScript files
- `.md` - Markdown documentation

### Safety Features

- Creates backup before overwrite
- Warns about editing critical files
- Requires admin role
- Logs all file modifications

### Routes

```python
GET  /admin/code-editor                # Code editor page
POST /api/admin/read-file              # Read file contents
POST /api/admin/save-file              # Save file with backup
GET  /api/admin/list-templates         # List template files
GET  /api/admin/list-backups           # List backup files
POST /api/admin/restore-backup         # Restore from backup
```

---

## System Reports {#system-reports}

### Overview
Generate comprehensive reports on project hours and team utilization.

### Reports

**Project Hours Summary:**
- Total hours per project (Year-to-Date)
- Customer name
- Budget hours vs actual hours
- % budget used
- Hours remaining

**User Utilization Summary:**
- Hours worked per user (for date range)
- Project hours
- Admin hours
- PTO hours
- Total utilization %

**Date Range Filtering:**
- Default: Year-to-date
- Custom: Select any date range
- Real-time calculation

### Metrics

**Project Metrics:**
- Total budget hours across all projects
- Total hours used
- Total hours remaining
- Average % budget used

**Team Metrics:**
- Total hours worked
- Average hours per user
- Project vs admin split
- PTO usage

### Routes

```python
GET /admin/reports                     # Reports page
GET /api/reports/summary               # Get summary report data
```

---

## System Backup {#system-backup}

### Overview
Create, download, and restore full system backups including database and application files.

### Backup Contents

Each full backup (`timetracker_backup_YYYYMMDD_HHMMSS.tar.gz`) contains:

1. **database.sql** - Complete PostgreSQL dump
2. **timetracker_files.tar.gz** - All application files
3. **restore.sh** - One-command restoration script

### Excluded from Backup

- `venv/` - Python virtual environment
- `__pycache__/` - Python compiled files
- `backups/` - Existing backups
- `.git/` - Git repository
- `*.pyc` - Compiled Python files
- Test files

### Features

**Create Backup:**
- One-click full backup creation
- Stored in `/opt/timetracker/backups/full/`
- Timestamped filename
- Progress indication

**List Backups:**
- View all available backups
- Show size and date created
- Sort by date (newest first)

**Download Backup:**
- Download backup archive to local machine
- Direct browser download
- Preserve filename

**Delete Backup:**
- Remove old backup files
- Free up disk space
- Confirmation prompt

**Restore (Manual):**
- Extract backup on new server
- Run included `restore.sh` script
- Automatically installs dependencies and restores data

### Routes

```python
GET    /admin/system-backup            # Backup management page
POST   /api/admin/create-full-backup   # Create new backup
GET    /api/admin/list-full-backups    # List all backups
GET    /api/admin/download-backup/<filename>  # Download backup
DELETE /api/admin/delete-backup/<filename>    # Delete backup
```

### Backup Storage

Location: `/opt/timetracker/backups/full/`

Format: `timetracker_backup_YYYYMMDD_HHMMSS.tar.gz`

Example: `timetracker_backup_20270225_143022.tar.gz`

---

## Team Dashboard {#team-dashboard}

### Overview
Admin-only view of team-wide metrics and utilization across all users.

### Features

**Team Metrics:**
- Total hours logged by all users
- Total project hours
- Total admin hours
- Total PTO hours
- Team-wide utilization %

**User Breakdown:**
- Hours per user
- Individual utilization rates
- Project vs admin split
- Top performers

**Date Range Filtering:**
- Select custom date ranges
- View historical trends
- Compare periods

### Routes

```python
GET /admin/team-dashboard              # Team dashboard page
GET /api/admin/team-metrics            # Get team-wide metrics
```

---

# Part 4: Technical Reference

## Complete API Reference {#api-reference}

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/login` | User login | No |
| GET | `/logout` | User logout | Yes |
| POST | `/register` | User registration | No |

### Dashboard Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/dashboard` | Dashboard page | User |
| GET | `/api/dashboard/metrics` | Get metrics for date range | User |
| GET | `/api/dashboard/utilization-history` | Historical utilization data | User |
| GET | `/api/dashboard/upcoming-holidays` | Next 3 holidays | User |

### Time Entry Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/time-entry` | Time entry page | User |
| GET | `/api/time-entries` | Get time entries | User |
| POST | `/api/time-entries` | Create time entry | User |
| PUT | `/api/time-entries/<id>` | Update time entry | User |
| DELETE | `/api/time-entries/<id>` | Delete time entry | User |

### Project Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/projects` | Projects page | User |
| GET | `/api/projects` | Get projects | User |
| POST | `/api/projects` | Create project | User |
| PUT | `/api/projects/<id>` | Update project | User |
| DELETE | `/api/projects/<id>` | Delete project | User |
| GET | `/api/projects/lookup/<job_number>` | Lookup project | User |
| GET | `/api/projects/with-usage` | Projects with usage stats | User |

### Bulk Import Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/bulk-import` | Bulk import page | User |
| POST | `/api/bulk-import/process` | Process CSV file | User |

### Configuration Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/config` | Configuration page | User |
| GET | `/api/config/job-task-codes` | Get job task codes | User |
| POST | `/api/config/job-task-codes` | Create task code | User |
| PUT | `/api/config/job-task-codes/<code>` | Update task code | User |
| DELETE | `/api/config/job-task-codes/<code>` | Delete task code | User |
| GET | `/api/config/admin-codes` | Get admin codes | User |
| POST | `/api/config/admin-job-codes` | Create admin code | User |
| PUT | `/api/config/admin-job-codes/<id>` | Update admin code | User |
| DELETE | `/api/config/admin-job-codes/<id>` | Delete admin code | User |
| GET | `/api/config/holidays` | Get holidays | User |
| POST | `/api/config/holidays` | Create holiday | User |
| PUT | `/api/config/holidays/<id>` | Update holiday | User |
| DELETE | `/api/config/holidays/<id>` | Delete holiday | User |

### Admin - User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/user-management` | User management page | Admin |
| GET | `/api/admin/get-users` | Get all users | Admin |
| POST | `/api/admin/change-user-password` | Change user password | Admin |
| POST | `/api/admin/toggle-user-active` | Toggle user active | Admin |
| DELETE | `/api/admin/delete-user` | Delete user | Admin |
| POST | `/api/admin/update-user-employment` | Update hire date/PTO | Admin |

### Admin - Manage User Data

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/manage-user-data` | Manage user data page | Admin |
| GET | `/api/admin/user-projects/<user_id>` | Get user projects | Admin |
| GET | `/api/admin/user-time-entries/<user_id>` | Get user entries | Admin |
| PUT | `/api/admin/update-time-entry/<id>` | Update entry | Admin |
| DELETE | `/api/admin/delete-time-entry/<id>` | Delete entry | Admin |
| POST | `/api/admin/add-time-entry` | Add entry for user | Admin |

### Admin - Server Configuration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/server-config` | Server config page | Admin |
| GET | `/api/admin/get-timezone` | Get timezone | Admin |
| POST | `/api/admin/set-timezone` | Set timezone | Admin |
| POST | `/api/admin/set-ntp-servers` | Set NTP servers | Admin |
| POST | `/api/admin/sync-ntp` | Sync time now | Admin |
| GET | `/api/admin/get-server-info` | Get server info | Admin |
| GET | `/api/admin/get-network-config` | Get network config | Admin |
| POST | `/api/admin/set-network-config` | Set network config | Admin |

### Admin - Code Editor

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/code-editor` | Code editor page | Admin |
| POST | `/api/admin/read-file` | Read file | Admin |
| POST | `/api/admin/save-file` | Save file | Admin |
| GET | `/api/admin/list-templates` | List templates | Admin |
| GET | `/api/admin/list-backups` | List backups | Admin |
| POST | `/api/admin/restore-backup` | Restore backup | Admin |

### Admin - System Reports

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/reports` | Reports page | Admin |
| GET | `/api/reports/summary` | Get summary report | Admin |

### Admin - System Backup

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/system-backup` | Backup page | Admin |
| POST | `/api/admin/create-full-backup` | Create backup | Admin |
| GET | `/api/admin/list-full-backups` | List backups | Admin |
| GET | `/api/admin/download-backup/<filename>` | Download backup | Admin |
| DELETE | `/api/admin/delete-backup/<filename>` | Delete backup | Admin |

### Admin - Team Dashboard

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/team-dashboard` | Team dashboard page | Admin |
| GET | `/api/admin/team-metrics` | Team metrics | Admin |

### Export

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/export/csv` | Export CSV | User |

### Password Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user/change-password-page` | Change password page | User |
| POST | `/api/user/change-password` | Change own password | User |

**Total API Endpoints:** 79

---

## Database Schema {#database-schema}

### Tables

#### 1. users

Stores user account information and employment data.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',  -- 'user' or 'admin'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    hire_date DATE,  -- Optional: Employee hire date
    pto_time DECIMAL(10,2)  -- Optional: Total PTO hours allocated
);
```

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `username`
- UNIQUE on `email`

#### 2. time_entries

Stores all time entry records.

```sql
CREATE TABLE time_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    job_number VARCHAR(50),
    job_task_code VARCHAR(20),
    description TEXT,
    hours DECIMAL(5,2) NOT NULL,
    category VARCHAR(20) NOT NULL,  -- 'Project', 'Admin', 'PTO', 'Holiday'
    customer_name VARCHAR(200),
    job_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `entry_date`
- INDEX on `category`
- INDEX on `job_number`

#### 3. project_budgets

Stores project budget information.

```sql
CREATE TABLE project_budgets (
    id SERIAL PRIMARY KEY,
    job_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    project_description TEXT,
    budget_hours DECIMAL(8,2) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'Active',  -- 'Active' or 'Closed'
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `job_number`
- INDEX on `status`
- INDEX on `user_id`

#### 4. job_task_codes

Stores job task code definitions.

```sql
CREATE TABLE job_task_codes (
    task_code VARCHAR(20) PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `task_code`

#### 5. admin_job_codes

Stores admin code definitions.

```sql
CREATE TABLE admin_job_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `code`

#### 6. company_holidays

Stores company holiday calendar.

```sql
CREATE TABLE company_holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `holiday_date`

### Views

#### time_entries_with_details

Joins time_entries with related tables for detailed reporting.

```sql
CREATE OR REPLACE VIEW time_entries_with_details AS
SELECT
    te.id,
    te.user_id,
    te.entry_date,
    te.job_number,
    te.job_task_code,
    te.description,
    te.hours,
    te.category,
    te.customer_name,
    te.job_description,
    te.created_at,
    te.updated_at,
    jtc.task_name,
    u.username,
    u.full_name
FROM time_entries te
LEFT JOIN job_task_codes jtc ON te.job_task_code = jtc.task_code
LEFT JOIN users u ON te.user_id = u.id;
```

### Relationships

```
users (1) ─────< (many) time_entries
users (1) ─────< (many) project_budgets

time_entries (many) >───── (1) job_task_codes
                           (via job_task_code)

project_budgets (1) ─────< (many) time_entries
                           (via job_number)
```

---

## UI Templates {#ui-templates}

### Template Files

All templates extend `base.html` which provides:
- Navigation bar
- Bootstrap 5 layout
- Common CSS/JS includes
- User session info
- Responsive design

### Template List

1. **base.html** - Base template with navigation
2. **login.html** - Login & registration modal
3. **dashboard.html** - Main dashboard with metrics & charts
4. **time_entry.html** - Time entry form and list
5. **projects.html** - Project management
6. **bulk_import.html** - CSV bulk import
7. **config.html** - Configuration (codes & holidays)
8. **admin.html** - Admin panel home (colored cards)
9. **user_management.html** - User account management
10. **manage_user_data.html** - Edit user time entries
11. **server-config.html** - Server configuration
12. **code_editor.html** - In-browser code editor
13. **reports.html** - System reports
14. **system_backup.html** - Backup management
15. **team_dashboard.html** - Team metrics (admin)
16. **change_password.html** - Password change form

### Navigation Structure

**User Navigation:**
- Dashboard
- Time Entry
- Projects
- Bulk Import
- Configuration
- Change Password
- Logout

**Admin Navigation:**
- Dashboard
- Time Entry
- Projects
- Bulk Import
- Configuration
- **Admin** (dropdown)
  - User Management
  - Manage User Data
  - Server Config
  - Code Editor
  - System Reports
  - System Backup
  - Team Dashboard
- Change Password
- Logout

---

## Configuration Files {#config-files}

### Environment Variables (.env)

Location: `/opt/timetracker/.env`

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Database Configuration
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=your-db-password
DB_PORT=5432

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=5000
```

### Systemd Service

Location: `/etc/systemd/system/timetracker.service`

```ini
[Unit]
Description=Savant Time Tracker Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=timetracker
Group=timetracker
WorkingDirectory=/opt/timetracker
Environment="PATH=/opt/timetracker/venv/bin"
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

Location: `/etc/nginx/sites-available/timetracker`

```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/timetracker/static;
        expires 30d;
    }
}
```

### Cron Job (Daily Backup)

```cron
# Daily database backup at 2 AM
0 2 * * * /opt/timetracker/backup.sh >> /opt/timetracker/backup.log 2>&1
```

---

# Part 5: Installation & Deployment

## Installation Guide {#installation}

### Prerequisites

- Ubuntu 20.04 LTS or later
- 2GB RAM minimum (4GB recommended)
- 10GB free disk space
- Root/sudo access
- Internet connection

### Quick Installation

```bash
# 1. Clone or copy application files to server
cd /opt/timetracker

# 2. Run automated installation script
sudo ./install.sh

# 3. Access application
# Open browser to http://your-server-ip
```

### Manual Installation Steps

**1. Install Dependencies**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib
```

**2. Create Application User**
```bash
sudo adduser --system --group --home /opt/timetracker timetracker
```

**3. Setup PostgreSQL**
```bash
sudo -u postgres psql
CREATE DATABASE timetracker;
CREATE USER timetracker WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;
\q
```

**4. Install Application**
```bash
cd /opt/timetracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**5. Configure Environment**
```bash
cat > .env << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=production
DB_HOST=localhost
DB_NAME=timetracker
DB_USER=timetracker
DB_PASSWORD=your-password
DB_PORT=5432
EOF
```

**6. Load Database Schema**
```bash
# Schema is created automatically by application on first run
# Or load from SQL file if provided
```

**7. Configure Systemd**
```bash
sudo cp timetracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable timetracker
sudo systemctl start timetracker
```

**8. Configure Nginx**
```bash
sudo cp timetracker.nginx /etc/nginx/sites-available/timetracker
sudo ln -s /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**9. Setup Firewall**
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**10. Create First User**
```bash
# Open browser to http://your-server-ip
# Click "Create Account"
# Register first user (becomes admin)
```

---

## Configuration Options {#configuration-options}

### Application Settings

**Workers (Gunicorn):**
```bash
# Edit /etc/systemd/system/timetracker.service
ExecStart=/opt/timetracker/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
# Recommended: 2-4 workers for small installations
```

**Database Connection Pooling:**
```python
# In app.py, connections are created per request
# No persistent connection pool by default
```

**Session Timeout:**
```python
# Flask default: Session lasts until browser closes
# To set timeout, add to app.py:
app.permanent_session_lifetime = timedelta(hours=8)
```

### PostgreSQL Tuning

For 4GB RAM server:
```ini
# /etc/postgresql/*/main/postgresql.conf
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 32MB
```

### Backup Schedule

Default: Daily at 2 AM

To change:
```bash
sudo crontab -e -u timetracker
# Modify: 0 2 * * * /opt/timetracker/backup.sh
```

---

## Security {#security}

### Built-in Security Features

✅ **Password Hashing**
- Werkzeug's generate_password_hash
- PBKDF2-SHA256 with salt

✅ **SQL Injection Prevention**
- Parameterized queries throughout
- psycopg2 handles escaping

✅ **Role-Based Access Control**
- User vs Admin roles
- Decorators enforce permissions

✅ **Session Security**
- Flask secure sessions
- HTTP-only cookies

✅ **Input Validation**
- Server-side validation
- Type checking on all inputs

### Recommended Security Enhancements

**1. Enable HTTPS**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**2. Strong Database Password**
```bash
# Use 20+ character random password
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

**3. Restrict Database Access**
```ini
# /etc/postgresql/*/main/pg_hba.conf
local   timetracker  timetracker  md5
host    timetracker  timetracker  127.0.0.1/32  md5
```

**4. Firewall Rules**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**5. Regular Updates**
```bash
sudo apt update && sudo apt upgrade -y
```

---

## Backup & Restore {#backup-restore}

### Automated Daily Backups

Location: `/opt/timetracker/backups/`
Schedule: Daily at 2 AM
Retention: 30 days
Format: `db_backup_YYYYMMDD_HHMMSS.sql.gz`

### Manual Database Backup

```bash
sudo -u timetracker /opt/timetracker/backup.sh
```

### Full System Backup (via Admin UI)

1. Log in as admin
2. Go to **Admin → System Backup**
3. Click **Create Full Backup**
4. Download the `.tar.gz` file

Backup contains:
- Complete database dump
- All application files
- Automated restore script

### Restore from Full Backup

On a NEW Ubuntu server:

```bash
# 1. Copy backup to new server
scp timetracker_backup_*.tar.gz user@new-server:~

# 2. Extract backup
tar -xzf timetracker_backup_*.tar.gz

# 3. Run restore script
sudo bash restore.sh
```

The restore script will:
- Install all dependencies
- Create database and user
- Restore database
- Install application files
- Configure systemd and nginx
- Start services

### Restore Database Only

```bash
# Stop application
sudo systemctl stop timetracker

# Drop existing database
sudo -u postgres psql -c "DROP DATABASE timetracker;"
sudo -u postgres psql -c "CREATE DATABASE timetracker;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker;"

# Restore from backup
gunzip -c /opt/timetracker/backups/db_backup_*.sql.gz | \
  sudo -u timetracker psql -U timetracker timetracker

# Start application
sudo systemctl start timetracker
```

---

## Troubleshooting {#troubleshooting}

### Application Won't Start

**Check logs:**
```bash
sudo journalctl -u timetracker -n 50 --no-pager
```

**Common issues:**
- Database connection error → Check `.env` file
- Port already in use → Check if another process using port 5000
- Python errors → Check dependencies installed

**Solutions:**
```bash
# Restart service
sudo systemctl restart timetracker

# Check status
sudo systemctl status timetracker

# View full logs
sudo journalctl -u timetracker -f
```

### Can't Access Web Interface

**Check Nginx:**
```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

**Check firewall:**
```bash
sudo ufw status
```

**Test locally:**
```bash
curl http://localhost
```

### Database Connection Errors

**Check PostgreSQL:**
```bash
sudo systemctl status postgresql
```

**Test connection:**
```bash
sudo -u timetracker psql -U timetracker -d timetracker -c "SELECT 1;"
```

**Reset password:**
```bash
sudo -u postgres psql
ALTER USER timetracker WITH PASSWORD 'new_password';
\q

# Update .env file with new password
sudo nano /opt/timetracker/.env
```

### PTO Information Not Showing

**Check database columns:**
```bash
sudo -u postgres psql -d timetracker -c "\d users"
```

**Verify hire_date and pto_time columns exist.**

If not:
```bash
sudo -u postgres psql -d timetracker -f /tmp/add_hire_date_pto_fields.sql
```

### Backup Creation Fails

**Check disk space:**
```bash
df -h
```

**Check permissions:**
```bash
ls -la /opt/timetracker/backups/
```

**Manual backup:**
```bash
sudo -u timetracker pg_dump -U timetracker timetracker > /tmp/manual_backup.sql
```

### High CPU/Memory Usage

**Check worker count:**
```bash
ps aux | grep gunicorn
```

**Reduce workers if needed:**
```bash
# Edit /etc/systemd/system/timetracker.service
# Change --workers 4 to --workers 2
sudo systemctl daemon-reload
sudo systemctl restart timetracker
```

### Slow Performance

**Check PostgreSQL:**
```bash
# Analyze tables
sudo -u timetracker psql -U timetracker timetracker -c "VACUUM ANALYZE;"
```

**Check indexes:**
```bash
sudo -u timetracker psql -U timetracker timetracker -c "\di"
```

**Review query performance:**
```bash
# Enable query logging in PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf
# Set: log_min_duration_statement = 1000  # Log queries > 1 second
```

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Service Management
sudo systemctl start timetracker
sudo systemctl stop timetracker
sudo systemctl restart timetracker
sudo systemctl status timetracker

# View Logs
sudo journalctl -u timetracker -f
sudo journalctl -u timetracker -n 100

# Database Access
sudo -u timetracker psql -U timetracker timetracker

# Backup
sudo -u timetracker /opt/timetracker/backup.sh

# Nginx
sudo systemctl restart nginx
sudo nginx -t
```

### Important Paths

- **Application:** `/opt/timetracker/app.py`
- **Config:** `/opt/timetracker/.env`
- **Templates:** `/opt/timetracker/templates/`
- **Backups:** `/opt/timetracker/backups/`
- **Full Backups:** `/opt/timetracker/backups/full/`
- **Logs:** `sudo journalctl -u timetracker`
- **Nginx Config:** `/etc/nginx/sites-available/timetracker`
- **Systemd Service:** `/etc/systemd/system/timetracker.service`

### Default Credentials

- **Database:** timetracker / (set during install)
- **First User:** Created via web interface
- **Admin Role:** Assigned via User Management

---

## Document Information

**Document Title:** Savant Time Tracker - Complete System Documentation
**Version:** 1.0
**Date:** 2026-02-26
**Total Sections:** 28
**Total Endpoints:** 79
**Total Templates:** 16
**Total Tables:** 6

**Purpose:**
This document provides comprehensive documentation of every feature, configuration option, API endpoint, database table, and setting in the Savant Time Tracker application. It is suitable for:
- System administrators
- Developers
- AI training and reference
- User support
- System audits
- Onboarding and training

**Completeness:**
This documentation covers 100% of the application's features and functionality as of February 2026, including:
- All 79 API endpoints
- All 16 UI templates
- Complete database schema
- All configuration options
- Installation and deployment
- Security and backup procedures
- Troubleshooting guides

**Maintenance:**
This document should be updated when:
- New features are added
- API endpoints change
- Database schema is modified
- Configuration options are added
- Security procedures change

---

**End of Documentation**
