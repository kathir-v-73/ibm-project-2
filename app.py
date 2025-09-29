from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
import plotly.express as px
import plotly.utils
import json
import os
from datetime import datetime, timedelta
import io
import sqlite3

from src.models import db, User, Student, StudentFile, Notification, AnalyticsData
from src.database import init_db, add_student, delete_student, get_all_students, update_student
from src.database import import_students_from_csv, save_uploaded_file, delete_file, rename_file, get_all_files
from src.database import create_notification, send_notification, get_student_by_id
from src.predictor import predict_student_risk, update_all_student_risks
from src.notifier import send_email_notification, send_sms_notification

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize extensions
init_db(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def dashboard():
    students = get_all_students()
    total_students = len(students)
    
    # Calculate statistics
    high_risk_count = len([s for s in students if s.risk_level == 'High Risk'])
    avg_grade = sum([s.grade_average for s in students]) / total_students if total_students > 0 else 0
    avg_attendance = sum([s.attendance_rate for s in students]) / total_students if total_students > 0 else 0
    
    # Create charts
    risk_distribution = create_risk_distribution_chart(students)
    grade_distribution = create_grade_distribution_chart(students)
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         high_risk_count=high_risk_count,
                         avg_grade=avg_grade,
                         avg_attendance=avg_attendance,
                         risk_distribution=risk_distribution,
                         grade_distribution=grade_distribution,
                         students=students)

@app.route('/students')
@login_required
def students():
    students_list = get_all_students()
    return render_template('students.html', students=students_list)

@app.route('/student/<int:student_id>')
@login_required
def student_detail(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('students'))
    
    files = StudentFile.query.filter_by(student_id=student_id).all()
    return render_template('student_form.html', student=student, files=files)

