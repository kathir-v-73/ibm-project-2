"""
TechKey Analysis - Model Tests
"""

import pytest
import os
import sys
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import Base, Student, Course, Enrollment, Grade, Attendance, Prediction
from src.database import get_session


class TestModels:
    """Test cases for database models."""
    
    @pytest.fixture
    def session(self):
        """Create a temporary database for testing."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_student_creation(self, session):
        """Test creating a student."""
        student = Student(
            student_id="TEST001",
            name="Test Student",
            email="test@university.edu",
            enrollment_date=date(2023, 9, 1)
        )
        
        session.add(student)
        session.commit()
        
        # Verify student was created
        saved_student = session.query(Student).filter_by(student_id="TEST001").first()
        assert saved_student is not None
        assert saved_student.name == "Test Student"
        assert saved_student.email == "test@university.edu"
    
    def test_student_grade_average(self, session):
        """Test student grade average calculation."""
        student = Student(student_id="S001", name="Test Student")
        session.add(student)
        session.commit()
        
        # Add grades
        grades = [
            Grade(student_id=student.id, assignment_name="Test 1", score=80.0),
            Grade(student_id=student.id, assignment_name="Test 2", score=90.0),
            Grade(student_id=student.id, assignment_name="Test 3", score=70.0)
        ]
        
        for grade in grades:
            session.add(grade)
        session.commit()
        
        # Test grade average calculation
        assert student.get_grade_average() == 80.0
    
    def test_student_attendance_rate(self, session):
        """Test student attendance rate calculation."""
        student = Student(student_id="S002", name="Test Student 2")
        session.add(student)
        session.commit()
        
        # Add attendance records
        attendance_records = [
            Attendance(student_id=student.id, date=date(2024, 1, 1), present=True),
            Attendance(student_id=student.id, date=date(2024, 1, 2), present=True),
            Attendance(student_id=student.id, date=date(2024, 1, 3), present=False),
            Attendance(student_id=student.id, date=date(2024, 1, 4), present=True)
        ]
        
        for record in attendance_records:
            session.add(record)
        session.commit()
        
        # Test attendance rate calculation
        assert student.get_attendance_rate() == 75.0
    
    def test_student_risk_level(self, session):
        """Test student risk level calculation."""
        # Test high risk
        student1 = Student(student_id="S003", name="High Risk Student")
        session.add(student1)
        
        grade1 = Grade(student_id=student1.id, assignment_name="Test", score=55.0)
        session.add(grade1)
        
        assert student1.get_risk_level() == "High Risk"
        
        # Test medium risk
        student2 = Student(student_id="S004", name="Medium Risk Student")
        session.add(student2)
        
        grade2 = Grade(student_id=student2.id, assignment_name="Test", score=65.0)
        session.add(grade2)
        
        assert student2.get_risk_level() == "Medium Risk"
        
        # Test low risk
        student3 = Student(student_id="S005", name="Low Risk Student")
        session.add(student3)
        
        grade3 = Grade(student_id=student3.id, assignment_name="Test", score=85.0)
        session.add(grade3)
        
        assert student3.get_risk_level() == "Low Risk"
        
        session.commit()
    
    def test_course_creation(self, session):
        """Test creating a course."""
        course = Course(
            name="Test Course",
            code="TEST101",
            description="A test course",
            credits=3
        )
        
        session.add(course)
        session.commit()
        
        saved_course = session.query(Course).filter_by(code="TEST101").first()
        assert saved_course is not None
        assert saved_course.name == "Test Course"
        assert saved_course.credits == 3
    
    def test_enrollment_creation(self, session):
        """Test creating an enrollment."""
        student = Student(student_id="S006", name="Enrollment Student")
        course = Course(name="Enrollment Course", code="ENRL101")
        
        session.add_all([student, course])
        session.commit()
        
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            enrollment_date=date(2024, 1, 1)
        )
        
        session.add(enrollment)
        session.commit()
        
        saved_enrollment = session.query(Enrollment).filter_by(
            student_id=student.id,
            course_id=course.id
        ).first()
        
        assert saved_enrollment is not None
        assert saved_enrollment.status == "Active"
    
    def test_grade_letter_grade(self, session):
        """Test grade letter grade conversion."""
        student = Student(student_id="S007", name="Grade Student")
        session.add(student)
        session.commit()
        
        # Test different grade ranges
        test_cases = [
            (95.0, 'A'),
            (85.0, 'B'),
            (75.0, 'C'),
            (65.0, 'D'),
            (55.0, 'F')
        ]
        
        for score, expected_letter in test_cases:
            grade = Grade(
                student_id=student.id,
                assignment_name=f"Test {score}",
                score=score
            )
            assert grade.get_letter_grade() == expected_letter
    
    def test_prediction_creation(self, session):
        """Test creating a prediction."""
        student = Student(student_id="S008", name="Prediction Student")
        session.add(student)
        session.commit()
        
        prediction = Prediction(
            student_id=student.id,
            prediction="High Risk",
            probability=0.85,
            model_version="1.0"
        )
        
        session.add(prediction)
        session.commit()
        
        saved_prediction = session.query(Prediction).filter_by(
            student_id=student.id
        ).first()
        
        assert saved_prediction is not None
        assert saved_prediction.prediction == "High Risk"
        assert saved_prediction.probability == 0.85


if __name__ == "__main__":
    pytest.main([__file__])