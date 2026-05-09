"""
Authentication module for SkillBridge
Handles user registration, login, logout, and session management
"""
from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from functools import wraps
from config import db_config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_db_connection():
    """Get a connection to the MySQL database (supports Aiven Cloud)."""
    try:
        # Build connection kwargs
        conn_kwargs = {
            'host': db_config.MYSQL_HOST,
            'user': db_config.MYSQL_USER,
            'password': db_config.MYSQL_PASSWORD,
            'database': db_config.MYSQL_DB,
            'port': db_config.MYSQL_PORT,
            'autocommit': True  # For session management
        }
        
        # Add SSL configuration if enabled (recommended for Aiven)
        if db_config.USE_SSL:
            import os
            if os.path.exists(db_config.SSL_CA_PATH):
                conn_kwargs['ssl_verify_cert'] = True
                conn_kwargs['ssl_verify_identity'] = True
                conn_kwargs['ssl_ca'] = db_config.SSL_CA_PATH
            else:
                # If CA file doesn't exist, use SSL without verification (less secure)
                conn_kwargs['ssl_disabled'] = False
        
        return mysql.connector.connect(**conn_kwargs)
    except mysql.connector.Error as err:
        if err.errno == 2003:
            raise Exception(f"Cannot connect to database at {db_config.MYSQL_HOST}:{db_config.MYSQL_PORT}. Check your connection parameters in .env")
        else:
            raise Exception(f"Database connection error: {err}")

def login_required(f):
    """Decorator to check if user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'warning')
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function

def generate_alias():
    """Generate a unique alias for a user."""
    import random
    import string
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    while True:
        random_hex = ''.join(random.choices(string.hexdigits[:16].lower(), k=4))
        alias = f'user_{random_hex}'
        
        cursor.execute('SELECT alias FROM users WHERE alias = %s', (alias,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return alias

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        student_number = request.form.get('student_number', '').strip()
        school = request.form.get('school', '').strip()
        year_of_study = request.form.get('year_of_study', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Client-side validation errors
        errors = []
        if not student_number:
            errors.append('Student number is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Server-side validation and insertion
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if student number already exists
            cursor.execute('SELECT user_id FROM users WHERE student_number = %s', (student_number,))
            if cursor.fetchone():
                flash('This student number is already registered.', 'danger')
                cursor.close()
                conn.close()
                return render_template('auth/register.html')
            
            # Generate unique alias
            alias = generate_alias()
            password_hash = generate_password_hash(password)
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (alias, student_number, password_hash, school, year_of_study)
                VALUES (%s, %s, %s, %s, %s)
            ''', (alias, student_number, password_hash, school, year_of_study))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect('/auth/login')
        except Exception as e:
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        student_number = request.form.get('student_number', '').strip()
        password = request.form.get('password', '')
        
        if not student_number or not password:
            flash('Invalid credentials', 'danger')
            return render_template('auth/login.html')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('SELECT user_id, password_hash FROM users WHERE student_number = %s', (student_number,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                flash('Login successful!', 'success')
                return redirect('/dashboard')
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/auth/login')

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """View user profile."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return render_template('auth/profile.html', user=user)
        else:
            flash('User not found.', 'danger')
            return redirect('/auth/logout')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect('/dashboard')

@auth_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    school = request.form.get('school', '').strip()
    year_of_study = request.form.get('year_of_study', '').strip()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET school = %s, year_of_study = %s
            WHERE user_id = %s
        ''', (school, year_of_study, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect('/auth/profile')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect('/auth/profile')