@app.route('/api/students', methods=['POST'])
@login_required
def api_add_student():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'})
        
        success, message = add_student(data)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def api_update_student(student_id):
    try:
        data = request.get_json()
        success, message = update_student(student_id, data)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def api_delete_student(student_id):
    try:
        success, message = delete_student(student_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render_template('upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('upload.html')
        
        if file and file.filename.endswith('.csv'):
            try:
                # Save file temporarily
                temp_path = f"temp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
                file.save(temp_path)
                
                # Import students
                success, message = import_students_from_csv(temp_path)
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'error')
                
                return render_template('upload.html')
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return render_template('upload.html')
        else:
            flash('Please upload a CSV file', 'error')
            return render_template('upload.html')
    
    return render_template('upload.html')

@app.route('/analytics')
@login_required
def analytics():
    students = get_all_students()
    
    # Create various analytics charts
    risk_chart = create_risk_distribution_chart(students)
    attendance_chart = create_attendance_trend_chart(students)
    grade_chart = create_grade_distribution_chart(students)
    enrollment_chart = create_enrollment_trend_chart(students)
    
    return render_template('analytics.html',
                         risk_chart=risk_chart,
                         attendance_chart=attendance_chart,
                         grade_chart=grade_chart,
                         enrollment_chart=enrollment_chart)

@app.route('/files')
@login_required
def files_management():
    files = get_all_files()
    students = get_all_students()
    return render_template('files.html', files=files, students=students)

@app.route('/api/files', methods=['POST'])
@login_required
def api_upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file selected'})
        
        file = request.files['file']
        student_id = request.form.get('student_id', None)
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        success, message = save_uploaded_file(file, student_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def api_delete_file(file_id):
    try:
        success, message = delete_file(file_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/files/<int:file_id>/rename', methods=['PUT'])
@login_required
def api_rename_file(file_id):
    try:
        data = request.get_json()
        new_filename = data.get('new_filename')
        
        if not new_filename:
            return jsonify({'success': False, 'message': 'New filename required'})
        
        success, message = rename_file(file_id, new_filename)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/download/file/<int:file_id>')
@login_required
def download_file(file_id):
    try:
        file_record = StudentFile.query.get_or_404(file_id)
        return send_file(file_record.file_path, as_attachment=True, download_name=file_record.original_filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('files_management'))

@app.route('/notifications')
@login_required
def notifications():
    notifications_list = Notification.query.order_by(Notification.created_at.desc()).all()
    students = get_all_students()
    return render_template('notifications.html', notifications=notifications_list, students=students)

@app.route('/api/notifications', methods=['POST'])
@login_required
def api_create_notification():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        notification_type = data.get('type')
        message = data.get('message')
        
        if not all([student_id, notification_type, message]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        success, msg = create_notification(student_id, notification_type, message)
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/notifications/<int:notification_id>/send', methods=['POST'])
@login_required
def api_send_notification(notification_id):
    try:
        notification = Notification.query.get_or_404(notification_id)
        student = notification.student
        
        try:
            if notification.type == 'email' and student.email:
                success, message = send_email_notification(student.email, notification.message)
            elif notification.type == 'sms' and student.phone:
                success, message = send_sms_notification(student.phone, notification.message)
            else:
                return jsonify({'success': False, 'message': 'Invalid notification type or missing contact info'})
            
            if success:
                notification.status = 'sent'
                notification.sent_at = datetime.utcnow()
                db.session.commit()
                return jsonify({'success': True, 'message': 'Notification sent successfully'})
            else:
                notification.status = 'failed'
                db.session.commit()
                return jsonify({'success': False, 'message': message})
                
        except Exception as e:
            notification.status = 'failed'
            db.session.commit()
            return jsonify({'success': False, 'message': f'Failed to send notification: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/export/students')
@login_required
def export_students():
    try:
        students = get_all_students()
        
        # Create DataFrame
        data = []
        for student in students:
            data.append({
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'phone': student.phone,
                'address': student.address,
                'enrollment_date': student.enrollment_date,
                'grade_average': student.grade_average,
                'attendance_rate': student.attendance_rate,
                'risk_level': student.risk_level,
                'created_at': student.created_at
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Students', index=False)
        
        output.seek(0)
        
        return send_file(output, 
                        download_name=f'students_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx',
                        as_attachment=True,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/update_risks', methods=['POST'])
@login_required
def api_update_risks():
    try:
        update_all_student_risks()
        return jsonify({'success': True, 'message': 'Risk levels updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating risks: {str(e)}'})

# Chart creation functions
def create_risk_distribution_chart(students):
    try:
        risk_counts = {}
        for student in students:
            risk_level = student.risk_level or 'Unknown'
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        fig = px.pie(values=list(risk_counts.values()), 
                     names=list(risk_counts.keys()),
                     title='Student Risk Distribution',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        # Return empty chart on error
        fig = px.pie(values=[1], names=['No Data'], title='Risk Distribution - No Data Available')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_grade_distribution_chart(students):
    try:
        grades = [student.grade_average for student in students if student.grade_average is not None]
        if not grades:
            fig = px.histogram(title='Grade Distribution - No Data Available')
        else:
            fig = px.histogram(x=grades, 
                              title='Grade Distribution',
                              labels={'x': 'Grade Average', 'y': 'Count'},
                              nbins=20)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception:
        fig = px.histogram(title='Grade Distribution - Error Loading Data')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_attendance_trend_chart(students):
    try:
        attendance_rates = [student.attendance_rate for student in students if student.attendance_rate is not None]
        if not attendance_rates:
            fig = px.box(title='Attendance Distribution - No Data Available')
        else:
            fig = px.box(x=attendance_rates,
                        title='Attendance Rate Distribution',
                        labels={'x': 'Attendance Rate'})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception:
        fig = px.box(title='Attendance Distribution - Error Loading Data')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_enrollment_trend_chart(students):
    try:
        enrollment_dates = {}
        for student in students:
            if student.enrollment_date:
                year = student.enrollment_date.year
                enrollment_dates[year] = enrollment_dates.get(year, 0) + 1
        
        if not enrollment_dates:
            fig = px.bar(title='Enrollment Trend - No Data Available')
        else:
            years = sorted(enrollment_dates.keys())
            counts = [enrollment_dates[year] for year in years]
            
            fig = px.bar(x=years, y=counts,
                        title='Enrollment Trend by Year',
                        labels={'x': 'Year', 'y': 'Number of Students'})
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception:
        fig = px.bar(title='Enrollment Trend - Error Loading Data')
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        # In production, use proper password hashing like werkzeug.security.check_password_hash
        if user and user.password_hash == password:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create new user (in production, hash the password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password  # In production, use: generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Create default admin user if no users exist
    with app.app_context():
        if not User.query.first():
            admin_user = User(
                username='admin',
                email='admin@school.edu',
                password_hash='admin'  # Change this in production!
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)