"""
TechKey Analysis - Web Application Models
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='teacher')  # admin, teacher, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has specified role."""
        role_hierarchy = {
            'admin': ['admin', 'teacher', 'viewer'],
            'teacher': ['teacher', 'viewer'],
            'viewer': ['viewer']
        }
        return self.role in role_hierarchy.get(role_name, [])
    
    def __repr__(self):
        return f'<User {self.username}>'


# Import and extend the core models
from src.models import Student, Course, Enrollment, Grade, Attendance, Prediction, Notification

# Re-export all models
__all__ = [
    'db', 'User', 'Student', 'Course', 'Enrollment', 
    'Grade', 'Attendance', 'Prediction', 'Notification'
]