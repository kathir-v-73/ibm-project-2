"""
TechKey Analysis - Web Application Tests
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from flask import url_for

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web.app import create_app
from web.models import db, User


class TestWebApp:
    """Test cases for web application."""
    
    @pytest.fixture
    def app(self):
        """Create and configure a Flask app for testing."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def auth_client(self, client):
        """Create an authenticated test client."""
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            role='teacher'
        )
        user.set_password('testpass')
        
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        return client
    
    def test_home_redirect(self, client):
        """Test home page redirects to login when not authenticated."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_login_page(self, client):
        """Test login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'TechKey Analysis' in response.data
        assert b'Sign in to your account' in response.data
    
    def test_successful_login(self, client):
        """Test successful user login."""
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            role='teacher'
        )
        user.set_password('testpass')
        
        db.session.add(user)
        db.session.commit()
        
        # Login
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard after successful login
    
    def test_failed_login(self, client):
        """Test failed login attempt."""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_dashboard_authenticated(self, auth_client):
        """Test dashboard access when authenticated."""
        response = auth_client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_students_page(self, auth_client):
        """Test students page access."""
        response = auth_client.get('/students')
        assert response.status_code == 200
        assert b'Student Management' in response.data
    
    def test_analytics_page(self, auth_client):
        """Test analytics page access."""
        response = auth_client.get('/analytics')
        assert response.status_code == 200
        assert b'Analytics Dashboard' in response.data
    
    def test_notifications_page(self, auth_client):
        """Test notifications page access."""
        response = auth_client.get('/notifications')
        assert response.status_code == 200
        assert b'Notifications' in response.data
    
    def test_api_students(self, auth_client):
        """Test students API endpoint."""
        response = auth_client.get('/api/students')
        assert response.status_code == 200
        # Should return JSON array
        assert response.is_json
    
    def test_api_predictions(self, auth_client):
        """Test predictions API endpoint."""
        response = auth_client.get('/api/predictions')
        assert response.status_code == 200
        assert response.is_json
    
    def test_export_students(self, auth_client):
        """Test students export functionality."""
        response = auth_client.get('/export/students')
        assert response.status_code == 200
        # Should return CSV file
        assert 'text/csv' in response.content_type
    
    def test_logout(self, auth_client):
        """Test user logout."""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
        assert b'Sign in to your account' in response.data
    
    def test_user_creation(self, app):
        """Test user creation and password hashing."""
        with app.app_context():
            user = User(
                username='newuser',
                email='new@example.com',
                role='viewer'
            )
            user.set_password('securepassword')
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            saved_user = User.query.filter_by(username='newuser').first()
            assert saved_user is not None
            assert saved_user.check_password('securepassword')
            assert not saved_user.check_password('wrongpassword')
            assert saved_user.has_role('viewer')
            assert not saved_user.has_role('admin')
    
    def test_admin_permissions(self, app):
        """Test user role permissions."""
        with app.app_context():
            admin = User(username='admin', role='admin')
            teacher = User(username='teacher', role='teacher')
            viewer = User(username='viewer', role='viewer')
            
            # Admin should have all permissions
            assert admin.has_role('admin')
            assert admin.has_role('teacher')
            assert admin.has_role('viewer')
            
            # Teacher should have teacher and viewer permissions
            assert not teacher.has_role('admin')
            assert teacher.has_role('teacher')
            assert teacher.has_role('viewer')
            
            # Viewer should only have viewer permissions
            assert not viewer.has_role('admin')
            assert not viewer.has_role('teacher')
            assert viewer.has_role('viewer')


if __name__ == "__main__":
    pytest.main([__file__])