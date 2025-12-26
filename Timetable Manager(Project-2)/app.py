from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from database import init_db, get_db_connection
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'timetable-secret-key-change-in-production'

# Initialize database
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            institution = request.form.get('institution', '')
            phone = request.form.get('phone', '')
            
            conn = get_db_connection()
            existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            
            if existing:
                flash('Email already registered.', 'error')
                return redirect(url_for('signup'))
            
            hashed_password = generate_password_hash(password)
            conn.execute('''
                INSERT INTO users (name, email, password, institution, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, hashed_password, institution, phone))
            conn.commit()
            
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()
            
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

@app.route('/')
@login_required
def dashboard():
    """Main dashboard"""
    conn = get_db_connection()
    
    stats = {
        'teachers': conn.execute('SELECT COUNT(*) as count FROM teachers WHERE user_id = ?', 
                                (session['user_id'],)).fetchone()['count'],
        'subjects': conn.execute('SELECT COUNT(*) as count FROM subjects WHERE user_id = ?', 
                                (session['user_id'],)).fetchone()['count'],
        'rooms': conn.execute('SELECT COUNT(*) as count FROM rooms WHERE user_id = ?', 
                             (session['user_id'],)).fetchone()['count'],
        'classes': conn.execute('SELECT COUNT(*) as count FROM classes WHERE user_id = ?', 
                               (session['user_id'],)).fetchone()['count'],
        'entries': conn.execute('SELECT COUNT(*) as count FROM timetable_entries WHERE user_id = ?', 
                               (session['user_id'],)).fetchone()['count']
    }
    
    # Recent activities
    recent_classes = conn.execute('''
        SELECT * FROM classes WHERE user_id = ? ORDER BY id DESC LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', stats=stats, recent_classes=recent_classes)

# ============================================================================
# TEACHERS MANAGEMENT
# ============================================================================

@app.route('/teachers')
@login_required
def teachers():
    """List all teachers"""
    conn = get_db_connection()
    teachers = conn.execute('''
        SELECT * FROM teachers WHERE user_id = ? ORDER BY name
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    """Add new teacher"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO teachers (name, email, phone, department, specialization,
                                     max_hours_per_day, max_hours_per_week, preferred_days, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['name'], request.form['email'], request.form['phone'],
                  request.form['department'], request.form['specialization'],
                  request.form['max_hours_per_day'], request.form['max_hours_per_week'],
                  request.form['preferred_days'], session['user_id']))
            conn.commit()
            conn.close()
            flash('Teacher added successfully!', 'success')
            return redirect(url_for('teachers'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('add_teacher.html')

@app.route('/teachers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(id):
    """Edit teacher"""
    conn = get_db_connection()
    if request.method == 'POST':
        try:
            conn.execute('''
                UPDATE teachers SET name=?, email=?, phone=?, department=?, specialization=?,
                                   max_hours_per_day=?, max_hours_per_week=?, preferred_days=?
                WHERE id=? AND user_id=?
            ''', (request.form['name'], request.form['email'], request.form['phone'],
                  request.form['department'], request.form['specialization'],
                  request.form['max_hours_per_day'], request.form['max_hours_per_week'],
                  request.form['preferred_days'], id, session['user_id']))
            conn.commit()
            flash('Teacher updated successfully!', 'success')
            return redirect(url_for('teachers'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    teacher = conn.execute('SELECT * FROM teachers WHERE id=? AND user_id=?', 
                          (id, session['user_id'])).fetchone()
    conn.close()
    return render_template('edit_teacher.html', teacher=teacher)

@app.route('/teachers/delete/<int:id>', methods=['POST'])
@login_required
def delete_teacher(id):
    """Delete teacher"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM teachers WHERE id=? AND user_id=?', (id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# SUBJECTS MANAGEMENT
# ============================================================================

@app.route('/subjects')
@login_required
def subjects():
    """List all subjects"""
    conn = get_db_connection()
    subjects = conn.execute('''
        SELECT * FROM subjects WHERE user_id = ? ORDER BY name
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('subjects.html', subjects=subjects)

@app.route('/subjects/add', methods=['GET', 'POST'])
@login_required
def add_subject():
    """Add new subject"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO subjects (name, code, department, credits, hours_per_week,
                                     theory_practical, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['name'], request.form['code'], request.form['department'],
                  request.form['credits'], request.form['hours_per_week'],
                  request.form['theory_practical'], session['user_id']))
            conn.commit()
            conn.close()
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('add_subject.html')

@app.route('/subjects/delete/<int:id>', methods=['POST'])
@login_required
def delete_subject(id):
    """Delete subject"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM subjects WHERE id=? AND user_id=?', (id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# ROOMS MANAGEMENT
# ============================================================================

@app.route('/rooms')
@login_required
def rooms():
    """List all rooms"""
    conn = get_db_connection()
    rooms = conn.execute('''
        SELECT * FROM rooms WHERE user_id = ? ORDER BY room_number
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('rooms.html', rooms=rooms)

@app.route('/rooms/add', methods=['GET', 'POST'])
@login_required
def add_room():
    """Add new room"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO rooms (name, room_number, capacity, room_type,
                                  has_projector, has_lab_equipment, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (request.form['name'], request.form['room_number'], request.form['capacity'],
                  request.form['room_type'], 1 if 'has_projector' in request.form else 0,
                  1 if 'has_lab_equipment' in request.form else 0, session['user_id']))
            conn.commit()
            conn.close()
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('add_room.html')

@app.route('/rooms/delete/<int:id>', methods=['POST'])
@login_required
def delete_room(id):
    """Delete room"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM rooms WHERE id=? AND user_id=?', (id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# CLASSES MANAGEMENT
# ============================================================================

@app.route('/classes')
@login_required
def classes():
    """List all classes"""
    conn = get_db_connection()
    classes = conn.execute('''
        SELECT * FROM classes WHERE user_id = ? ORDER BY name
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('classes.html', classes=classes)

@app.route('/classes/add', methods=['GET', 'POST'])
@login_required
def add_class():
    """Add new class"""
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO classes (name, semester, department, num_students, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (request.form['name'], request.form['semester'], request.form['department'],
                  request.form['num_students'], session['user_id']))
            conn.commit()
            conn.close()
            flash('Class added successfully!', 'success')
            return redirect(url_for('classes'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('add_class.html')

@app.route('/classes/delete/<int:id>', methods=['POST'])
@login_required
def delete_class(id):
    """Delete class"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM classes WHERE id=? AND user_id=?', (id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# TIMETABLE GENERATION & VIEWING
# ============================================================================

@app.route('/generate')
@login_required
def generate_timetable():
    """Generate timetable page"""
    conn = get_db_connection()
    classes = conn.execute('SELECT * FROM classes WHERE user_id=?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('generate.html', classes=classes)

@app.route('/api/generate-timetable', methods=['POST'])
@login_required
def api_generate_timetable():
    """Generate timetable using genetic algorithm"""
    try:
        data = request.get_json()
        class_id = data['class_id']
        
        conn = get_db_connection()
        
        # Get all required data
        teachers = conn.execute('SELECT * FROM teachers WHERE user_id=?', (session['user_id'],)).fetchall()
        subjects = conn.execute('SELECT * FROM subjects WHERE user_id=?', (session['user_id'],)).fetchall()
        rooms = conn.execute('SELECT * FROM rooms WHERE user_id=?', (session['user_id'],)).fetchall()
        time_slots = conn.execute('SELECT * FROM time_slots WHERE user_id=?', (session['user_id'],)).fetchall()
        
        # Simple timetable generation logic
        # Clear existing entries for this class
        conn.execute('DELETE FROM timetable_entries WHERE class_id=? AND user_id=?', 
                    (class_id, session['user_id']))
        
        # Generate timetable
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        slots_per_day = 6
        
        subject_idx = 0
        teacher_idx = 0
        room_idx = 0
        
        for day in days:
            day_slots = conn.execute('''
                SELECT * FROM time_slots WHERE day=? AND user_id=? ORDER BY slot_number
            ''', (day, session['user_id'])).fetchall()
            
            for slot in day_slots:
                if subject_idx < len(subjects):
                    subject = subjects[subject_idx]
                    teacher = teachers[teacher_idx % len(teachers)]
                    room = rooms[room_idx % len(rooms)]
                    
                    conn.execute('''
                        INSERT INTO timetable_entries 
                        (class_id, subject_id, teacher_id, room_id, time_slot_id, day, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (class_id, subject['id'], teacher['id'], room['id'], 
                          slot['id'], day, session['user_id']))
                    
                    subject_idx += 1
                    teacher_idx += 1
                    room_idx += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Timetable generated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/view/<int:class_id>')
@login_required
def view_timetable(class_id):
    """View timetable for a class"""
    conn = get_db_connection()
    
    class_info = conn.execute('SELECT * FROM classes WHERE id=? AND user_id=?', 
                             (class_id, session['user_id'])).fetchone()
    
    # Get timetable entries with all details
    entries = conn.execute('''
        SELECT 
            te.*,
            s.name as subject_name, s.code as subject_code,
            t.name as teacher_name,
            r.name as room_name, r.room_number,
            ts.day, ts.start_time, ts.end_time, ts.slot_number
        FROM timetable_entries te
        JOIN subjects s ON te.subject_id = s.id
        JOIN teachers t ON te.teacher_id = t.id
        JOIN rooms r ON te.room_id = r.id
        JOIN time_slots ts ON te.time_slot_id = ts.id
        WHERE te.class_id = ? AND te.user_id = ?
        ORDER BY ts.slot_number
    ''', (class_id, session['user_id'])).fetchall()
    
    # Organize entries by day and slot
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = conn.execute('''
        SELECT DISTINCT start_time, end_time, slot_number 
        FROM time_slots WHERE user_id=?
        ORDER BY slot_number
    ''', (session['user_id'],)).fetchall()
    
    # Create timetable grid
    timetable_grid = {}
    for day in days:
        timetable_grid[day] = {}
        for slot in time_slots:
            timetable_grid[day][slot['slot_number']] = None
    
    for entry in entries:
        timetable_grid[entry['day']][entry['slot_number']] = entry
    
    conn.close()
    
    return render_template('view_timetable.html', 
                         class_info=class_info, 
                         timetable_grid=timetable_grid,
                         days=days,
                         time_slots=time_slots)

@app.route('/teacher-timetable/<int:teacher_id>')
@login_required
def teacher_timetable(teacher_id):
    """View timetable for a specific teacher"""
    conn = get_db_connection()
    
    teacher = conn.execute('SELECT * FROM teachers WHERE id=? AND user_id=?', 
                          (teacher_id, session['user_id'])).fetchone()
    
    entries = conn.execute('''
        SELECT 
            te.*,
            s.name as subject_name,
            c.name as class_name,
            r.room_number,
            ts.day, ts.start_time, ts.end_time, ts.slot_number
        FROM timetable_entries te
        JOIN subjects s ON te.subject_id = s.id
        JOIN classes c ON te.class_id = c.id
        JOIN rooms r ON te.room_id = r.id
        JOIN time_slots ts ON te.time_slot_id = ts.id
        WHERE te.teacher_id = ? AND te.user_id = ?
        ORDER BY ts.slot_number
    ''', (teacher_id, session['user_id'])).fetchall()
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = conn.execute('''
        SELECT DISTINCT start_time, end_time, slot_number 
        FROM time_slots WHERE user_id=?
        ORDER BY slot_number
    ''', (session['user_id'],)).fetchall()
    
    timetable_grid = {}
    for day in days:
        timetable_grid[day] = {}
        for slot in time_slots:
            timetable_grid[day][slot['slot_number']] = None
    
    for entry in entries:
        timetable_grid[entry['day']][entry['slot_number']] = entry
    
    conn.close()
    
    return render_template('teacher_timetable.html',
                         teacher=teacher,
                         timetable_grid=timetable_grid,
                         days=days,
                         time_slots=time_slots)

# ============================================================================
# ANALYTICS & REPORTS
# ============================================================================

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard"""
    conn = get_db_connection()
    
    # Teacher workload
    teacher_workload = conn.execute('''
        SELECT 
            t.name,
            COUNT(te.id) as total_classes,
            COUNT(DISTINCT te.day) as days_teaching
        FROM teachers t
        LEFT JOIN timetable_entries te ON t.id = te.teacher_id
        WHERE t.user_id = ?
        GROUP BY t.id, t.name
        ORDER BY total_classes DESC
    ''', (session['user_id'],)).fetchall()
    
    # Room utilization
    room_utilization = conn.execute('''
        SELECT 
            r.room_number,
            r.name,
            COUNT(te.id) as times_used
        FROM rooms r
        LEFT JOIN timetable_entries te ON r.id = te.room_id
        WHERE r.user_id = ?
        GROUP BY r.id, r.room_number, r.name
        ORDER BY times_used DESC
    ''', (session['user_id'],)).fetchall()
    
    # Subject distribution
    subject_distribution = conn.execute('''
        SELECT 
            s.name,
            s.code,
            COUNT(te.id) as frequency
        FROM subjects s
        LEFT JOIN timetable_entries te ON s.id = te.subject_id
        WHERE s.user_id = ?
        GROUP BY s.id, s.name, s.code
        ORDER BY frequency DESC
    ''', (session['user_id'],)).fetchall()
    
    # Day-wise distribution
    day_distribution = conn.execute('''
        SELECT 
            day,
            COUNT(*) as classes_count
        FROM timetable_entries
        WHERE user_id = ?
        GROUP BY day
        ORDER BY 
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
            END
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('analytics.html',
                         teacher_workload=teacher_workload,
                         room_utilization=room_utilization,
                         subject_distribution=subject_distribution,
                         day_distribution=day_distribution)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/check-conflicts', methods=['POST'])
@login_required
def check_conflicts():
    """Check for scheduling conflicts"""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        room_id = data.get('room_id')
        time_slot_id = data.get('time_slot_id')
        day = data.get('day')
        
        conn = get_db_connection()
        
        conflicts = []
        
        # Check teacher conflict
        if teacher_id:
            teacher_conflict = conn.execute('''
                SELECT COUNT(*) as count FROM timetable_entries
                WHERE teacher_id = ? AND time_slot_id = ? AND day = ? AND user_id = ?
            ''', (teacher_id, time_slot_id, day, session['user_id'])).fetchone()
            
            if teacher_conflict['count'] > 0:
                conflicts.append('Teacher already scheduled at this time')
        
        # Check room conflict
        if room_id:
            room_conflict = conn.execute('''
                SELECT COUNT(*) as count FROM timetable_entries
                WHERE room_id = ? AND time_slot_id = ? AND day = ? AND user_id = ?
            ''', (room_id, time_slot_id, day, session['user_id'])).fetchone()
            
            if room_conflict['count'] > 0:
                conflicts.append('Room already booked at this time')
        
        conn.close()
        
        return jsonify({'conflicts': conflicts, 'has_conflict': len(conflicts) > 0})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/get-available-rooms', methods=['POST'])
@login_required
def get_available_rooms():
    """Get available rooms for a time slot"""
    try:
        data = request.get_json()
        time_slot_id = data.get('time_slot_id')
        day = data.get('day')
        
        conn = get_db_connection()
        
        available_rooms = conn.execute('''
            SELECT r.* FROM rooms r
            WHERE r.user_id = ? AND r.id NOT IN (
                SELECT room_id FROM timetable_entries
                WHERE time_slot_id = ? AND day = ? AND user_id = ?
            )
        ''', (session['user_id'], time_slot_id, day, session['user_id'])).fetchall()
        
        conn.close()
        
        return jsonify({'rooms': [dict(room) for room in available_rooms]})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/stats')
@login_required
def api_stats():
    """Get dashboard statistics"""
    conn = get_db_connection()
    
    stats = {
        'teachers': conn.execute('SELECT COUNT(*) as c FROM teachers WHERE user_id=?', 
                                (session['user_id'],)).fetchone()['c'],
        'subjects': conn.execute('SELECT COUNT(*) as c FROM subjects WHERE user_id=?', 
                                (session['user_id'],)).fetchone()['c'],
        'rooms': conn.execute('SELECT COUNT(*) as c FROM rooms WHERE user_id=?', 
                             (session['user_id'],)).fetchone()['c'],
        'classes': conn.execute('SELECT COUNT(*) as c FROM classes WHERE user_id=?', 
                               (session['user_id'],)).fetchone()['c'],
    }
    
    conn.close()
    return jsonify(stats)

# ============================================================================
# SETTINGS
# ============================================================================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            conn.execute('''
                UPDATE users SET name=?, institution=?, phone=?
                WHERE id=?
            ''', (request.form['name'], request.form['institution'],
                  request.form['phone'], session['user_id']))
            conn.commit()
            session['user_name'] = request.form['name']
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    
    stats = {
        'teachers': conn.execute('SELECT COUNT(*) as c FROM teachers WHERE user_id=?', 
                                (session['user_id'],)).fetchone()['c'],
        'subjects': conn.execute('SELECT COUNT(*) as c FROM subjects WHERE user_id=?', 
                                (session['user_id'],)).fetchone()['c'],
        'rooms': conn.execute('SELECT COUNT(*) as c FROM rooms WHERE user_id=?', 
                             (session['user_id'],)).fetchone()['c'],
        'classes': conn.execute('SELECT COUNT(*) as c FROM classes WHERE user_id=?', 
                               (session['user_id'],)).fetchone()['c'],
    }
    
    conn.close()
    
    return render_template('settings.html', user=user, stats=stats)

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password"""
    try:
        current = request.form['current_password']
        new = request.form['new_password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT password FROM users WHERE id=?', 
                          (session['user_id'],)).fetchone()
        
        if not check_password_hash(user['password'], current):
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('settings'))
        
        hashed = generate_password_hash(new)
        conn.execute('UPDATE users SET password=? WHERE id=?', 
                    (hashed, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Password changed successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)