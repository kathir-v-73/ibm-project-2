"""
TechKey Analysis - Web Authentication
"""

from flask_login import LoginManager, UserMixin
from flask import current_app
from .models import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_login(app):
    """Initialize login manager with the app."""
    login_manager.init_app(app)