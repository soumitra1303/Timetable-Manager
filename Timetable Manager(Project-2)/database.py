import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
import random

DATABASE = 'timetable.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            institution TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            specialization TEXT,
            max_hours_per_day INTEGER DEFAULT 6,
            max_hours_per_week INTEGER DEFAULT 30,
            preferred_days TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Subjects table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            department TEXT,
            credits INTEGER DEFAULT 3,
            hours_per_week INTEGER DEFAULT 3,
            theory_practical TEXT DEFAULT 'Theory',
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Rooms table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_number TEXT UNIQUE NOT NULL,
            capacity INTEGER DEFAULT 60,
            room_type TEXT DEFAULT 'Classroom',
            has_projector BOOLEAN DEFAULT 1,
            has_lab_equipment BOOLEAN DEFAULT 0,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Classes/Sections table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT,
            department TEXT,
            num_students INTEGER DEFAULT 60,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Time slots table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            slot_number INTEGER,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Timetable entries table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS timetable_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            subject_id INTEGER,
            teacher_id INTEGER,
            room_id INTEGER,
            time_slot_id INTEGER,
            day TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (class_id) REFERENCES classes (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (time_slot_id) REFERENCES time_slots (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Teacher availability table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS teacher_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            day TEXT NOT NULL,
            time_slot_id INTEGER,
            is_available BOOLEAN DEFAULT 1,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (time_slot_id) REFERENCES time_slots (id)
        )
    ''')
    
    # Check if demo user exists
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    if user_count == 0:
        # Create demo admin user
        demo_password = generate_password_hash('admin123')
        conn.execute('''
            INSERT INTO users (name, email, password, role, institution)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin User', 'admin@timetable.com', demo_password, 'admin', 'Demo University'))
        conn.commit()
        
        admin_id = conn.execute('SELECT id FROM users WHERE email = ?', 
                               ('admin@timetable.com',)).fetchone()[0]
        
        print("=" * 70)
        print("✅ Demo admin user created!")
        print("=" * 70)
        print("Email:    admin@timetable.com")
        print("Password: admin123")
        print("=" * 70)
        
        # Add sample data
        add_sample_data(conn, admin_id)
    
    conn.close()

def add_sample_data(conn, user_id):
    """Add comprehensive sample data with realistic timetable entries"""
    
    # Sample Teachers (20 teachers)
    teachers = [
        ('Dr. Rajesh Kumar', 'rajesh@demo.com', '9876543210', 'Computer Science', 'Data Structures & Algorithms'),
        ('Prof. Priya Singh', 'priya@demo.com', '9876543211', 'Computer Science', 'Database Management Systems'),
        ('Dr. Amit Sharma', 'amit@demo.com', '9876543212', 'Computer Science', 'Operating Systems'),
        ('Prof. Sneha Patel', 'sneha@demo.com', '9876543213', 'Computer Science', 'Computer Networks'),
        ('Dr. Vikram Reddy', 'vikram@demo.com', '9876543214', 'Computer Science', 'Software Engineering'),
        ('Prof. Anita Desai', 'anita@demo.com', '9876543215', 'Mathematics', 'Discrete Mathematics'),
        ('Dr. Suresh Menon', 'suresh@demo.com', '9876543216', 'Computer Science', 'Web Technologies'),
        ('Prof. Kavita Iyer', 'kavita@demo.com', '9876543217', 'Computer Science', 'Machine Learning'),
        ('Dr. Arun Gupta', 'arun@demo.com', '9876543218', 'Computer Science', 'Artificial Intelligence'),
        ('Prof. Meera Nair', 'meera@demo.com', '9876543219', 'Computer Science', 'Cloud Computing'),
        ('Dr. Rahul Verma', 'rahul@demo.com', '9876543220', 'Computer Science', 'Cybersecurity'),
        ('Prof. Deepa Joshi', 'deepa@demo.com', '9876543221', 'Computer Science', 'Mobile App Development'),
        ('Dr. Karthik Raman', 'karthik@demo.com', '9876543222', 'Computer Science', 'Data Mining'),
        ('Prof. Shalini Kapoor', 'shalini@demo.com', '9876543223', 'Computer Science', 'Computer Graphics'),
        ('Dr. Manoj Tiwari', 'manoj@demo.com', '9876543224', 'Mathematics', 'Linear Algebra'),
        ('Prof. Nisha Agarwal', 'nisha@demo.com', '9876543225', 'Mathematics', 'Probability & Statistics'),
        ('Dr. Sandeep Bose', 'sandeep@demo.com', '9876543226', 'Computer Science', 'Compiler Design'),
        ('Prof. Ritu Malhotra', 'ritu@demo.com', '9876543227', 'Computer Science', 'Information Security'),
        ('Dr. Prakash Rao', 'prakash@demo.com', '9876543228', 'Computer Science', 'Blockchain Technology'),
        ('Prof. Lakshmi Iyer', 'lakshmi@demo.com', '9876543229', 'Computer Science', 'Internet of Things'),
    ]
    
    for teacher in teachers:
        conn.execute('''
            INSERT INTO teachers (name, email, phone, department, specialization, 
                                 max_hours_per_day, max_hours_per_week, preferred_days, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher[0], teacher[1], teacher[2], teacher[3], teacher[4], 6, 30, 
              'Monday,Tuesday,Wednesday,Thursday,Friday', user_id))
    
    # Sample Subjects (30 subjects including labs)
    subjects = [
        ('Data Structures & Algorithms', 'CS201', 'Computer Science', 4, 4, 'Theory'),
        ('Database Management Systems', 'CS202', 'Computer Science', 4, 4, 'Theory'),
        ('Operating Systems', 'CS203', 'Computer Science', 3, 3, 'Theory'),
        ('Computer Networks', 'CS204', 'Computer Science', 3, 3, 'Theory'),
        ('Software Engineering', 'CS205', 'Computer Science', 3, 3, 'Theory'),
        ('Discrete Mathematics', 'MA201', 'Mathematics', 3, 3, 'Theory'),
        ('Web Technologies', 'CS206', 'Computer Science', 3, 3, 'Theory'),
        ('Machine Learning', 'CS301', 'Computer Science', 4, 4, 'Theory'),
        ('Artificial Intelligence', 'CS302', 'Computer Science', 4, 4, 'Theory'),
        ('Cloud Computing', 'CS303', 'Computer Science', 3, 3, 'Theory'),
        ('Cybersecurity', 'CS304', 'Computer Science', 3, 3, 'Theory'),
        ('Mobile App Development', 'CS305', 'Computer Science', 3, 3, 'Theory'),
        ('Data Mining', 'CS306', 'Computer Science', 3, 3, 'Theory'),
        ('Computer Graphics', 'CS307', 'Computer Science', 3, 3, 'Theory'),
        ('Linear Algebra', 'MA202', 'Mathematics', 3, 3, 'Theory'),
        ('Probability & Statistics', 'MA203', 'Mathematics', 3, 3, 'Theory'),
        ('Compiler Design', 'CS401', 'Computer Science', 4, 4, 'Theory'),
        ('Information Security', 'CS402', 'Computer Science', 3, 3, 'Theory'),
        ('Blockchain Technology', 'CS403', 'Computer Science', 3, 3, 'Theory'),
        ('Internet of Things', 'CS404', 'Computer Science', 3, 3, 'Theory'),
        # Practical Labs
        ('Data Structures Lab', 'CS201L', 'Computer Science', 2, 2, 'Practical'),
        ('DBMS Lab', 'CS202L', 'Computer Science', 2, 2, 'Practical'),
        ('Operating Systems Lab', 'CS203L', 'Computer Science', 2, 2, 'Practical'),
        ('Computer Networks Lab', 'CS204L', 'Computer Science', 2, 2, 'Practical'),
        ('Web Technologies Lab', 'CS206L', 'Computer Science', 2, 2, 'Practical'),
        ('Machine Learning Lab', 'CS301L', 'Computer Science', 2, 2, 'Practical'),
        ('AI Lab', 'CS302L', 'Computer Science', 2, 2, 'Practical'),
        ('Mobile App Development Lab', 'CS305L', 'Computer Science', 2, 2, 'Practical'),
        ('Cybersecurity Lab', 'CS304L', 'Computer Science', 2, 2, 'Practical'),
        ('Computer Graphics Lab', 'CS307L', 'Computer Science', 2, 2, 'Practical'),
    ]
    
    for subject in subjects:
        conn.execute('''
            INSERT INTO subjects (name, code, department, credits, hours_per_week, 
                                 theory_practical, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (subject[0], subject[1], subject[2], subject[3], subject[4], subject[5], user_id))
    
    # Sample Rooms (25 rooms)
    rooms = [
        ('Main Lecture Hall 1', 'LH-101', 120, 'Lecture Hall', 1, 0),
        ('Main Lecture Hall 2', 'LH-102', 120, 'Lecture Hall', 1, 0),
        ('Main Lecture Hall 3', 'LH-103', 100, 'Lecture Hall', 1, 0),
        ('Classroom A', 'CR-201', 60, 'Classroom', 1, 0),
        ('Classroom B', 'CR-202', 60, 'Classroom', 1, 0),
        ('Classroom C', 'CR-203', 60, 'Classroom', 1, 0),
        ('Classroom D', 'CR-204', 60, 'Classroom', 1, 0),
        ('Classroom E', 'CR-205', 60, 'Classroom', 1, 0),
        ('Classroom F', 'CR-206', 60, 'Classroom', 1, 0),
        ('Computer Lab 1', 'LAB-301', 40, 'Lab', 1, 1),
        ('Computer Lab 2', 'LAB-302', 40, 'Lab', 1, 1),
        ('Computer Lab 3', 'LAB-303', 40, 'Lab', 1, 1),
        ('Computer Lab 4', 'LAB-304', 40, 'Lab', 1, 1),
        ('Computer Lab 5', 'LAB-305', 40, 'Lab', 1, 1),
        ('Computer Lab 6', 'LAB-306', 40, 'Lab', 1, 1),
        ('Seminar Hall 1', 'SH-401', 150, 'Seminar Hall', 1, 0),
        ('Seminar Hall 2', 'SH-402', 100, 'Seminar Hall', 1, 0),
        ('Tutorial Room 1', 'TR-501', 30, 'Tutorial Room', 1, 0),
        ('Tutorial Room 2', 'TR-502', 30, 'Tutorial Room', 1, 0),
        ('Tutorial Room 3', 'TR-503', 30, 'Tutorial Room', 1, 0),
        ('Smart Classroom 1', 'SC-601', 50, 'Smart Classroom', 1, 0),
        ('Smart Classroom 2', 'SC-602', 50, 'Smart Classroom', 1, 0),
        ('Workshop Lab', 'WS-701', 35, 'Workshop', 1, 1),
        ('Research Lab', 'RL-801', 25, 'Research Lab', 1, 1),
        ('Conference Room', 'CF-901', 40, 'Conference Room', 1, 0),
    ]
    
    for room in rooms:
        conn.execute('''
            INSERT INTO rooms (name, room_number, capacity, room_type, 
                              has_projector, has_lab_equipment, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (room[0], room[1], room[2], room[3], room[4], room[5], user_id))
    
    # Sample Classes (12 classes - 4 semesters with sections)
    classes = [
        ('CSE 3rd Semester A', 'Semester 3', 'Computer Science', 60),
        ('CSE 3rd Semester B', 'Semester 3', 'Computer Science', 60),
        ('CSE 3rd Semester C', 'Semester 3', 'Computer Science', 55),
        ('CSE 4th Semester A', 'Semester 4', 'Computer Science', 58),
        ('CSE 4th Semester B', 'Semester 4', 'Computer Science', 58),
        ('CSE 4th Semester C', 'Semester 4', 'Computer Science', 52),
        ('CSE 5th Semester A', 'Semester 5', 'Computer Science', 55),
        ('CSE 5th Semester B', 'Semester 5', 'Computer Science', 55),
        ('CSE 6th Semester A', 'Semester 6', 'Computer Science', 50),
        ('CSE 6th Semester B', 'Semester 6', 'Computer Science', 50),
        ('CSE 7th Semester A', 'Semester 7', 'Computer Science', 48),
        ('CSE 7th Semester B', 'Semester 7', 'Computer Science', 48),
    ]
    
    for cls in classes:
        conn.execute('''
            INSERT INTO classes (name, semester, department, num_students, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (cls[0], cls[1], cls[2], cls[3], user_id))
    
    # Sample Time Slots (Monday to Friday, 6 slots per day)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = [
        ('09:00 AM', '10:00 AM', 1),
        ('10:00 AM', '11:00 AM', 2),
        ('11:15 AM', '12:15 PM', 3),
        ('12:15 PM', '01:15 PM', 4),
        ('02:00 PM', '03:00 PM', 5),
        ('03:00 PM', '04:00 PM', 6),
    ]
    
    for day in days:
        for slot in time_slots:
            conn.execute('''
                INSERT INTO time_slots (day, start_time, end_time, slot_number, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (day, slot[0], slot[1], slot[2], user_id))
    
    conn.commit()
    
    # Generate realistic timetable entries
    generate_timetable_entries(conn, user_id, days, len(time_slots))
    
    print("✅ Sample data added:")
    print(f"   • {len(teachers)} Teachers")
    print(f"   • {len(subjects)} Subjects")
    print(f"   • {len(rooms)} Rooms")
    print(f"   • {len(classes)} Classes")
    print(f"   • {len(days) * len(time_slots)} Time Slots")
    print(f"   • Comprehensive Timetable Entries Generated")
    print("=" * 70)

def generate_timetable_entries(conn, user_id, days, slots_per_day):
    """Generate realistic timetable entries for all classes"""
    
    # Get all data
    classes = conn.execute('SELECT id, name, semester FROM classes').fetchall()
    subjects = conn.execute('SELECT id, name, theory_practical FROM subjects').fetchall()
    teachers = conn.execute('SELECT id FROM teachers').fetchall()
    rooms = conn.execute('SELECT id, room_type FROM rooms').fetchall()
    
    # Define subject assignments per semester
    semester_subjects = {
        'Semester 3': [1, 2, 3, 4, 6, 21, 22, 23, 24],  # IDs from subjects list
        'Semester 4': [5, 7, 8, 15, 25, 26, 27],
        'Semester 5': [9, 10, 11, 12, 28, 29],
        'Semester 6': [13, 14, 16, 30],
        'Semester 7': [17, 18, 19, 20],
    }
    
    # Create timetable for each class
    for cls in classes:
        class_id = cls[0]
        semester = cls[2]
        
        # Get subjects for this semester
        relevant_subject_ids = semester_subjects.get(semester, [1, 2, 3, 4])
        
        # Get time slots
        time_slots = conn.execute('''
            SELECT id, day, slot_number FROM time_slots 
            ORDER BY 
                CASE day 
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                END,
                slot_number
        ''').fetchall()
        
        # Track used time slots
        used_slots = set()
        
        # Assign subjects to time slots (avoiding slot 4 - lunch break most times)
        for day in days:
            day_slots = [ts for ts in time_slots if ts[1] == day]
            
            # Randomly assign 4-5 classes per day
            num_classes = random.randint(4, 5)
            selected_slots = random.sample([s for s in day_slots if s[2] != 4], 
                                          min(num_classes, len(day_slots)-1))
            
            for slot in selected_slots:
                # Pick a random subject for this semester
                subject_id = random.choice(relevant_subject_ids)
                subject = next(s for s in subjects if s[0] == subject_id)
                
                # Pick random teacher
                teacher_id = random.choice(teachers)[0]
                
                # Pick appropriate room based on subject type
                if subject[2] == 'Practical':
                    available_rooms = [r[0] for r in rooms if r[1] in ['Lab', 'Workshop']]
                else:
                    available_rooms = [r[0] for r in rooms if r[1] in ['Classroom', 'Lecture Hall', 'Smart Classroom']]
                
                room_id = random.choice(available_rooms) if available_rooms else rooms[0][0]
                
                # Insert timetable entry
                conn.execute('''
                    INSERT INTO timetable_entries 
                    (class_id, subject_id, teacher_id, room_id, time_slot_id, day, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (class_id, subject_id, teacher_id, room_id, slot[0], day, user_id))
    
    conn.commit()
    print("   • Timetable entries populated for all classes")

if __name__ == '__main__':
    init_db()
    print("✅ Timetable database setup complete!")