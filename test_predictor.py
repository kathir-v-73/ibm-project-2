"""
TechKey Analysis - Predictor Tests
"""

import pytest
import numpy as np
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.predictor import prepare_training_data, prepare_prediction_data, create_prediction_pipeline
from src.models import Student, Grade, Attendance


class TestPredictor:
    """Test cases for predictor module."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        return session
    
    def test_prepare_training_data(self, mock_session):
        """Test training data preparation."""
        # Mock student data
        student1 = Mock()
        student1.id = 1
        student1.get_grade_average.return_value = 75.0
        student1.get_attendance_rate.return_value = 85.0
        student1.enrollments = [Mock(), Mock()]  # 2 courses
        
        student2 = Mock()
        student2.id = 2
        student2.get_grade_average.return_value = 45.0
        student2.get_attendance_rate.return_value = 60.0
        student2.enrollments = [Mock()]  # 1 course
        
        # Mock grade queries
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [Mock(score=80.0), Mock(score=70.0)],  # Recent grades for student1
            [Mock(score=75.0)],  # Older grades for student1
            [Mock(score=40.0), Mock(score=50.0)],  # Recent grades for student2
            [Mock(score=45.0)]  # Older grades for student2
        ]
        
        # Mock grade count queries
        grade_count_mock = Mock()
        grade_count_mock.count.return_value = 5  # Total assignments
        mock_session.query.return_value.filter_by.return_value = grade_count_mock
        
        mock_session.query.return_value.all.return_value = [student1, student2]
        
        # Test data preparation
        X, y, feature_names = prepare_training_data(mock_session)
        
        # Verify results
        assert X.shape[0] == 2  # Two students
        assert X.shape[1] == 6  # Six features
        assert len(y) == 2
        assert len(feature_names) == 6
        
        # Student1 should be low risk (grade >= 60 and attendance >= 75)
        # Student2 should be high risk (grade < 60 or attendance < 75)
        assert y[0] == 0  # Low risk
        assert y[1] == 1  # High risk
    
    def test_prepare_prediction_data(self, mock_session):
        """Test prediction data preparation for single student."""
        # Mock student
        student = Mock()
        student.id = 1
        student.get_grade_average.return_value = 80.0
        student.get_attendance_rate.return_value = 90.0
        student.enrollments = [Mock(), Mock(), Mock()]  # 3 courses
        
        # Mock grade queries
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [Mock(score=85.0), Mock(score=75.0)],  # Recent grades
            [Mock(score=80.0)]  # Older grades
        ]
        
        # Mock grade count query
        grade_count_mock = Mock()
        grade_count_mock.count.return_value = 10  # Total assignments
        completed_grades = [Mock(score=85.0), Mock(score=75.0), Mock(score=80.0)]
        student.grades = completed_grades
        mock_session.query.return_value.filter_by.return_value = grade_count_mock
        
        # Test data preparation
        X, features = prepare_prediction_data(student, mock_session)
        
        # Verify results
        assert X is not None
        assert len(X) == 6  # Six features
        assert features['grade_average'] == 80.0
        assert features['attendance_rate'] == 90.0
        assert features['course_count'] == 3
        assert features['missing_assignments'] == 7  # 10 total - 3 completed
    
    def test_create_prediction_pipeline(self):
        """Test pipeline creation."""
        pipeline = create_prediction_pipeline()
        
        # Verify pipeline structure
        assert hasattr(pipeline, 'steps')
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0][0] == 'scaler'
        assert pipeline.steps[1][0] == 'classifier'
    
    @patch('src.predictor.joblib.load')
    def test_predict_student_risk(self, mock_joblib, mock_session):
        """Test student risk prediction."""
        from src.predictor import predict_student_risk
        
        # Mock model
        mock_model = Mock()
        mock_model.predict_proba.return_value = [[0.3, 0.7]]  # 70% probability of high risk
        mock_model.predict.return_value = [1]  # High risk prediction
        mock_joblib.return_value = mock_model
        
        # Mock student
        student = Mock()
        student.id = 1
        student.name = "Test Student"
        student.get_grade_average.return_value = 55.0
        student.get_attendance_rate.return_value = 65.0
        student.enrollments = [Mock()]
        
        # Mock grade queries
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [Mock(score=50.0), Mock(score=60.0)],  # Recent grades
            [Mock(score=55.0)]  # Older grades
        ]
        
        # Mock grade count query
        grade_count_mock = Mock()
        grade_count_mock.count.return_value = 8
        completed_grades = [Mock(score=50.0), Mock(score=60.0), Mock(score=55.0)]
        student.grades = completed_grades
        mock_session.query.return_value.filter_by.return_value = grade_count_mock
        
        # Test prediction
        result = predict_student_risk(student, mock_session)
        
        # Verify results
        assert result is not None
        assert result['risk_level'] == 'High Risk'
        assert result['probability'] == 0.7
        assert result['student_name'] == 'Test Student'
        assert 'features' in result
    
    def test_prediction_with_insufficient_data(self, mock_session):
        """Test prediction with insufficient student data."""
        # Mock student with no grades
        student = Mock()
        student.id = 1
        student.get_grade_average.return_value = 0.0
        student.get_attendance_rate.return_value = 0.0
        student.enrollments = []
        student.grades = []
        
        # Mock empty grade queries
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        # Mock grade count query
        grade_count_mock = Mock()
        grade_count_mock.count.return_value = 0
        mock_session.query.return_value.filter_by.return_value = grade_count_mock
        
        # Test data preparation
        X, features = prepare_prediction_data(student, mock_session)
        
        # Should return valid data with zeros
        assert X is not None
        assert features['grade_average'] == 0.0
        assert features['attendance_rate'] == 0.0
        assert features['course_count'] == 0
        assert features['missing_assignments'] == 0


if __name__ == "__main__":
    pytest.main([__file__])