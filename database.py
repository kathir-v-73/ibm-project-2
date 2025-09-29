from .models import db, Student, StudentFile, Notification, AnalyticsData, User
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import datetime
import os

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

def add_student(student_data):
    try:
        # Check if student already exists
        existing_student = Student.query.filter_by(student_id=student_data['student_id']).first()
        if existing_student:
            return False, "Student ID already exists"
        
        student = Student(
            student_id=student_data['student_id'],
            name=student_data['name'],
            email=student_data['email'],
            phone=student_data.get('phone'),
            address=student_data.get('address'),
            enrollment_date=student_data.get('enrollment_date')
        )
        db.session.add(student)
        db.session.commit()
        return True, "Student added successfully"
    except IntegrityError as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"
    except Exception as e:
        db.session.rollback()
        return False, f"Error: {str(e)}"

def delete_student(student_id):
    try:
        student = Student.query.filter_by(id=student_id).first()
        if student:
            # Delete associated files and notifications
            StudentFile.query.filter_by(student_id=student_id).delete()
            Notification.query.filter_by(student_id=student_id).delete()
            
            db.session.delete(student)
            db.session.commit()
            return True, "Student deleted successfully"
        return False, "Student not found"
    except Exception as e:
        db.session.rollback()
        return False, f"Error: {str(e)}"

def get_all_students():
    return Student.query.all()

def get_student_by_id(student_id):
    return Student.query.filter_by(id=student_id).first()

def update_student(student_id, update_data):
    try:
        student = Student.query.filter_by(id=student_id).first()
        if student:
            for key, value in update_data.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            student.updated_at = datetime.utcnow()
            db.session.commit()
            return True, "Student updated successfully"
        return False, "Student not found"
    except Exception as e:
        db.session.rollback()
        return False, f"Error: {str(e)}"

def import_students_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        required_columns = ['student_id', 'name', 'email']
        
        # Validate required columns
        if not all(col in df.columns for col in required_columns):
            return False, f"Missing required columns. Required: {required_columns}"
        
        success_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            student_data = {
                'student_id': str(row['student_id']).strip(),
                'name': str(row['name']).strip(),
                'email': str(row['email']).strip(),
                'phone': str(row['phone']).strip() if 'phone' in row and pd.notna(row['phone']) else None,
                'enrollment_date': datetime.strptime(row['enrollment_date'], '%Y-%m-%d').date() if 'enrollment_date' in row and pd.notna(row['enrollment_date']) else None
            }
            
            success, message = add_student(student_data)
            if success:
                success_count += 1
            else:
                error_messages.append(f"Row {index + 2}: {message}")
        
        return True, f"Imported {success_count} students. Errors: {len(error_messages)}"
    
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"

def save_uploaded_file(file, student_id=None):
    try:
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        student_file = StudentFile(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type,
            student_id=student_id
        )
        
        db.session.add(student_file)
        db.session.commit()
        return True, "File uploaded successfully"
    except Exception as e:
        return False, f"Error uploading file: {str(e)}"

def delete_file(file_id):
    try:
        file_record = StudentFile.query.filter_by(id=file_id).first()
        if file_record:
            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Delete database record
            db.session.delete(file_record)
            db.session.commit()
            return True, "File deleted successfully"
        return False, "File not found"
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting file: {str(e)}"

def rename_file(file_id, new_filename):
    try:
        file_record = StudentFile.query.filter_by(id=file_id).first()
        if file_record:
            # Rename physical file
            old_path = file_record.file_path
            directory = os.path.dirname(old_path)
            new_path = os.path.join(directory, new_filename)
            
            os.rename(old_path, new_path)
            
            # Update database record
            file_record.filename = new_filename
            file_record.original_filename = new_filename
            file_record.file_path = new_path
            db.session.commit()
            return True, "File renamed successfully"
        return False, "File not found"
    except Exception as e:
        db.session.rollback()
        return False, f"Error renaming file: {str(e)}"

def get_all_files():
    return StudentFile.query.all()

def create_notification(student_id, notification_type, message):
    try:
        notification = Notification(
            student_id=student_id,
            type=notification_type,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        return True, "Notification created successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating notification: {str(e)}"

def send_notification(notification_id):
    try:
        notification = Notification.query.filter_by(id=notification_id).first()
        if notification:
            # Here you would integrate with your email/SMS service
            # For now, we'll just mark it as sent
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
            db.session.commit()
            return True, "Notification sent successfully"
        return False, "Notification not found"
    except Exception as e:
        db.session.rollback()
        return False, f"Error sending notification: {str(e)}"