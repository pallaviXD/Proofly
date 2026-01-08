"""
Proofly - Proof-of-Learning Tracker
Backend: Python Flask with SQLite
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'proofly-secret-key-change-in-production'
CORS(app, supports_credentials=True)

DATABASE = 'proofly.db'

# ============== DATABASE SETUP ==============

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Skills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            public_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Learning entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_spent INTEGER NOT NULL,
            what_studied TEXT NOT NULL,
            key_takeaway TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# ============== AUTH DECORATOR ==============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============== ROUTES ==============

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# ============== AUTH API ==============

@app.route('/api/signup', methods=['POST'])
def signup():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'message': 'Account created successfully', 'user': {'id': user_id, 'username': username}}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Login successful', 'user': {'id': user['id'], 'username': user['username']}})
    
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    if 'user_id' in session:
        return jsonify({'user': {'id': session['user_id'], 'username': session['username']}})
    return jsonify({'user': None})

# ============== SKILLS API ==============

@app.route('/api/skills', methods=['GET'])
@login_required
def get_skills():
    """Get all skills for current user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, 
               COALESCE(SUM(e.time_spent), 0) as total_time,
               COUNT(e.id) as entry_count
        FROM skills s
        LEFT JOIN entries e ON s.id = e.skill_id
        WHERE s.user_id = ?
        GROUP BY s.id
        ORDER BY s.created_at DESC
    ''', (session['user_id'],))
    skills = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'skills': skills})

@app.route('/api/skills', methods=['POST'])
@login_required
def create_skill():
    """Create a new skill"""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    import uuid
    public_id = str(uuid.uuid4())[:8]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO skills (user_id, name, public_id) VALUES (?, ?, ?)',
        (session['user_id'], name, public_id)
    )
    conn.commit()
    skill_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'message': 'Skill created', 'skill': {'id': skill_id, 'name': name, 'public_id': public_id}}), 201

@app.route('/api/skills/<int:skill_id>', methods=['DELETE'])
@login_required
def delete_skill(skill_id):
    """Delete a skill"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM skills WHERE id = ? AND user_id = ?', (skill_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Skill deleted'})

# ============== ENTRIES API ==============

@app.route('/api/skills/<int:skill_id>/entries', methods=['GET'])
@login_required
def get_entries(skill_id):
    """Get all entries for a skill"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify skill belongs to user
    cursor.execute('SELECT * FROM skills WHERE id = ? AND user_id = ?', (skill_id, session['user_id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Skill not found'}), 404
    
    cursor.execute('SELECT * FROM entries WHERE skill_id = ? ORDER BY date DESC, created_at DESC', (skill_id,))
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'entries': entries})

@app.route('/api/skills/<int:skill_id>/entries', methods=['POST'])
@login_required
def create_entry(skill_id):
    """Create a new learning entry"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify skill belongs to user
    cursor.execute('SELECT * FROM skills WHERE id = ? AND user_id = ?', (skill_id, session['user_id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Skill not found'}), 404
    
    data = request.get_json()
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    time_spent = data.get('time_spent', 0)
    what_studied = data.get('what_studied', '').strip()
    key_takeaway = data.get('key_takeaway', '').strip()
    
    if not what_studied or not key_takeaway:
        conn.close()
        return jsonify({'error': 'All fields are required'}), 400
    
    cursor.execute(
        'INSERT INTO entries (skill_id, date, time_spent, what_studied, key_takeaway) VALUES (?, ?, ?, ?, ?)',
        (skill_id, date, time_spent, what_studied, key_takeaway)
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'message': 'Entry added', 'entry_id': entry_id}), 201

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_entry(entry_id):
    """Delete an entry"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM entries WHERE id = ? AND skill_id IN (
            SELECT id FROM skills WHERE user_id = ?
        )
    ''', (entry_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Entry deleted'})

# ============== PUBLIC PROOF PAGE API ==============

@app.route('/api/proof/<public_id>', methods=['GET'])
def get_proof(public_id):
    """Get public proof page data (no auth required)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, u.username 
        FROM skills s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.public_id = ?
    ''', (public_id,))
    skill = cursor.fetchone()
    
    if not skill:
        conn.close()
        return jsonify({'error': 'Proof page not found'}), 404
    
    cursor.execute('SELECT * FROM entries WHERE skill_id = ? ORDER BY date ASC', (skill['id'],))
    entries = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT SUM(time_spent) as total FROM entries WHERE skill_id = ?', (skill['id'],))
    total = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    return jsonify({
        'skill': {
            'name': skill['name'],
            'username': skill['username'],
            'created_at': skill['created_at']
        },
        'total_time': total,
        'entries': entries
    })

# ============== MAIN ==============

if __name__ == '__main__':
    init_db()
    print("🚀 Proofly is running at http://localhost:5000")
    app.run(debug=True, port=5000)
