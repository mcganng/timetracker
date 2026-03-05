"""
Savant Time Tracker - Flask Application
Complete version with Admin and Bulk Import features
Fixed for Savant tab-separated format
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, date
import os
from functools import wraps
import json
import csv
import io
import re
import shlex
import subprocess

# Try to import admin helper client (optional - for privileged operations)
try:
    from admin_helper_client import AdminHelperClient
    ADMIN_HELPER_AVAILABLE = True
except ImportError:
    ADMIN_HELPER_AVAILABLE = False
    AdminHelperClient = None

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'timetracker'),
    'user': os.environ.get('DB_USER', 'timetracker'),
    'password': os.environ.get('DB_PASSWORD', 'timetracker'),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT role FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ========================================
# Authentication Routes
# ========================================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    
    if user and check_password_hash(user['password_hash'], password):
        # Check if user is active
        if not user.get('is_active', True):  # Default to True if column doesn't exist yet
            cur.close()
            conn.close()
            return jsonify({'error': 'Account has been deactivated. Contact administrator.'}), 403
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user.get('role', 'user')
        
        # Update last login
        cur.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user['id'],))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'user': {'username': user['username'], 'full_name': user['full_name']}})
    
    cur.close()
    conn.close()
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    """User registration"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    # Optional fields
    hire_date = data.get('hire_date')  # Optional: Date of hire
    pto_time = data.get('pto_time')    # Optional: Total PTO time in hours

    if not all([username, email, password, full_name]):
        return jsonify({'error': 'All fields required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        password_hash = generate_password_hash(password)

        # Build dynamic SQL to handle optional fields
        if hire_date and pto_time:
            cur.execute(
                'INSERT INTO users (username, email, password_hash, full_name, role, hire_date, pto_time) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (username, email, password_hash, full_name, 'user', hire_date, pto_time)
            )
        elif hire_date:
            cur.execute(
                'INSERT INTO users (username, email, password_hash, full_name, role, hire_date) VALUES (%s, %s, %s, %s, %s, %s)',
                (username, email, password_hash, full_name, 'user', hire_date)
            )
        elif pto_time:
            cur.execute(
                'INSERT INTO users (username, email, password_hash, full_name, role, pto_time) VALUES (%s, %s, %s, %s, %s, %s)',
                (username, email, password_hash, full_name, 'user', pto_time)
            )
        else:
            cur.execute(
                'INSERT INTO users (username, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, %s)',
                (username, email, password_hash, full_name, 'user')
            )

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400

# ========================================
# Dashboard Routes
# ========================================

@app.route('/api/dashboard/utilization-history')
@login_required
def get_utilization_history():
    """Get weekly utilization history for the chart"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get weekly utilization for the past 12 weeks
    cur.execute('''
        WITH weekly_data AS (
            SELECT
                DATE_TRUNC('week', entry_date) AS week_start,
                SUM(CASE WHEN category = 'Project' THEN hours ELSE 0 END) as project_hours,
                SUM(CASE WHEN category = 'Admin' THEN hours ELSE 0 END) as admin_hours,
                SUM(hours) as total_hours
            FROM time_entries
            WHERE user_id = %s
                AND entry_date >= CURRENT_DATE - INTERVAL '12 weeks'
            GROUP BY DATE_TRUNC('week', entry_date)
            ORDER BY week_start
        )
        SELECT
            TO_CHAR(week_start, 'MM/DD') as week_label,
            project_hours,
            admin_hours,
            total_hours,
            CASE 
                WHEN total_hours > 0 
                THEN ROUND((project_hours / total_hours * 100)::numeric, 1)
                ELSE 0 
            END as project_util,
            CASE 
                WHEN total_hours > 0 
                THEN ROUND((admin_hours / total_hours * 100)::numeric, 1)
                ELSE 0 
            END as admin_util
        FROM weekly_data
    ''', (session['user_id'],))
    
    data = cur.fetchall()
    cur.close()
    conn.close()
    
    # Format for Chart.js
    result = {
        'labels': [row['week_label'] for row in data],
        'project_utilization': [float(row['project_util']) for row in data],
        'admin_utilization': [float(row['admin_util']) for row in data]
    }
    
    return jsonify(result)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', user=session)

@app.route('/api/dashboard/metrics')
@login_required
def dashboard_metrics():
    """Get dashboard metrics for date range"""
    start_date = request.args.get('start_date')
    end_date   = request.args.get('end_date')
    user_id    = session['user_id']

    conn = get_db_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get user's employment information for PTO calculations
    cur.execute('''
        SELECT hire_date, pto_time
        FROM users
        WHERE id = %s
    ''', (user_id,))

    user_info = cur.fetchone()
    hire_date = user_info['hire_date'] if user_info else None
    total_pto_allowed = float(user_info['pto_time']) if user_info and user_info['pto_time'] else None

    # Summary metrics
    cur.execute('''
        SELECT
            SUM(CASE WHEN category != 'Holiday' THEN hours ELSE 0 END) as total_hours,
            SUM(CASE WHEN category = 'Project'  THEN hours ELSE 0 END) as project_hours,
            SUM(CASE WHEN category = 'Admin'    THEN hours ELSE 0 END) as admin_hours,
            SUM(CASE WHEN category = 'PTO'      THEN hours ELSE 0 END) as pto_hours,
            SUM(CASE WHEN category = 'Holiday'  THEN hours ELSE 0 END) as holiday_hours
        FROM time_entries
        WHERE user_id = %s AND entry_date BETWEEN %s AND %s
    ''', (user_id, start_date, end_date))

    metrics = cur.fetchone()

    total_hours   = float(metrics['total_hours']   or 0)
    project_hours = float(metrics['project_hours'] or 0)
    admin_hours   = float(metrics['admin_hours']   or 0)
    pto_hours     = float(metrics['pto_hours']     or 0)
    holiday_hours = float(metrics['holiday_hours'] or 0)

    days             = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    weeks            = days / 7.0
    available_hours  = weeks * 40
    project_util     = (project_hours / available_hours * 100) if available_hours > 0 else 0
    admin_util       = (admin_hours   / available_hours * 100) if available_hours > 0 else 0

    # Calculate PTO information based on current PTO year (from hire date anniversary)
    pto_remaining = None
    pto_reset_date = None
    days_until_reset = None

    if hire_date and total_pto_allowed:
        # Calculate PTO taken in current PTO year (anniversary-based)
        today = datetime.now().date()
        current_year = today.year

        # Find the most recent hire date anniversary
        # This year's anniversary
        anniversary_this_year = hire_date.replace(year=current_year)

        # If we haven't reached this year's anniversary yet, use last year's
        if today < anniversary_this_year:
            pto_year_start = hire_date.replace(year=current_year - 1)
            pto_reset_date = anniversary_this_year
        else:
            pto_year_start = anniversary_this_year
            pto_reset_date = hire_date.replace(year=current_year + 1)

        # Calculate PTO taken since the start of current PTO year
        cur.execute('''
            SELECT COALESCE(SUM(hours), 0) as pto_used_this_year
            FROM time_entries
            WHERE user_id = %s
              AND category = 'PTO'
              AND entry_date >= %s
              AND entry_date < %s
        ''', (user_id, pto_year_start, pto_reset_date))

        pto_year_data = cur.fetchone()
        pto_used_this_year = float(pto_year_data['pto_used_this_year'] or 0)

        # Calculate remaining PTO
        pto_remaining = total_pto_allowed - pto_used_this_year

        # Calculate days until reset
        days_until_reset = (pto_reset_date - today).days

    # Project hours by task
    cur.execute('''
        SELECT job_task_code, task_name, SUM(hours) as hours
        FROM time_entries_with_details
        WHERE user_id = %s AND entry_date BETWEEN %s AND %s AND category = 'Project'
        GROUP BY job_task_code, task_name
        ORDER BY job_task_code
    ''', (user_id, start_date, end_date))
    project_hours_by_task = cur.fetchall()

    # Active projects - filtered by user (admins see all, users see only their own)
    if session.get('role') == 'admin':
        cur.execute('''
            SELECT
                pb.id,
                pb.job_number,
                pb.customer_name,
                pb.project_description,
                pb.budget_hours,
                pb.start_date,
                pb.end_date,
                COALESCE(SUM(te.hours), 0)                                           AS hours_used,
                pb.budget_hours - COALESCE(SUM(te.hours), 0)                        AS hours_remaining,
                CASE WHEN pb.budget_hours > 0
                     THEN ROUND((COALESCE(SUM(te.hours), 0) / pb.budget_hours * 100)::numeric, 1)
                     ELSE 0 END                                                       AS percent_used
            FROM project_budgets pb
            LEFT JOIN time_entries te ON pb.job_number = te.job_number
                AND te.entry_date BETWEEN %s AND %s
            WHERE pb.status = 'Active'
            GROUP BY pb.id, pb.job_number, pb.customer_name, pb.project_description,
                     pb.budget_hours, pb.start_date, pb.end_date
            ORDER BY pb.customer_name
        ''', (start_date, end_date))
    else:
        cur.execute('''
            SELECT
                pb.id,
                pb.job_number,
                pb.customer_name,
                pb.project_description,
                pb.budget_hours,
                pb.start_date,
                pb.end_date,
                COALESCE(SUM(te.hours), 0)                                           AS hours_used,
                pb.budget_hours - COALESCE(SUM(te.hours), 0)                        AS hours_remaining,
                CASE WHEN pb.budget_hours > 0
                     THEN ROUND((COALESCE(SUM(te.hours), 0) / pb.budget_hours * 100)::numeric, 1)
                     ELSE 0 END                                                       AS percent_used
            FROM project_budgets pb
            LEFT JOIN time_entries te ON pb.job_number = te.job_number
                AND te.entry_date BETWEEN %s AND %s
            WHERE pb.status = 'Active' AND pb.user_id = %s
            GROUP BY pb.id, pb.job_number, pb.customer_name, pb.project_description,
                     pb.budget_hours, pb.start_date, pb.end_date
            ORDER BY pb.customer_name
        ''', (start_date, end_date, user_id))

    active_projects = cur.fetchall()

    # Convert dates
    for proj in active_projects:
        proj['start_date'] = proj['start_date'].isoformat() if proj['start_date'] else None
        proj['end_date']   = proj['end_date'].isoformat()   if proj['end_date']   else None

    cur.close()
    conn.close()

    return jsonify({
        'metrics': {
            'total_hours':          total_hours,
            'project_hours':        project_hours,
            'admin_hours':          admin_hours,
            'pto_hours':            pto_hours,
            'holiday_hours':        holiday_hours,
            'weeks':                round(weeks, 2),
            'available_hours':      round(available_hours, 2),
            'project_utilization':  round(project_util, 1),
            'admin_utilization':    round(admin_util, 1),
            'total_pto_allowed':    total_pto_allowed,
            'pto_remaining':        round(pto_remaining, 1) if pto_remaining is not None else None,
            'pto_reset_date':       pto_reset_date.isoformat() if pto_reset_date else None,
            'days_until_reset':     days_until_reset,
            'hire_date':            hire_date.isoformat() if hire_date else None
        },
        'project_hours_by_task': project_hours_by_task,
        'active_projects':       active_projects
    })

@app.route('/api/dashboard/upcoming-holidays')
@login_required
def get_upcoming_holidays():
    """Get next 3 upcoming holidays"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute('''
        SELECT holiday_date, holiday_name, description
        FROM company_holidays
        WHERE holiday_date >= CURRENT_DATE
        ORDER BY holiday_date
        LIMIT 3
    ''')
    
    holidays = cur.fetchall()
    
    # Convert dates to strings
    for holiday in holidays:
        if holiday['holiday_date']:
            holiday['holiday_date'] = holiday['holiday_date'].isoformat()
    
    cur.close()
    conn.close()
    
    return jsonify(holidays)

# ========================================
# Time Entry Routes
# ========================================

@app.route('/time-entry')
@login_required
def time_entry_page():
    """Time entry page"""
    return render_template('time_entry.html', user=session)

@app.route('/api/time-entries', methods=['GET'])
@login_required
def get_time_entries():
    """Get time entries for a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('''
        SELECT * FROM time_entries_with_details
        WHERE user_id = %s AND entry_date BETWEEN %s AND %s
        ORDER BY entry_date DESC, id DESC
    ''', (user_id, start_date, end_date))
    
    entries = cur.fetchall()
    
    # Convert dates to strings
    for entry in entries:
        entry['entry_date'] = entry['entry_date'].isoformat() if entry['entry_date'] else None
        entry['created_at'] = entry['created_at'].isoformat() if entry['created_at'] else None
        entry['updated_at'] = entry['updated_at'].isoformat() if entry['updated_at'] else None
    
    cur.close()
    conn.close()
    
    return jsonify(entries)

@app.route('/api/time-entries', methods=['POST'])
@login_required
def create_time_entry():
    """Create a new time entry"""
    data = request.json
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO time_entries 
            (user_id, entry_date, job_number, job_task_code, job_type, description, 
             hours, category, customer_name, job_description, person_responsible)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id,
            data.get('entry_date'),
            data.get('job_number'),
            data.get('job_task_code'),
            data.get('job_type', 'Job'),
            data.get('description'),
            data.get('hours'),
            data.get('category'),
            data.get('customer_name'),
            data.get('job_description'),
            data.get('person_responsible')
        ))
        
        entry_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'id': entry_id})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/time-entries/<int:entry_id>', methods=['PUT'])
@login_required
def update_time_entry(entry_id):
    """Update a time entry"""
    data = request.json
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE time_entries
            SET entry_date = %s, job_number = %s, job_task_code = %s, job_type = %s,
                description = %s, hours = %s, category = %s, customer_name = %s,
                job_description = %s, person_responsible = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('entry_date'),
            data.get('job_number'),
            data.get('job_task_code'),
            data.get('job_type'),
            data.get('description'),
            data.get('hours'),
            data.get('category'),
            data.get('customer_name'),
            data.get('job_description'),
            data.get('person_responsible'),
            entry_id,
            user_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/time-entries/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_time_entry(entry_id):
    """Delete a time entry"""
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM time_entries WHERE id = %s AND user_id = %s', (entry_id, user_id))
    conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

# ========================================
# Bulk Import Routes (Like Excel Paste Area!)
# ========================================

@app.route('/bulk-import')
@login_required
def bulk_import_page():
    """Bulk import page - paste Savant data here"""
    return render_template('bulk_import.html', user=session)

@app.route('/api/bulk-import/process', methods=['POST'])
@login_required
def process_bulk_import():
    """Process pasted Savant data (tab-separated format)"""
    data = request.json
    pasted_text = data.get('pasted_text', '')
    monday_date = data.get('monday_date')
    
    if not pasted_text or not monday_date:
        return jsonify({'error': 'Missing pasted text or Monday date'}), 400
    
    try:
        lines = pasted_text.strip().split('\n')
        year, month, day = map(int, monday_date.split('-'))
        monday_date_obj = date(year, month, day)
        
        entries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split by tabs (Savant exports as tab-separated)
            parts = line.split('\t')
            
            if len(parts) < 11:
                continue  # Skip invalid lines
            
            # Parse Savant format:
            # Column 0: Type (Job/Absence)
            # Column 1: Job Number
            # Column 2: Task Code
            # Column 3: Short name
            # Columns 4-10: Hours for Mon-Sun
            
            job_type = parts[0].strip()
            job_number = parts[1].strip()
            
            # Extract task code
            try:
                job_task_code = int(parts[2].strip())
            except (ValueError, IndexError):
                continue
            
            # Columns are swapped in Savant export
            customer_name = parts[16].strip() if len(parts) > 16 and parts[16] else ''
            description = parts[17].strip() if len(parts) > 17 and parts[17] else ''

            # Filter out numeric values
            if customer_name and customer_name.isdigit():
                customer_name = ''
            
            # Determine category based on task code
            if job_task_code in [110, 120, 130, 140, 150, 160, 169, 170, 180, 190, 200]:
                category = 'Project'
            elif job_task_code in [410, 450]:
                category = 'Admin'
            elif job_task_code == 420:
                category = 'PTO'
                job_number = 'PTO'
            elif job_task_code == 440:
                category = 'Holiday'
                job_number = 'HOLIDAY'
            else:
                category = 'Project'
            
            # Auto-create missing task codes
            conn_check = get_db_connection()
            cur_check = conn_check.cursor()
            cur_check.execute('SELECT task_code FROM job_task_codes WHERE task_code = %s', (job_task_code,))
            if not cur_check.fetchone():
                cur_check.execute('''
                    INSERT INTO job_task_codes (task_code, task_name, category, description, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    ON CONFLICT (task_code) DO NOTHING
                ''', (job_task_code, f'Task {job_task_code}', category, f'Auto-created from import'))
                conn_check.commit()
            cur_check.close()
            conn_check.close()
            
            # Extract hours for each day (columns 4-10 are Sun-Sat in Savant format)
            # User provides Monday date, so subtract 1 day to get Sunday start
            day_offset = 0
            for i in range(4, 11):
                try:
                    if i < len(parts) and parts[i].strip():
                        hours = float(parts[i].strip())
                        if hours > 0:
                            entry_date = monday_date_obj + timedelta(days=day_offset)
                            
                            entries.append({
                                'entry_date': entry_date.strftime('%Y-%m-%d'),
                                'job_number': job_number,
                                'job_task_code': job_task_code,
                                'hours': hours,
                                'category': category,
                                'job_type': job_type,
                                'description': description,
                                'customer_name': customer_name
                            })
                except (ValueError, IndexError):
                    pass
                
                day_offset += 1
        
        # Insert entries into database
        conn = get_db_connection()
        cur = conn.cursor()
        user_id = session['user_id']
        
        inserted_count = 0
        for entry in entries:
            cur.execute('''
                INSERT INTO time_entries 
                (user_id, entry_date, job_number, job_task_code, job_type, 
                 hours, category, description, customer_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                entry['entry_date'],
                entry['job_number'],
                entry['job_task_code'],
                entry['job_type'],
                entry['hours'],
                entry['category'],
                entry['description'],
                entry['customer_name']
            ))
            inserted_count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'entries_imported': inserted_count,
            'message': f'Successfully imported {inserted_count} time entries'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========================================
# Project Budget Routes
# ========================================

@app.route('/projects')
@login_required
def projects_page():
    """Projects management page"""
    return render_template('projects.html', user=session)

@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    """Get projects - users see only their own, admins see all"""
    status = request.args.get('status', 'Active')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Admins see all projects, users see only their own
    if session.get('role') == 'admin':
        cur.execute('''
            SELECT pb.*, u.username as owner_name
            FROM project_budgets pb
            LEFT JOIN users u ON pb.user_id = u.id
            WHERE pb.status = %s
            ORDER BY pb.customer_name, pb.job_number
        ''', (status,))
    else:
        cur.execute('''
            SELECT pb.*, u.username as owner_name
            FROM project_budgets pb
            LEFT JOIN users u ON pb.user_id = u.id
            WHERE pb.status = %s AND pb.user_id = %s
            ORDER BY pb.customer_name, pb.job_number
        ''', (status, session.get('user_id')))
    
    projects = cur.fetchall()
    
    # Convert dates to strings
    for project in projects:
        project['start_date'] = project['start_date'].isoformat() if project['start_date'] else None
        project['end_date'] = project['end_date'].isoformat() if project['end_date'] else None
        project['created_at'] = project['created_at'].isoformat() if project['created_at'] else None
        project['updated_at'] = project['updated_at'].isoformat() if project['updated_at'] else None
    
    cur.close()
    conn.close()
    
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project - automatically assigned to current user"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO project_budgets 
            (job_number, customer_name, project_description, budget_hours, status, start_date, end_date, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data.get('job_number'),
            data.get('customer_name'),
            data.get('project_description'),
            data.get('budget_hours'),
            data.get('status', 'Active'),
            data.get('start_date'),
            data.get('end_date'),
            session.get('user_id')  # Automatically assign to current user
        ))
        
        project_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'id': project_id})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update a project - users can only update their own projects"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check ownership (admins can edit any, users only their own)
        if session.get('role') != 'admin':
            cur.execute('SELECT user_id FROM project_budgets WHERE id = %s', (project_id,))
            result = cur.fetchone()
            if not result or result[0] != session.get('user_id'):
                cur.close()
                conn.close()
                return jsonify({'error': 'Unauthorized - you can only edit your own projects'}), 403
        
        cur.execute('''
            UPDATE project_budgets
            SET customer_name = %s, project_description = %s, budget_hours = %s,
                status = %s, start_date = %s, end_date = %s
            WHERE id = %s
        ''', (
            data.get('customer_name'),
            data.get('project_description'),
            data.get('budget_hours'),
            data.get('status'),
            data.get('start_date'),
            data.get('end_date'),
            project_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/lookup/<job_number>', methods=['GET'])
@login_required
def lookup_project(job_number):
    """Look up project details by job number - users can only lookup their own projects"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Admins can lookup any project, users only their own
    if session.get('role') == 'admin':
        cur.execute('''
            SELECT job_number, customer_name, project_description
            FROM project_budgets
            WHERE LOWER(job_number) = LOWER(%s)
            LIMIT 1
        ''', (job_number,))
    else:
        cur.execute('''
            SELECT job_number, customer_name, project_description
            FROM project_budgets
            WHERE LOWER(job_number) = LOWER(%s) AND user_id = %s
            LIMIT 1
        ''', (job_number, session.get('user_id')))

    project = cur.fetchone()
    cur.close()
    conn.close()

    if project:
        return jsonify({
            'found': True,
            'job_number': project['job_number'],
            'customer_name': project['customer_name'],
            'project_description': project['project_description']
        })
    else:
        return jsonify({'found': False})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project - users can only delete their own projects"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check ownership (admins can delete any, users only their own)
        if session.get('role') != 'admin':
            cur.execute('SELECT user_id FROM project_budgets WHERE id = %s', (project_id,))
            result = cur.fetchone()
            if not result or result[0] != session.get('user_id'):
                cur.close()
                conn.close()
                return jsonify({'error': 'Unauthorized - you can only delete your own projects'}), 403
        
        cur.execute('DELETE FROM project_budgets WHERE id = %s', (project_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500    

@app.route('/api/projects/with-usage', methods=['GET'])
@login_required
def get_projects_with_usage():
    """Get projects with calculated hours used and remaining - filtered by user"""
    status = request.args.get('status', 'Active')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Admins see all projects, users see only their own
    if session.get('role') == 'admin':
        cur.execute('''
            SELECT 
                pb.id, pb.job_number, pb.customer_name, pb.project_description,
                pb.budget_hours, pb.status, pb.start_date, pb.end_date,
                pb.created_at, pb.updated_at,
                COALESCE(SUM(te.hours), 0) as hours_used,
                pb.budget_hours - COALESCE(SUM(te.hours), 0) as hours_remaining,
                CASE WHEN pb.budget_hours > 0 
                     THEN ROUND((COALESCE(SUM(te.hours), 0) / pb.budget_hours * 100)::numeric, 1)
                     ELSE 0 END as percent_used
            FROM project_budgets pb
            LEFT JOIN time_entries te ON LOWER(pb.job_number) = LOWER(te.job_number)
            WHERE pb.status = %s
            GROUP BY pb.id, pb.job_number, pb.customer_name, pb.project_description,
                     pb.budget_hours, pb.status, pb.start_date, pb.end_date,
                     pb.created_at, pb.updated_at
            ORDER BY pb.customer_name, pb.job_number
        ''', (status,))
    else:
        cur.execute('''
            SELECT 
                pb.id, pb.job_number, pb.customer_name, pb.project_description,
                pb.budget_hours, pb.status, pb.start_date, pb.end_date,
                pb.created_at, pb.updated_at,
                COALESCE(SUM(te.hours), 0) as hours_used,
                pb.budget_hours - COALESCE(SUM(te.hours), 0) as hours_remaining,
                CASE WHEN pb.budget_hours > 0 
                     THEN ROUND((COALESCE(SUM(te.hours), 0) / pb.budget_hours * 100)::numeric, 1)
                     ELSE 0 END as percent_used
            FROM project_budgets pb
            LEFT JOIN time_entries te ON LOWER(pb.job_number) = LOWER(te.job_number)
            WHERE pb.status = %s AND pb.user_id = %s
            GROUP BY pb.id, pb.job_number, pb.customer_name, pb.project_description,
                     pb.budget_hours, pb.status, pb.start_date, pb.end_date,
                     pb.created_at, pb.updated_at
            ORDER BY pb.customer_name, pb.job_number
        ''', (status, session.get('user_id')))
    
    projects = cur.fetchall()
    
    for project in projects:
        if project['start_date']:
            project['start_date'] = project['start_date'].isoformat()
        if project['end_date']:
            project['end_date'] = project['end_date'].isoformat()
        if project['created_at']:
            project['created_at'] = project['created_at'].isoformat()
        if project['updated_at']:
            project['updated_at'] = project['updated_at'].isoformat()
    
    cur.close()
    conn.close()
    return jsonify(projects)

# ========================================
# Configuration Routes
# ========================================

@app.route('/api/config/job-task-codes/<task_code>', methods=['PUT'])
@login_required
@admin_required
def update_job_task_code(task_code):
    """Update a job task code - task_code IS the primary key"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            UPDATE job_task_codes
            SET task_code = %s, task_name = %s, category = %s, description = %s
            WHERE task_code = %s
        ''', (
            data['task_code'],
            data['task_name'],
            data.get('category', 'Project'),
            data.get('description'),
            task_code          # <-- WHERE task_code = original value
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/job-task-codes/<task_code>', methods=['DELETE'])
@login_required
@admin_required
def delete_job_task_code(task_code):
    """Delete a job task code - task_code IS the primary key"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM job_task_codes WHERE task_code = %s', (task_code,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


# ─── ADMIN JOB CODES ────────────────────────────────────────────────────────

@app.route('/api/config/admin-job-codes', methods=['GET'])
@login_required
def get_admin_job_codes():
    """Get all admin job codes"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('SELECT * FROM admin_job_codes ORDER BY admin_code')
    codes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify(codes)

@app.route('/api/config/admin-job-codes', methods=['POST'])
@login_required
@admin_required
def add_admin_job_code():
    """Add a new admin job code"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO admin_job_codes (admin_code, description)
            VALUES (%s, %s)
        ''', (data['admin_code'], data['description']))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/admin-job-codes/<int:code_id>', methods=['PUT'])
@login_required
@admin_required
def update_admin_job_code(code_id):
    """Update an admin job code"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE admin_job_codes
            SET admin_code = %s, description = %s
            WHERE id = %s
        ''', (data['admin_code'], data['description'], code_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/admin-job-codes/<int:code_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_admin_job_code(code_id):
    """Delete an admin job code"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM admin_job_codes WHERE id = %s', (code_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


# ─── COMPANY HOLIDAYS ───────────────────────────────────────────────────────

@app.route('/api/config/holidays', methods=['POST'])
@login_required
@admin_required
def add_holiday():
    """Add a new company holiday"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO company_holidays (holiday_date, holiday_name, description)
            VALUES (%s::date, %s, %s)
        ''', (data['holiday_date'], data['holiday_name'], data.get('description')))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/holidays/<int:holiday_id>', methods=['PUT'])
@login_required
@admin_required
def update_holiday(holiday_id):
    """Update a company holiday"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE company_holidays
            SET holiday_date = %s::date, holiday_name = %s, description = %s
            WHERE id = %s
        ''', (data['holiday_date'], data['holiday_name'], data.get('description'), holiday_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/holidays/<int:holiday_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_holiday(holiday_id):
    """Delete a company holiday"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM company_holidays WHERE id = %s', (holiday_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/config')
@login_required
def config_page():
    """Configuration page"""
    return render_template('config.html', user=session)

@app.route('/api/config/job-task-codes', methods=['GET'])
@login_required
def get_job_task_codes():
    """Get all job task codes"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('SELECT * FROM job_task_codes ORDER BY task_code')
    codes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify(codes)

@app.route('/api/config/job-task-codes', methods=['POST'])
@login_required
@admin_required
def add_job_task_code():
    """Add a new job task code"""
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
        INSERT INTO job_task_codes (task_code, task_name, category, description)
        VALUES (%s, %s, %s, %s)
        ''', (data['task_code'], data['task_name'], data.get('category', 'Project'), data.get('description')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/admin-codes', methods=['GET'])
@login_required
def get_admin_codes():
    """Get all admin job codes"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('SELECT * FROM admin_job_codes ORDER BY admin_code')
    codes = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify(codes)

@app.route('/api/config/holidays', methods=['GET'])
@login_required
def get_holidays():
    """Get all holidays"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('SELECT * FROM company_holidays ORDER BY holiday_date DESC')
    holidays = cur.fetchall()
    
    for holiday in holidays:
        holiday['holiday_date'] = holiday['holiday_date'].isoformat()
    
    cur.close()
    conn.close()
    
    return jsonify(holidays)

# ========================================
# Admin Routes
# ========================================

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    """Admin panel page"""
    return render_template('admin.html', user=session)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Get all users (admin only)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('''
        SELECT id, username, email, full_name, role, created_at, last_login
        FROM users
        ORDER BY created_at
    ''')
    
    users = cur.fetchall()
    
    for user in users:
        user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
        user['last_login'] = user['last_login'].isoformat() if user['last_login'] else None
    
    cur.close()
    conn.close()
    
    return jsonify(users)

@app.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@login_required
@admin_required
def update_user_role(user_id):
    """Update user role (admin only)"""
    data = request.json
    new_role = data.get('role')
    
    if new_role not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('UPDATE users SET role = %s WHERE id = %s', (new_role, user_id))
    conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/delete-user', methods=['DELETE'])
@login_required
@admin_required
def delete_user_api():
    """Delete a user via API (admin only)"""
    import sys
    try:
        data = request.json
        user_id = data.get('user_id')
        
        print(f"[USER] Admin attempting to delete user_id: {user_id}", file=sys.stderr)
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Don't allow deleting yourself
        if int(user_id) == session.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get username before deletion
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        username = result[0]
        
        # Delete the user (CASCADE will delete related records)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[USER] User {username} (ID: {user_id}) deleted by admin", file=sys.stderr)
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
        
    except Exception as e:
        print(f"[USER] Error deleting user: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/admin/team-dashboard')
@login_required
@admin_required
def team_dashboard():
    """Team dashboard page (admin only)"""
    return render_template('team_dashboard.html', user=session)

@app.route('/api/admin/team-metrics')
@login_required
@admin_required
def team_metrics():
    """Get team-wide metrics (admin only)"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('''
        SELECT 
            u.id,
            u.username,
            u.full_name,
            SUM(CASE WHEN te.category != 'Holiday' THEN te.hours ELSE 0 END) as total_hours,
            SUM(CASE WHEN te.category = 'Project' THEN te.hours ELSE 0 END) as project_hours,
            SUM(CASE WHEN te.category = 'Admin' THEN te.hours ELSE 0 END) as admin_hours,
            SUM(CASE WHEN te.category = 'PTO' THEN te.hours ELSE 0 END) as pto_hours
        FROM users u
        LEFT JOIN time_entries te ON u.id = te.user_id 
            AND te.entry_date BETWEEN %s AND %s
        GROUP BY u.id, u.username, u.full_name
        ORDER BY u.username
    ''', (start_date, end_date))
    
    user_metrics = cur.fetchall()
    
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    weeks = days / 7.0
    available_hours = weeks * 40
    
    for user in user_metrics:
        user['project_utilization'] = (user['project_hours'] / available_hours * 100) if available_hours > 0 else 0
        user['admin_utilization'] = (user['admin_hours'] / available_hours * 100) if available_hours > 0 else 0
    
    cur.close()
    conn.close()
    
    return jsonify({
        'users': user_metrics,
        'weeks': round(weeks, 2),
        'available_hours': round(available_hours, 2)
    })

# Server Configuration Routes

@app.route('/admin')
@login_required
@admin_required
def admin():
    """Admin landing page"""
    return render_template('admin.html', user=session)

@app.route('/admin/server-config')
@login_required
@admin_required
def server_config():
    """Server configuration page"""
    return render_template('server_config.html', user=session)

@app.route('/api/admin/get-timezone', methods=['GET'])
@login_required
@admin_required
def get_timezone():
    """Get current server timezone"""
    try:
        result = subprocess.run(['/usr/bin/timedatectl', 'show', '--property=Timezone', '--value'], 
                              capture_output=True, text=True)
        timezone = result.stdout.strip()
        
        result_ntp = subprocess.run(['/usr/bin/timedatectl', 'show', '--property=NTP', '--value'], 
                                   capture_output=True, text=True)
        ntp_enabled = result_ntp.stdout.strip() == 'yes'
        
        result_time = subprocess.run(['/usr/bin/date'], capture_output=True, text=True)
        current_time = result_time.stdout.strip()
        
# Get NTP servers from timesyncd.conf
        ntp_servers = 'Default system servers'
        try:
            with open('/etc/systemd/timesyncd.conf', 'r') as f:
                for line in f:
                    if line.strip().startswith('NTP='):
                        servers = line.split('=', 1)[1].strip()
                        if servers:
                            ntp_servers = servers
                        break
        except:
            pass
        
        return jsonify({
            'current_time': current_time,
            'current_timezone': timezone,
            'ntp_enabled': ntp_enabled,
            'ntp_servers': ntp_servers
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/set-timezone', methods=['POST'])
@login_required
@admin_required
def set_timezone():
    """Set server timezone using admin helper service or sudo fallback"""
    timezone = request.json.get('timezone')
    try:
        if ADMIN_HELPER_AVAILABLE and AdminHelperClient:
            # Use admin helper service (preferred method)
            helper = AdminHelperClient()
            result = helper.set_timezone(timezone)
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify(result), 500
        else:
            # Fallback to sudo method (requires sudoers configuration)
            subprocess.run(['/usr/bin/sudo', '/usr/bin/timedatectl', 'set-timezone', timezone], check=True)
            return jsonify({'success': True, 'message': f'Timezone set to {timezone}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/set-ntp-servers', methods=['POST'])
@login_required
@admin_required
def set_ntp_servers():
    """Set custom NTP servers using admin helper service or sudo fallback"""
    try:
        data = request.json
        ntp_server1 = data.get('ntp_server1', '').strip()
        ntp_server2 = data.get('ntp_server2', '').strip()

        if not ntp_server1:
            return jsonify({'error': 'Primary NTP server is required'}), 400

        ntp_servers = [ntp_server1]
        if ntp_server2:
            ntp_servers.append(ntp_server2)

        if ADMIN_HELPER_AVAILABLE and AdminHelperClient:
            # Use admin helper service (preferred method)
            helper = AdminHelperClient()
            result = helper.set_ntp_servers(ntp_servers)
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify(result), 500
        else:
            # Fallback to sudo method (requires /usr/local/bin/update-ntp-config script)
            ntp_config = ' '.join(ntp_servers)
            proc = subprocess.Popen(
                ['/usr/bin/sudo', '/usr/local/bin/update-ntp-config'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(input=ntp_config.encode(), timeout=10)
            if proc.returncode == 0:
                return jsonify({'success': True, 'message': f'NTP servers set to: {ntp_config}'})
            else:
                return jsonify({'error': f'Failed to set NTP servers: {stderr.decode()}'}), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout setting NTP servers'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/sync-ntp', methods=['POST'])
@login_required
@admin_required
def sync_ntp():
    """Enable NTP time synchronization using admin helper service or sudo fallback"""
    try:
        if ADMIN_HELPER_AVAILABLE and AdminHelperClient:
            # Use admin helper service (preferred method)
            helper = AdminHelperClient()
            result = helper.enable_ntp_sync()
            if result.get('success'):
                return jsonify(result)
            else:
                return jsonify(result), 500
        else:
            # Fallback to sudo method
            subprocess.run(['/usr/bin/sudo', '/usr/bin/timedatectl', 'set-ntp', 'true'], check=True)
            return jsonify({'success': True, 'message': 'NTP sync enabled'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/get-server-info', methods=['GET'])
@login_required
@admin_required
def get_server_info():
    """Get server information"""
    try:
        # Get disk usage
        result = subprocess.run(['/usr/bin/df', '-h', '/opt/timetracker'], 
                              capture_output=True, text=True, check=False)
        disk_info = result.stdout if result.returncode == 0 else 'Unable to get disk info'
        
        # Get memory info
        result = subprocess.run(['/usr/bin/free', '-h'], 
                              capture_output=True, text=True, check=False)
        memory_info = result.stdout if result.returncode == 0 else 'Unable to get memory info'
        
        # Get uptime
        result = subprocess.run(['/usr/bin/uptime', '-p'], 
                              capture_output=True, text=True, check=False)
        uptime = result.stdout.strip() if result.returncode == 0 else 'Unable to get uptime'
        
        return jsonify({
            'disk_info': disk_info,
            'memory_info': memory_info,
            'uptime': uptime
        })
    except Exception as e:
        import traceback
        print(f"Error in get_server_info: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ========================================
# Export Routes
# ========================================

@app.route('/api/export/csv')
@login_required
def export_csv():
    """Export time entries to CSV"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute('''
        SELECT * FROM time_entries_with_details
        WHERE user_id = %s AND entry_date BETWEEN %s AND %s
        ORDER BY entry_date, id
    ''', (user_id, start_date, end_date))
    
    entries = cur.fetchall()
    
    cur.close()
    conn.close()
    
    output = io.StringIO()
    if entries:
        writer = csv.DictWriter(output, fieldnames=entries[0].keys())
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'time_entries_{start_date}_to_{end_date}.csv'
    )

# ========================================
# Code Editor
# ========================================    

import subprocess
import yaml
import ipaddress
import shutil
import glob

@app.route('/admin/code-editor')
@login_required
@admin_required
def code_editor():
    """Code editor page"""
    return render_template('code_editor.html', user=session)

# Add these routes to app.py

# ============================================================================
# USER MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/user-management')
@login_required
@admin_required
def user_management():
    """User management page (admin only)"""
    return render_template('user_management.html', user=session)


@app.route('/user/change-password-page')
@login_required
def change_password_page():
    """Change password page (all users)"""
    return render_template('change_password.html', user=session)


@app.route('/api/admin/get-users')
@login_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                username,
                full_name,
                role,
                is_active,
                last_login,
                hire_date,
                pto_time
            FROM users
            ORDER BY username
        """)

        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'is_admin': row[3] == 'admin',
                'is_active': row[4],  # Read actual value from database
                'last_login': row[5].strftime('%Y-%m-%d %H:%M') if row[5] else None,
                'hire_date': row[6].strftime('%Y-%m-%d') if row[6] else None,
                'pto_time': float(row[7]) if row[7] else None
            })

        cursor.close()
        conn.close()

        return jsonify({'users': users})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/change-user-password', methods=['POST'])
@login_required
@admin_required
def change_user_password():
    """Admin changes any user's password"""
    import sys
    try:
        data = request.json
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        print(f"[PASSWORD] Admin changing password for user_id: {user_id}", file=sys.stderr)
        
        if not user_id or not new_password:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update password
        cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """, (password_hash, user_id))
        
        conn.commit()
        
        # Get username for logging
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        username = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"[PASSWORD] Successfully changed password for user: {username}", file=sys.stderr)
        
        return jsonify({
            'success': True,
            'message': f'Password changed for user {username}'
        })
        
    except Exception as e:
        print(f"[PASSWORD] Error: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/toggle-user-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active():
    """Toggle user active status"""
    import sys
    try:
        data = request.json
        user_id = data.get('user_id')
        
        print(f"[USER] Admin toggling active status for user_id: {user_id}", file=sys.stderr)
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Don't allow deactivating yourself
        if int(user_id) == session.get('user_id'):
            return jsonify({'error': 'Cannot deactivate your own account'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Toggle active status
        cursor.execute("""
            UPDATE users
            SET is_active = NOT is_active
            WHERE id = %s
            RETURNING username, is_active
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        username, is_active = result
        conn.commit()
        cursor.close()
        conn.close()
        
        status = 'activated' if is_active else 'deactivated'
        print(f"[USER] User {username} {status}", file=sys.stderr)
        
        return jsonify({
            'success': True,
            'message': f'User {username} {status}',
            'is_active': is_active
        })
        
    except Exception as e:
        print(f"[USER] Error: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/update-user-employment', methods=['POST'])
@login_required
@admin_required
def update_user_employment():
    """Admin updates user hire date and PTO time"""
    import sys
    try:
        data = request.json
        user_id = data.get('user_id')
        hire_date = data.get('hire_date')  # Can be None
        pto_time = data.get('pto_time')    # Can be None

        print(f"[USER] Admin updating employment info for user_id: {user_id}", file=sys.stderr)

        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update hire_date and pto_time
        cursor.execute("""
            UPDATE users
            SET hire_date = %s, pto_time = %s
            WHERE id = %s
            RETURNING username
        """, (hire_date, pto_time, user_id))

        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'User not found'}), 404

        username = result[0]
        conn.commit()
        cursor.close()
        conn.close()

        print(f"[USER] Updated employment info for {username}: hire_date={hire_date}, pto_time={pto_time}", file=sys.stderr)

        return jsonify({
            'success': True,
            'message': f'Employment information updated for {username}'
        })

    except Exception as e:
        print(f"[USER] Error: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/change-password', methods=['POST'])
@login_required
def user_change_password():
    """User changes their own password"""
    import sys
    try:
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        user_id = session.get('user_id')
        username = session.get('username')
        
        print(f"[PASSWORD] User {username} attempting password change", file=sys.stderr)
        
        if not current_password or not new_password:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        
        if current_password == new_password:
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current password hash
        cursor.execute("""
            SELECT password_hash
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        current_hash = result[0]
        
        # Verify current password
        if not check_password_hash(current_hash, current_password):
            print(f"[PASSWORD] Invalid current password for user {username}", file=sys.stderr)
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash new password
        new_hash = generate_password_hash(new_password)
        
        # Update password
        cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """, (new_hash, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[PASSWORD] Successfully changed password for user {username}", file=sys.stderr)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        print(f"[PASSWORD] Error: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500
@app.route('/api/admin/read-file', methods=['POST'])
@login_required
@admin_required
def read_file():
    """Read file content - allows all HTML templates dynamically"""
    data = request.json
    filename = data.get('filename')
    
    # Static files with fixed paths
    static_files = {
        'app.py': '/opt/timetracker/app.py',
        'requirements.txt': '/opt/timetracker/requirements.txt',
        '.env': '/opt/timetracker/.env',
        'style.css': '/opt/timetracker/static/css/style.css'
    }
    
    # Check if it's a static file
    if filename in static_files:
        filepath = static_files[filename]
    # Check if it's an HTML template (dynamic)
    elif filename.endswith('.html'):
        # Security: prevent path traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 403
        
        filepath = f'/opt/timetracker/templates/{filename}'
        
        # Verify file exists
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
    else:
        return jsonify({'error': 'File not allowed'}), 403
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/save-file', methods=['POST'])
@login_required
@admin_required
def save_file():
    """Save file content - allows all HTML templates dynamically"""
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    
    # Static files with fixed paths
    static_files = {
        'app.py': '/opt/timetracker/app.py',
        'requirements.txt': '/opt/timetracker/requirements.txt',
        '.env': '/opt/timetracker/.env',
        'style.css': '/opt/timetracker/static/css/style.css'
    }
    
    # Check if it's a static file
    if filename in static_files:
        filepath = static_files[filename]
    # Check if it's an HTML template (dynamic)
    elif filename.endswith('.html'):
        # Security: prevent path traversal
        if '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 403
        
        filepath = f'/opt/timetracker/templates/{filename}'
        
        # Verify file exists (for editing existing files)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
    else:
        return jsonify({'error': 'File not allowed'}), 403
    
    try:
        # Create backup
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        
        # Validate Python syntax
        if filename.endswith('.py'):
            try:
                compile(content, filename, 'exec')
            except SyntaxError as e:
                return jsonify({'error': f'Syntax Error: Line {e.lineno}: {e.msg}'}), 400
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)
        
        # Restart if app.py
        if filename == 'app.py':
            subprocess.run(['/usr/bin/sudo', '/bin/systemctl', 'restart', 'timetracker'])
            return jsonify({'success': True, 'message': 'File saved and restarting...'})
        
        return jsonify({'success': True, 'message': 'File saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/list-backups', methods=['GET'])
@login_required
@admin_required
def list_backups():
    """List backup files"""
    backups = []
    for pattern in ['/opt/timetracker/app.py.backup.*', '/opt/timetracker/.env.backup.*']:
        for filepath in glob.glob(pattern):
            stat = os.stat(filepath)
            backups.append({
                'filename': os.path.basename(filepath),
                'path': filepath,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(backups)

@app.route('/api/admin/list-templates', methods=['GET'])
@login_required
@admin_required
def list_templates():
    """List all HTML template files dynamically"""
    try:
        templates_dir = '/opt/timetracker/templates'
        template_files = []
        
        # Get all .html files
        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(templates_dir, filename)
                template_files.append({
                    'filename': filename,
                    'modified': os.path.getmtime(filepath)
                })
        
        # Sort alphabetically
        template_files.sort(key=lambda x: x['filename'].lower())
        
        return jsonify(template_files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/restore-backup', methods=['POST'])
@login_required
@admin_required
def restore_backup():
    """Restore from backup"""
    backup_path = request.json.get('backup_path')
    
    if not backup_path.startswith('/opt/timetracker/'):
        return jsonify({'error': 'Invalid path'}), 403
    
    try:
        if 'app.py.backup' in backup_path:
            target = '/opt/timetracker/app.py'
        elif '.env.backup' in backup_path:
            target = '/opt/timetracker/.env'
        else:
            return jsonify({'error': 'Unknown backup type'}), 400
        
        shutil.copy2(backup_path, target)
        subprocess.run(['/usr/bin/sudo', '/bin/systemctl', 'restart', 'timetracker'])
        return jsonify({'success': True, 'message': 'Restored and restarting...'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/get-network-config')
@login_required
@admin_required
def get_network_config():
    """Get current network configuration"""
    try:
        # Find the primary network interface
        result = subprocess.run(['/usr/sbin/ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        interface = 'ens160'
        
        if result.stdout:
            parts = result.stdout.split()
            if 'dev' in parts:
                interface = parts[parts.index('dev') + 1]
        
        # Get IP address and subnet
        result = subprocess.run(['/usr/sbin/ip', 'addr', 'show', interface], 
                              capture_output=True, text=True)
        
        ip_address = 'Not configured'
        subnet_mask = 'Not configured'
        
        for line in result.stdout.split('\n'):
            if 'inet ' in line and not 'inet6' in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    cidr = parts[1]
                    ip, prefix = cidr.split('/')
                    ip_address = ip
                    subnet_mask = str(ipaddress.IPv4Network(f'0.0.0.0/{prefix}', strict=False).netmask)
        
        # Get gateway
        result = subprocess.run(['/usr/sbin/ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        gateway = 'Not configured'
        if result.stdout:
            parts = result.stdout.split()
            if 'via' in parts:
                gateway = parts[parts.index('via') + 1]
        
# Get DNS servers from resolvectl (systemd-resolved)
        dns_servers = 'Not configured'
        try:
            result = subprocess.run(
                ['/usr/bin/resolvectl', 'status'],
                capture_output=True, text=True
            )
            if result.stdout:
                nameservers = []
                for line in result.stdout.split('\n'):
                    if 'DNS Servers:' in line:
                        # Extract DNS IPs from lines like "       DNS Servers: 8.8.8.8"
                        parts = line.split('DNS Servers:')
                        if len(parts) > 1:
                            dns = parts[1].strip()
                            if dns and dns not in nameservers:
                                nameservers.append(dns)
                if nameservers:
                    dns_servers = ', '.join(nameservers)
        except:
            pass
        
        return jsonify({
            'interface': interface,
            'ip_address': ip_address,
            'subnet_mask': subnet_mask,
            'gateway': gateway,
            'dns_servers': dns_servers
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/set-network-config', methods=['POST'])
@login_required
@admin_required
def set_network_config():
    """Set network configuration using admin helper service"""
    import sys
    try:
        data = request.json
        ip_address = data.get('ip_address')
        subnet_mask = data.get('subnet_mask')
        gateway = data.get('gateway')
        dns1 = data.get('dns1')
        dns2 = data.get('dns2', '')

        print(f"[NETWORK] Received request: IP={ip_address}, Subnet={subnet_mask}, GW={gateway}, DNS1={dns1}, DNS2={dns2}", file=sys.stderr)

        if not all([ip_address, subnet_mask, gateway, dns1]):
            print(f"[NETWORK] Missing required fields", file=sys.stderr)
            return jsonify({'error': 'Missing required fields'}), 400

        # Find network interface
        result = subprocess.run(['/usr/sbin/ip', 'route', 'show', 'default'],
                              capture_output=True, text=True)
        interface = 'ens160'
        if result.stdout:
            parts = result.stdout.split()
            if 'dev' in parts:
                interface = parts[parts.index('dev') + 1]

        print(f"[NETWORK] Using interface: {interface}", file=sys.stderr)

        # Use admin helper service to set network config
        from admin_helper_client import AdminHelperClient
        helper = AdminHelperClient()

        print(f"[NETWORK] Calling admin helper service...", file=sys.stderr)
        result = helper.set_network_config(
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            gateway=gateway,
            dns1=dns1,
            dns2=dns2,
            interface=interface
        )

        print(f"[NETWORK] Helper response: {result}", file=sys.stderr)

        if result.get('success'):
            print(f"[NETWORK] Success!", file=sys.stderr)
            return jsonify(result)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"[NETWORK] Error: {error_msg}", file=sys.stderr)
            return jsonify(result), 500

    except Exception as e:
        import traceback
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"[NETWORK] Exception: {error_msg}", file=sys.stderr)
        print(f"[NETWORK] Traceback:\n{tb}", file=sys.stderr)
        return jsonify({'error': error_msg}), 500




# ============================================================================
# ADMIN USER DATA MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/manage-user-data')
@login_required
@admin_required
def manage_user_data():
    """Admin page to view and edit other users' data"""
    return render_template('manage_user_data.html', user=session)


@app.route('/api/admin/user-projects/<int:user_id>')
@login_required
@admin_required
def get_user_projects(user_id):
    """Get all projects for a specific user with usage statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute('''
            SELECT 
                pb.id,
                pb.job_number,
                pb.customer_name,
                pb.project_description,
                pb.budget_hours,
                pb.status,
                pb.start_date,
                pb.end_date,
                COALESCE(SUM(te.hours), 0) as hours_used,
                pb.budget_hours - COALESCE(SUM(te.hours), 0) as hours_remaining,
                CASE WHEN pb.budget_hours > 0 
                     THEN ROUND((COALESCE(SUM(te.hours), 0) / pb.budget_hours * 100)::numeric, 1)
                     ELSE 0 END as percent_used
            FROM project_budgets pb
            LEFT JOIN time_entries te ON pb.job_number = te.job_number
            WHERE pb.user_id = %s
            GROUP BY pb.id, pb.job_number, pb.customer_name, pb.project_description,
                     pb.budget_hours, pb.status, pb.start_date, pb.end_date
            ORDER BY pb.customer_name, pb.job_number
        ''', (user_id,))
        
        projects = cur.fetchall()
        
        # Convert dates to strings
        for p in projects:
            if p['start_date']:
                p['start_date'] = p['start_date'].isoformat()
            if p['end_date']:
                p['end_date'] = p['end_date'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/user-time-entries/<int:user_id>')
@login_required
@admin_required
def get_user_time_entries(user_id):
    """Get time entries for a specific user"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute('''
            SELECT 
                te.id,
                te.entry_date,
                te.hours,
                te.job_number,
                te.job_task_code,
                te.category,
                te.description,
                pb.customer_name
            FROM time_entries te
            LEFT JOIN project_budgets pb ON te.job_number = pb.job_number
            WHERE te.user_id = %s AND te.entry_date BETWEEN %s AND %s
            ORDER BY te.entry_date DESC, te.id DESC
        ''', (user_id, start_date, end_date))
        
        entries = cur.fetchall()
        
        # Convert dates
        for entry in entries:
            if entry['entry_date']:
                entry['entry_date'] = entry['entry_date'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(entries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/update-time-entry/<int:entry_id>', methods=['PUT'])
@login_required
@admin_required
def admin_update_time_entry(entry_id):
    """Admin updates any user's time entry"""
    import sys
    try:
        data = request.json
        
        print(f"[ADMIN] Updating time entry {entry_id}", file=sys.stderr)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE time_entries
            SET entry_date = %s,
                hours = %s,
                job_number = %s,
                category = %s,
                description = %s
            WHERE id = %s
        ''', (
            data.get('entry_date'),
            data.get('hours'),
            data.get('job_number'),
            data.get('category'),
            data.get('description'),
            entry_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[ADMIN] Time entry {entry_id} updated successfully", file=sys.stderr)
        
        return jsonify({'success': True, 'message': 'Time entry updated'})
    except Exception as e:
        print(f"[ADMIN] Error updating time entry: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/delete-time-entry/<int:entry_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_time_entry(entry_id):
    """Admin deletes any user's time entry"""
    import sys
    try:
        print(f"[ADMIN] Deleting time entry {entry_id}", file=sys.stderr)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('DELETE FROM time_entries WHERE id = %s', (entry_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[ADMIN] Time entry {entry_id} deleted successfully", file=sys.stderr)
        
        return jsonify({'success': True, 'message': 'Time entry deleted'})
    except Exception as e:
        print(f"[ADMIN] Error deleting time entry: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500



@app.route('/api/admin/add-time-entry', methods=['POST'])
@login_required
@admin_required
def admin_add_time_entry():
    """Admin adds a time entry for any user"""
    import sys
    try:
        data = request.json
        
        user_id = data.get('user_id')
        entry_date = data.get('entry_date')
        hours = data.get('hours')
        job_number = data.get('job_number')
        job_task_code = data.get('job_task_code')
        category = data.get('category')
        description = data.get('description', '')
        
        print(f"[ADMIN] Adding time entry for user_id: {user_id}", file=sys.stderr)
        
        if not user_id or not entry_date or not hours or not category:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate that user exists
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Insert time entry
        cur.execute('''
            INSERT INTO time_entries 
            (user_id, entry_date, hours, job_number, job_task_code, category, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, entry_date, hours, job_number, job_task_code, category, description))
        
        entry_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[ADMIN] Time entry {entry_id} created for user {user_id}", file=sys.stderr)
        
        return jsonify({
            'success': True,
            'id': entry_id,
            'message': 'Time entry added successfully'
        })
    except Exception as e:
        print(f"[ADMIN] Error adding time entry: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REPORTING ROUTES
# ============================================================================

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    """Admin page to view summary reports"""
    return render_template('reports.html', user=session)


@app.route('/api/reports/summary', methods=['GET'])
@login_required
@admin_required
def report_summary():
    """Admin endpoint to get total hours per project and user utilization"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Default to past 30 days if dates not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Calculate available hours based on date range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days + 1
        weeks = days / 7.0
        available_hours = weeks * 40.0

        # Query 1: Total hours per active project with budget comparison
        cur.execute('''
            SELECT
                pb.job_number,
                pb.customer_name,
                pb.budget_hours,
                COALESCE(SUM(te.hours), 0) as total_hours
            FROM project_budgets pb
            LEFT JOIN time_entries te ON pb.job_number = te.job_number
                AND te.entry_date BETWEEN %s AND %s AND te.category = 'Project'
            WHERE pb.status = 'Active'
            GROUP BY pb.job_number, pb.customer_name, pb.budget_hours
            ORDER BY total_hours DESC
        ''', (start_date, end_date))

        projects_raw = cur.fetchall()

        # Enhance project data with budget calculations
        projects = []
        for p in projects_raw:
            actual_hours = float(p['total_hours'] or 0)
            budget_hours = float(p['budget_hours'] or 0)
            remaining_hours = budget_hours - actual_hours
            percent_used = (actual_hours / budget_hours * 100) if budget_hours > 0 else 0

            # Determine status
            if percent_used > 100:
                status = 'over_budget'
            elif percent_used >= 90:
                status = 'warning'
            else:
                status = 'on_track'

            projects.append({
                'job_number': p['job_number'],
                'customer_name': p['customer_name'],
                'total_hours': actual_hours,
                'budget_hours': budget_hours,
                'remaining_hours': remaining_hours,
                'percent_used': round(percent_used, 1),
                'status': status
            })

        # Query 2: User utilization percentages with PTO and status
        cur.execute('''
            SELECT
                u.id as user_id,
                u.username,
                u.full_name,
                u.hire_date,
                SUM(CASE WHEN te.category = 'Project' THEN te.hours ELSE 0 END) as project_hours,
                SUM(CASE WHEN te.category = 'Admin' THEN te.hours ELSE 0 END) as admin_hours,
                SUM(CASE WHEN te.category = 'PTO' THEN te.hours ELSE 0 END) as pto_hours,
                SUM(CASE WHEN te.category = 'Holiday' THEN te.hours ELSE 0 END) as holiday_hours,
                SUM(CASE WHEN te.category != 'Holiday' THEN te.hours ELSE 0 END) as total_hours
            FROM users u
            LEFT JOIN time_entries te ON u.id = te.user_id
                AND te.entry_date BETWEEN %s AND %s
            WHERE u.is_active = TRUE OR u.is_active IS NULL
            GROUP BY u.id, u.username, u.full_name, u.hire_date
            ORDER BY u.full_name
        ''', (start_date, end_date))

        users_data = cur.fetchall()

        users = []
        for u in users_data:
            project_hrs = float(u['project_hours'] or 0)
            admin_hrs = float(u['admin_hours'] or 0)
            pto_hrs = float(u['pto_hours'] or 0)
            holiday_hrs = float(u['holiday_hours'] or 0)
            total_hrs = float(u['total_hours'] or 0)

            project_util = 0
            admin_util = 0
            total_util = 0

            if available_hours > 0:
                project_util = round((project_hrs / available_hours) * 100, 1)
                admin_util = round((admin_hrs / available_hours) * 100, 1)
                total_util = round(((project_hrs + admin_hrs + pto_hrs) / available_hours) * 100, 1)

            # Determine status
            if total_util > 100:
                status = 'overworked'
            elif total_util < 50:
                status = 'underutilized'
            else:
                status = 'optimal'

            # Calculate average hours per week
            avg_hours_per_week = (total_hrs / weeks) if weeks > 0 else 0

            users.append({
                'user_id': u['user_id'],
                'username': u['username'],
                'full_name': u['full_name'],
                'hire_date': u['hire_date'].strftime('%Y-%m-%d') if u['hire_date'] else None,
                'project_hours': project_hrs,
                'admin_hours': admin_hrs,
                'pto_hours': pto_hrs,
                'holiday_hours': holiday_hrs,
                'total_hours': total_hrs,
                'project_utilization_percent': project_util,
                'admin_utilization_percent': admin_util,
                'total_utilization_percent': total_util,
                'avg_hours_per_week': round(avg_hours_per_week, 1),
                'status': status
            })

        return jsonify({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date,
                'available_hours_per_user': round(available_hours, 2)
            },
            'projects': projects,
            'users': users
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/reports/executive-summary', methods=['GET'])
@login_required
@admin_required
def report_executive_summary():
    """Executive summary metrics for system reports"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Total company hours YTD (Year 2026)
        cur.execute('''
            SELECT COALESCE(SUM(hours), 0) as total_hours_ytd
            FROM time_entries
            WHERE entry_date >= '2026-01-01'
        ''')
        total_hours_ytd = float(cur.fetchone()['total_hours_ytd'])

        # Average utilization across all active users
        cur.execute('''
            SELECT
                COUNT(DISTINCT u.id) as user_count,
                COALESCE(SUM(te.hours), 0) as total_hours
            FROM users u
            LEFT JOIN time_entries te ON u.id = te.user_id
                AND te.entry_date >= '2026-01-01'
                AND te.category != 'Holiday'
            WHERE u.is_active = TRUE
        ''')
        util_data = cur.fetchone()
        user_count = util_data['user_count']
        total_work_hours = float(util_data['total_hours'])

        # Calculate average utilization (based on weeks YTD * 40 hrs/week)
        today = datetime.now()
        start_of_year = datetime(2026, 1, 1)
        days_ytd = (today - start_of_year).days + 1
        weeks_ytd = days_ytd / 7.0
        available_hours_per_user = weeks_ytd * 40.0

        avg_utilization = 0
        if user_count > 0 and available_hours_per_user > 0:
            avg_utilization = (total_work_hours / (user_count * available_hours_per_user)) * 100

        # Active employee count (users with hire_date)
        cur.execute('''
            SELECT COUNT(*) as employee_count
            FROM users
            WHERE is_active = TRUE AND hire_date IS NOT NULL
        ''')
        employee_count = cur.fetchone()['employee_count']

        # PTO usage rate (company-wide)
        cur.execute('''
            SELECT
                COALESCE(SUM(pto_time), 0) as total_pto_allocated,
                COALESCE((
                    SELECT SUM(te.hours)
                    FROM time_entries te
                    WHERE te.category = 'PTO' AND te.entry_date >= '2026-01-01'
                ), 0) as total_pto_used
            FROM users
            WHERE is_active = TRUE AND pto_time IS NOT NULL
        ''')
        pto_data = cur.fetchone()
        total_pto_allocated = float(pto_data['total_pto_allocated'])
        total_pto_used = float(pto_data['total_pto_used'])

        pto_usage_rate = 0
        if total_pto_allocated > 0:
            pto_usage_rate = (total_pto_used / total_pto_allocated) * 100

        return jsonify({
            'total_hours_ytd': round(total_hours_ytd, 1),
            'avg_utilization': round(avg_utilization, 1),
            'active_employee_count': employee_count,
            'pto_usage_rate': round(pto_usage_rate, 1),
            'pto_allocated': round(total_pto_allocated, 1),
            'pto_used': round(total_pto_used, 1),
            'pto_remaining': round(total_pto_allocated - total_pto_used, 1)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/reports/pto-analytics', methods=['GET'])
@login_required
@admin_required
def report_pto_analytics():
    """PTO analytics for all employees"""
    start_date = request.args.get('start_date', '2026-01-01')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Get all users with PTO data
        cur.execute('''
            SELECT
                u.id,
                u.username,
                u.full_name,
                u.hire_date,
                u.pto_time as total_pto
            FROM users u
            WHERE u.is_active = TRUE AND u.hire_date IS NOT NULL AND u.pto_time IS NOT NULL
            ORDER BY u.full_name
        ''')
        users = cur.fetchall()

        results = []
        alerts = {'critical': [], 'warning': [], 'info': []}

        for user in users:
            # Calculate PTO year boundaries
            hire_date = user['hire_date']
            total_pto = float(user['total_pto'])
            today = datetime.now().date()
            current_year = today.year

            anniversary_this_year = hire_date.replace(year=current_year)
            if today < anniversary_this_year:
                pto_year_start = hire_date.replace(year=current_year - 1)
                pto_reset_date = anniversary_this_year
            else:
                pto_year_start = anniversary_this_year
                pto_reset_date = hire_date.replace(year=current_year + 1)

            # Get PTO used in current PTO year
            cur.execute('''
                SELECT COALESCE(SUM(hours), 0) as pto_used
                FROM time_entries
                WHERE user_id = %s AND category = 'PTO'
                  AND entry_date >= %s AND entry_date < %s
            ''', (user['id'], pto_year_start, pto_reset_date))

            pto_used = float(cur.fetchone()['pto_used'])
            pto_remaining = total_pto - pto_used
            pto_percent_used = (pto_used / total_pto * 100) if total_pto > 0 else 0
            days_until_reset = (pto_reset_date - today).days

            user_data = {
                'user_id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'hire_date': hire_date.strftime('%Y-%m-%d'),
                'total_pto': total_pto,
                'pto_used': pto_used,
                'pto_remaining': pto_remaining,
                'pto_percent_used': round(pto_percent_used, 1),
                'reset_date': pto_reset_date.strftime('%Y-%m-%d'),
                'days_until_reset': days_until_reset
            }

            results.append(user_data)

            # Generate alerts
            if pto_remaining < (total_pto * 0.1):  # Less than 10% remaining
                alerts['critical'].append({
                    'user': user['full_name'],
                    'message': f"Only {pto_remaining:.1f} hours PTO remaining ({pto_percent_used:.0f}% used)"
                })

            if pto_used == 0 and days_until_reset < 180:  # No PTO used and more than halfway through year
                alerts['warning'].append({
                    'user': user['full_name'],
                    'message': f"No PTO used this year ({total_pto:.1f} hours available)"
                })

            if days_until_reset <= 30 and pto_remaining > 0:  # PTO expiring soon
                alerts['info'].append({
                    'user': user['full_name'],
                    'message': f"{pto_remaining:.1f} hours PTO expires in {days_until_reset} days"
                })

        return jsonify({
            'employees': results,
            'alerts': alerts,
            'summary': {
                'total_employees': len(results),
                'total_pto_allocated': sum(r['total_pto'] for r in results),
                'total_pto_used': sum(r['pto_used'] for r in results),
                'total_pto_remaining': sum(r['pto_remaining'] for r in results)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/reports/monthly-breakdown', methods=['GET'])
@login_required
@admin_required
def report_monthly_breakdown():
    """Monthly breakdown of hours by category"""
    start_date = request.args.get('start_date', '2026-01-01')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute('''
            SELECT
                TO_CHAR(entry_date, 'YYYY-MM') as month,
                SUM(CASE WHEN category = 'Project' THEN hours ELSE 0 END) as project_hours,
                SUM(CASE WHEN category = 'Admin' THEN hours ELSE 0 END) as admin_hours,
                SUM(CASE WHEN category = 'PTO' THEN hours ELSE 0 END) as pto_hours,
                SUM(CASE WHEN category = 'Holiday' THEN hours ELSE 0 END) as holiday_hours,
                SUM(hours) as total_hours,
                COUNT(DISTINCT user_id) as active_users
            FROM time_entries
            WHERE entry_date BETWEEN %s AND %s
            GROUP BY TO_CHAR(entry_date, 'YYYY-MM')
            ORDER BY month DESC
        ''', (start_date, end_date))

        monthly_data = cur.fetchall()

        results = []
        for row in monthly_data:
            # Calculate average utilization for the month
            # Assuming ~4.33 weeks per month * 40 hours = 173.2 hours per user
            active_users = row['active_users']
            total_work_hours = float(row['project_hours']) + float(row['admin_hours']) + float(row['pto_hours'])
            available_hours = active_users * 173.2  # Average hours per month

            avg_utilization = 0
            if available_hours > 0:
                avg_utilization = (total_work_hours / available_hours) * 100

            results.append({
                'month': row['month'],
                'project_hours': float(row['project_hours']),
                'admin_hours': float(row['admin_hours']),
                'pto_hours': float(row['pto_hours']),
                'holiday_hours': float(row['holiday_hours']),
                'total_hours': float(row['total_hours']),
                'active_users': active_users,
                'avg_utilization': round(avg_utilization, 1)
            })

        return jsonify({'months': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/reports/task-code-stats', methods=['GET'])
@login_required
@admin_required
def report_task_code_stats():
    """Task code usage statistics"""
    start_date = request.args.get('start_date', '2026-01-01')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Get total hours for percentage calculation
        cur.execute('''
            SELECT COALESCE(SUM(hours), 0) as total_hours
            FROM time_entries
            WHERE entry_date BETWEEN %s AND %s
        ''', (start_date, end_date))

        total_hours = float(cur.fetchone()['total_hours'])

        # Get task code statistics
        cur.execute('''
            SELECT
                te.job_task_code,
                jtc.task_name,
                jtc.category,
                SUM(te.hours) as total_hours,
                COUNT(DISTINCT te.user_id) as user_count,
                COUNT(DISTINCT te.job_number) as project_count,
                COUNT(*) as entry_count
            FROM time_entries te
            LEFT JOIN job_task_codes jtc ON te.job_task_code::text = jtc.task_code::text
            WHERE te.entry_date BETWEEN %s AND %s
            GROUP BY te.job_task_code, jtc.task_name, jtc.category
            ORDER BY total_hours DESC
            LIMIT 20
        ''', (start_date, end_date))

        task_codes = cur.fetchall()

        results = []
        for row in task_codes:
            hours = float(row['total_hours'])
            percent = (hours / total_hours * 100) if total_hours > 0 else 0

            results.append({
                'task_code': row['job_task_code'],
                'task_name': row['task_name'] or f"Task {row['job_task_code']}",
                'category': row['category'] or 'Unknown',
                'hours': hours,
                'percent': round(percent, 1),
                'user_count': row['user_count'],
                'project_count': row['project_count'],
                'entry_count': row['entry_count']
            })

        return jsonify({
            'task_codes': results,
            'total_hours': total_hours
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


# ============================================================================
# FULL SYSTEM BACKUP ROUTES
# ============================================================================

FULL_BACKUP_DIR = '/opt/timetracker/backups/full'

@app.route('/admin/system-backup')
@login_required
@admin_required
def admin_system_backup():
    """Admin page to manage full system backups"""
    return render_template('system_backup.html', user=session)


@app.route('/api/admin/create-full-backup', methods=['POST'])
@login_required
@admin_required
def create_full_backup():
    """Create a full system backup: app files + database dump bundled in a tar.gz"""
    import tempfile, tarfile, textwrap
    try:
        os.makedirs(FULL_BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        bundle_name = f'timetracker_backup_{timestamp}.tar.gz'
        bundle_path = os.path.join(FULL_BACKUP_DIR, bundle_name)

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Database dump
            db_dump_path = os.path.join(tmpdir, 'database.sql')
            env = os.environ.copy()
            env['PGPASSWORD'] = DB_CONFIG.get('password', '')
            result = subprocess.run(
                ['/usr/bin/pg_dump',
                 '-h', DB_CONFIG.get('host', 'localhost'),
                 '-p', str(DB_CONFIG.get('port', 5432)),
                 '-U', DB_CONFIG.get('user', 'timetracker'),
                 '-d', DB_CONFIG.get('database', 'timetracker'),
                 '-f', db_dump_path],
                env=env, capture_output=True, text=True
            )
            if result.returncode != 0:
                return jsonify({'error': f'pg_dump failed: {result.stderr}'}), 500

            # 2. App files tar (exclude venv, pycache, existing backups, test files)
            files_tar_path = os.path.join(tmpdir, 'timetracker_files.tar.gz')
            with tarfile.open(files_tar_path, 'w:gz') as tar:
                app_dir = '/opt/timetracker'
                exclude_names = {
                    'venv', '__pycache__', 'backups', '.git', '.cache',
                    'netplan-backups', 'ntp-backups', 'database',
                    'test_api.py', 'test_ui.py'
                }
                def _filter(tarinfo):
                    parts = tarinfo.name.split('/')
                    for part in parts:
                        if part in exclude_names:
                            return None
                    return tarinfo
                def _add_safe(tar, path, arcname):
                    try:
                        tar.add(path, arcname=arcname, filter=_filter, recursive=True)
                    except PermissionError:
                        pass
                _add_safe(tar, app_dir, 'timetracker')

            # 3. Generate restore.sh
            restore_script = textwrap.dedent(f"""\
                #!/usr/bin/env bash
                # Savant Time Tracker — Full Restore Script
                # Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                # Run on a fresh Ubuntu server as root or with sudo

                set -e
                SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
                APP_DIR=/opt/timetracker
                DB_NAME=timetracker
                DB_USER=timetracker

                echo "=== Savant Time Tracker Restore ==="

                # Install dependencies
                echo "[1/7] Installing system packages..."
                apt-get update -qq
                apt-get install -y -qq postgresql python3 python3-venv python3-pip nginx curl

                # Create OS user
                echo "[2/7] Creating system user..."
                id -u timetracker &>/dev/null || useradd -r -s /bin/false -d $APP_DIR timetracker

                # PostgreSQL setup
                echo "[3/7] Setting up PostgreSQL database..."
                systemctl start postgresql
                DB_PASSWORD=$(openssl rand -hex 16)
                sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
                sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" || true
                sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
                sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
                sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

                # Extract application files
                echo "[4/7] Restoring application files..."
                mkdir -p $APP_DIR
                tar xzf "$SCRIPT_DIR/timetracker_files.tar.gz" -C /opt/
                chown -R timetracker:timetracker $APP_DIR

                # Write .env
                cat > $APP_DIR/.env <<ENV
                SECRET_KEY=$(openssl rand -hex 32)
                DB_HOST=localhost
                DB_NAME=$DB_NAME
                DB_USER=$DB_USER
                DB_PASSWORD=$DB_PASSWORD
                DB_PORT=5432
                ENV
                chmod 600 $APP_DIR/.env

                # Recreate virtualenv
                echo "[5/7] Installing Python dependencies..."
                python3 -m venv $APP_DIR/venv
                $APP_DIR/venv/bin/pip install -q -r $APP_DIR/requirements.txt

                # Restore database
                echo "[6/7] Restoring database..."
                PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -f "$SCRIPT_DIR/database.sql"

                # Systemd service
                echo "[7/7] Registering and starting service..."
                cat > /etc/systemd/system/timetracker.service <<UNIT
                [Unit]
                Description=Savant Time Tracker
                After=network.target postgresql.service

                [Service]
                User=timetracker
                WorkingDirectory=$APP_DIR
                EnvironmentFile=$APP_DIR/.env
                ExecStart=$APP_DIR/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
                Restart=always

                [Install]
                WantedBy=multi-user.target
                UNIT

                systemctl daemon-reload
                systemctl enable timetracker
                systemctl start timetracker

                echo ""
                echo "=== Restore Complete! ==="
                echo "Database password: $DB_PASSWORD"
                echo "Please configure Nginx to proxy to http://127.0.0.1:5000"
                echo "Update /opt/timetracker/.env if you need to change any settings."
            """)

            restore_path = os.path.join(tmpdir, 'restore.sh')
            with open(restore_path, 'w') as f:
                f.write(restore_script)

            # 4. Bundle everything into final tar.gz
            with tarfile.open(bundle_path, 'w:gz') as bundle:
                bundle.add(db_dump_path,    arcname='database.sql')
                bundle.add(files_tar_path,  arcname='timetracker_files.tar.gz')
                bundle.add(restore_path,    arcname='restore.sh')

        stat = os.stat(bundle_path)
        return jsonify({
            'success': True,
            'filename': bundle_name,
            'size': stat.st_size,
            'created': datetime.now().isoformat()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/list-full-backups', methods=['GET'])
@login_required
@admin_required
def list_full_backups():
    """List all full system backup bundles"""
    try:
        os.makedirs(FULL_BACKUP_DIR, exist_ok=True)
        backups = []
        for f in os.listdir(FULL_BACKUP_DIR):
            if f.endswith('.tar.gz') and f.startswith('timetracker_backup_'):
                fp = os.path.join(FULL_BACKUP_DIR, f)
                stat = os.stat(fp)
                backups.append({
                    'filename': f,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        backups.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(backups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/download-backup/<filename>', methods=['GET'])
@login_required
@admin_required
def download_backup(filename):
    """Stream a full backup file for download"""
    # Security: only allow alphanumeric, underscores, hyphens, dots
    import re as _re
    if not _re.match(r'^[\w\-\.]+\.tar\.gz$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join(FULL_BACKUP_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Backup not found'}), 404
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=filename,
                     mimetype='application/gzip')


@app.route('/api/admin/delete-backup/<filename>', methods=['DELETE'])
@login_required
@admin_required
def delete_full_backup(filename):
    """Delete a full backup bundle"""
    import re as _re
    if not _re.match(r'^[\w\-\.]+\.tar\.gz$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join(FULL_BACKUP_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Backup not found'}), 404
    os.remove(filepath)
    return jsonify({'success': True, 'message': f'{filename} deleted'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
