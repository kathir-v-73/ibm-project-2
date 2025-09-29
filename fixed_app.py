"""
TechKey Analysis - Complete Fixed Application
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import io

# Setup paths
project_root = Path(__file__).parent
instance_dir = project_root / 'instance'
web_dir = project_root / 'web'
templates_dir = web_dir / 'templates'
static_dir = web_dir / 'static'

# Create directories
instance_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

# Add to path
sys.path.insert(0, str(project_root))

# Database path
DATABASE_PATH = instance_dir / 'app.db'
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

app = Flask(__name__, 
            template_folder=str(templates_dir),
            static_folder=str(static_dir))

app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Simple User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='admin')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html',
                         total_students=15,
                         high_risk=3,
                         avg_grade=75.5,
                         avg_attendance=82.3)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/students')
@login_required
def students():
    return render_template('students.html')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

# Initialize database and create admin user
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created: admin / admin123")
    
    print("✅ Database initialized!")

if __name__ == '__main__':
    print("🚀 Starting TechKey Analysis...")
    print("📍 http://localhost:5000")
    print("🔑 admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)