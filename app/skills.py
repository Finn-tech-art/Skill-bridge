"""
Skills module for SkillBridge
Handles skill listing, browsing, and search functionality
"""
from flask import Blueprint, render_template, request, redirect, session, flash
from app.auth import login_required, get_db_connection
import mysql.connector

skills_bp = Blueprint('skills', __name__, url_prefix='/skills')

@skills_bp.route('/my', methods=['GET'])
@login_required
def my_skills():
    """Display skills offered and wanted by current user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM skills
            WHERE user_id = %s
            ORDER BY skill_type, created_at DESC
        ''', (session['user_id'],))
        
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Separate offered and wanted skills
        offered_skills = [s for s in skills if s['skill_type'] == 'offer']
        wanted_skills = [s for s in skills if s['skill_type'] == 'want']
        
        return render_template('skills/my_skills.html', 
                             offered_skills=offered_skills,
                             wanted_skills=wanted_skills)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect('/dashboard')

@skills_bp.route('/add', methods=['POST'])
@login_required
def add_skill():
    """Add a new skill."""
    skill_name = request.form.get('skill_name', '').strip()
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    skill_type = request.form.get('skill_type', '').strip()
    
    errors = []
    if not skill_name:
        errors.append('Skill name is required.')
    if not category:
        errors.append('Category is required.')
    if not skill_type or skill_type not in ['offer', 'want']:
        errors.append('Valid skill type is required.')
    if len(description) > 200:
        errors.append('Description must be 200 characters or less.')
    
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect('/skills/my')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO skills (user_id, skill_name, category, description, skill_type)
            VALUES (%s, %s, %s, %s, %s)
        ''', (session['user_id'], skill_name, category, description, skill_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Skill added successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect('/skills/my')

@skills_bp.route('/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    """Delete a skill."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify skill belongs to current user
        cursor.execute('SELECT user_id FROM skills WHERE skill_id = %s', (skill_id,))
        skill = cursor.fetchone()
        
        if not skill:
            cursor.close()
            conn.close()
            return 'Skill not found', 404
        
        if skill['user_id'] != session['user_id']:
            cursor.close()
            conn.close()
            return 'Unauthorized', 403
        
        cursor.execute('DELETE FROM skills WHERE skill_id = %s', (skill_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Skill deleted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect('/skills/my')

@skills_bp.route('/browse', methods=['GET'])
@login_required
def browse():
    """Browse and search all skills."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    skill_type = request.args.get('type', '').strip()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build dynamic query
        sql = '''
            SELECT s.*, u.alias, u.reputation_score
            FROM skills s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.user_id != %s
        '''
        params = [session['user_id']]
        
        if query:
            sql += ' AND (s.skill_name LIKE %s OR s.description LIKE %s)'
            params.extend([f'%{query}%', f'%{query}%'])
        
        if category:
            sql += ' AND s.category = %s'
            params.append(category)
        
        if skill_type:
            sql += ' AND s.skill_type = %s'
            params.append(skill_type)
        
        sql += ' ORDER BY s.created_at DESC'
        
        cursor.execute(sql, params)
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('skills/browse.html', skills=skills)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect('/dashboard')

@skills_bp.route('/<int:skill_id>', methods=['GET'])
@login_required
def skill_detail(skill_id):
    """View detail of a single skill."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT s.*, u.alias, u.reputation_score
            FROM skills s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.skill_id = %s
        ''', (skill_id,))
        
        skill = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not skill:
            flash('Skill not found.', 'danger')
            return redirect('/skills/browse')
        
        return render_template('skills/skill_detail.html', skill=skill)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect('/skills/browse')
