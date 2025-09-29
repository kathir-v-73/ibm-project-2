"""
Initialize the database with enhanced dataset including grades and attendance
"""

import os
import sys
import pandas as pd
import random
from pathlib import Path
from datetime import datetime, date, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import init_db, get_session
from src.models import Student, Course, Grade, Attendance, Prediction, Notification

def load_csv_data():
    """Load data from the enhanced CSV file with grade and attendance percentages."""
    session = get_session()
    try:
        # Check if data already exists
        if session.query(Student).count() > 0:
            print("✅ Data already exists in database")
            return
        
        # Path to your CSV file
        csv_path = project_root / 'data' / 'sample_students.csv'
        
        if not csv_path.exists():
            print(f"❌ CSV file not found at {csv_path}")
            print("📁 Creating enhanced sample data instead...")
            create_enhanced_sample_data()
            return
        
        # Read CSV file
        print("📖 Loading enhanced data from CSV file...")
        df = pd.read_csv(csv_path)
        
        students_created = 0
        for _, row in df.iterrows():
            try:
                # Parse enrollment date
                if 'enrollment_date' in row and pd.notna(row['enrollment_date']):
                    try:
                        # Try different date formats
                        enrollment_date = datetime.strptime(str(row['enrollment_date']), '%Y-%m-%d').date()
                    except:
                        try:
                            enrollment_date = datetime.strptime(str(row['enrollment_date']), '%d.%m.%Y').date()
                        except:
                            enrollment_date = date.today()
                else:
                    enrollment_date = date.today()
                
                # Create student from CSV data
                student = Student(
                    student_id=str(row['student_id']),
                    name=row['name'],
                    email=row['email'],
                    phone=row.get('phone', ''),
                    enrollment_date=enrollment_date
                )
                session.add(student)
                session.flush()  # Get the student ID
                
                # Create academic records based on percentages
                create_student_academic_data(session, student.id, 
                                           row.get('grade_percentage', 75), 
                                           row.get('attendance_percentage', 85))
                
                students_created += 1
                
            except Exception as e:
                print(f"⚠️ Error creating student {row.get('student_id', 'unknown')}: {e}")
                continue
        
        session.commit()
        print(f"✅ Successfully loaded {students_created} students with academic records!")
        
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")
        session.rollback()
    finally:
        session.close()

def create_student_academic_data(session, student_id, grade_percentage, attendance_percentage):
    """Create detailed academic records for a student."""
    try:
        # Get or create courses
        courses = session.query(Course).all()
        if not courses:
            courses = [
                Course(name="Mathematics", code="MATH101", credits=4),
                Course(name="Computer Science", code="CS101", credits=3),
                Course(name="Physics", code="PHYS101", credits=4),
                Course(name="English Literature", code="ENG201", credits=3),
                Course(name="Data Structures", code="CS201", credits=3)
            ]
            for course in courses:
                session.add(course)
            session.commit()
            courses = session.query(Course).all()
        
        # Assignment types with weights
        assignment_types = [
            {"name": "Midterm Exam", "weight": 0.3},
            {"name": "Final Exam", "weight": 0.4},
            {"name": "Assignment 1", "weight": 0.1},
            {"name": "Assignment 2", "weight": 0.1},
            {"name": "Lab Work", "weight": 0.1}
        ]
        
        # Create grade records for each course
        for course in courses:
            for assignment in assignment_types:
                # Add some variation to grades based on the student's overall percentage
                variation = random.uniform(-5, 5)
                score = max(0, min(100, grade_percentage + variation))
                
                grade = Grade(
                    student_id=student_id,
                    course_id=course.id,
                    assignment_name=assignment["name"],
                    score=round(score, 1),
                    max_score=100,
                    weight=assignment["weight"],
                    grade_date=date.today() - timedelta(days=random.randint(1, 90))
                )
                session.add(grade)
            
            # Create attendance records (last 30 days)
            total_classes = 30
            present_classes = int((attendance_percentage / 100) * total_classes)
            
            # Mark present classes
            present_days = random.sample(range(total_classes), present_classes)
            for day in range(total_classes):
                record_date = date.today() - timedelta(days=day)
                present = day in present_days
                
                attendance = Attendance(
                    student_id=student_id,
                    course_id=course.id,
                    date=record_date,
                    present=present,
                    session_type="Lecture" if day % 3 != 0 else "Lab"
                )
                session.add(attendance)
        
        # Create risk prediction
        risk_level = "High Risk" if grade_percentage < 50 or attendance_percentage < 60 else \
                    "Medium Risk" if grade_percentage < 70 or attendance_percentage < 75 else "Low Risk"
        
        prediction = Prediction(
            student_id=student_id,
            prediction=risk_level,
            confidence=random.uniform(0.7, 0.95),
            created_at=datetime.utcnow()
        )
        session.add(prediction)
        
        # Create notifications for high-risk students
        if risk_level == "High Risk":
            student = session.query(Student).get(student_id)
            notification = Notification(
                student_id=student_id,
                message=f"High risk alert for {student.name}. Grades: {grade_percentage}%, Attendance: {attendance_percentage}%",
                priority="high",
                created_at=datetime.utcnow()
            )
            session.add(notification)
            
    except Exception as e:
        print(f"❌ Error creating academic data for student {student_id}: {e}")
        raise

def create_enhanced_sample_data():
    """Fallback: create enhanced sample data if CSV doesn't exist."""
    session = get_session()
    try:
        # Check if data already exists
        if session.query(Student).count() > 0:
            print("✅ Sample data already exists")
            return
        
        # Create enhanced sample students with realistic data
        students_data = [
            {"student_id": "3592310022", "name": "Kathir", "email": "vkathir07032006@gmail.com", "phone": "+91 7010636542", "grade": 80, "attendance": 75},
            {"student_id": "3592310023", "name": "Arun Kumar", "email": "arun.kumar@university.edu", "phone": "+91 9876543210", "grade": 85, "attendance": 92},
            {"student_id": "3592310024", "name": "Priya Sharma", "email": "priya.sharma@university.edu", "phone": "+91 8765432109", "grade": 92, "attendance": 88},
            # Add more students as needed...
        ]
        
        for data in students_data:
            student = Student(
                student_id=data["student_id"],
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                enrollment_date=date(2023, 9, 1)
            )
            session.add(student)
            session.flush()
            
            # Create academic records
            create_student_academic_data(session, student.id, data["grade"], data["attendance"])
        
        session.commit()
        print("✅ Enhanced sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Initializing TechKey Analysis Database with Enhanced Dataset...")
    init_db()
    load_csv_data()