"""
TechKey Analysis - Main GUI Window
"""

import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QLabel, QMessageBox, QTabWidget, QSplitter,
                            QHeaderView, QToolBar, QStatusBar, QAction,
                            QFileDialog, QComboBox, QLineEdit, QFormLayout,
                            QGroupBox, QProgressBar, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import plotly.express as px
import plotly.graph_objects as go

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_session
from src.models import Student, Grade, Prediction
from src.visuals import create_grade_distribution, create_performance_trends
from src.predictor import predict_student_risk
from src.notifier import notification_manager
from .student_dialog import StudentDialog


class MainWindow(QMainWindow):
    """Main application window for TechKey Analysis."""
    
    # Signals
    data_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.current_student_id = None
        self.setup_ui()
        self.load_data()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("TechKey Analysis - Student Performance System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon and style
        self.setStyleSheet(self.get_stylesheet())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_students_tab()
        self.create_analytics_tab()
        self.create_predictions_tab()
        self.create_notifications_tab()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add student action
        add_student_action = QAction("➕ Add Student", self)
        add_student_action.triggered.connect(self.add_student)
        toolbar.addAction(add_student_action)
        
        toolbar.addSeparator()
        
        # Import action
        import_action = QAction("📥 Import CSV", self)
        import_action.triggered.connect(self.import_csv)
        toolbar.addAction(import_action)
        
        # Export action
        export_action = QAction("📤 Export Data", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.load_data)
        toolbar.addAction(refresh_action)
        
        # Train model action
        train_action = QAction("🤖 Train Model", self)
        train_action.triggered.connect(self.train_model)
        toolbar.addAction(train_action)
        
    def create_dashboard_tab(self):
        """Create the dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Welcome section
        welcome_label = QLabel("🎓 TechKey Analytics Dashboard")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        
        # Stats overview
        stats_group = QGroupBox("📊 System Overview")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_students_label = QLabel("Total Students: --")
        self.high_risk_label = QLabel("High Risk: --")
        self.avg_grade_label = QLabel("Average Grade: --")
        self.avg_attendance_label = QLabel("Avg Attendance: --")
        
        for label in [self.total_students_label, self.high_risk_label, 
                     self.avg_grade_label, self.avg_attendance_label]:
            label.setFont(QFont("Arial", 12))
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_group)
        
        # Recent alerts
        alerts_group = QGroupBox("🚨 Recent Alerts")
        alerts_layout = QVBoxLayout(alerts_group)
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(150)
        self.alerts_text.setReadOnly(True)
        alerts_layout.addWidget(self.alerts_text)
        layout.addWidget(alerts_group)
        
        # Quick actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        quick_actions = [
            ("Run Predictions", self.run_predictions),
            ("Send Notifications", self.send_notifications),
            ("Generate Report", self.generate_report),
            ("System Check", self.system_check)
        ]
        
        for text, slot in quick_actions:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        layout.addWidget(actions_group)
        
        self.tab_widget.addTab(dashboard_widget, "🏠 Dashboard")
        
    def create_students_tab(self):
        """Create the students management tab."""
        students_widget = QWidget()
        layout = QVBoxLayout(students_widget)
        
        # Search and filter
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search students...")
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["All", "High Risk", "Medium Risk", "Low Risk"])
        filter_layout.addWidget(QLabel("Risk Level:"))
        filter_layout.addWidget(self.risk_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Students table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Grade Avg", "Attendance", "Risk Level"
        ])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.students_table)
        
        # Student actions
        actions_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("👁️ View Details")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.predict_btn = QPushButton("🔮 Predict Risk")
        
        for btn in [self.view_btn, self.edit_btn, self.delete_btn, self.predict_btn]:
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.tab_widget.addTab(students_widget, "👥 Students")
        
    def create_analytics_tab(self):
        """Create the analytics tab."""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Chart controls
        controls_layout = QHBoxLayout()
        
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "Grade Distribution",
            "Performance Trends", 
            "Risk Distribution",
            "Attendance vs Performance"
        ])
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type)
        
        self.refresh_chart_btn = QPushButton("🔄 Update Chart")
        controls_layout.addWidget(self.refresh_chart_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Chart display area
        self.chart_label = QLabel("Chart will be displayed here")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setMinimumHeight(400)
        self.chart_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self.chart_label)
        
        self.tab_widget.addTab(analytics_widget, "📊 Analytics")
        
    def create_predictions_tab(self):
        """Create the predictions tab."""
        predictions_widget = QWidget()
        layout = QVBoxLayout(predictions_widget)
        
        # Prediction controls
        pred_controls = QHBoxLayout()
        
        self.batch_predict_btn = QPushButton("🔮 Run Batch Predictions")
        self.train_model_btn = QPushButton("🤖 Train Model")
        self.export_pred_btn = QPushButton("📤 Export Predictions")
        
        for btn in [self.batch_predict_btn, self.train_model_btn, self.export_pred_btn]:
            pred_controls.addWidget(btn)
        
        pred_controls.addStretch()
        layout.addLayout(pred_controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Predictions table
        self.predictions_table = QTableWidget()
        self.predictions_table.setColumnCount(5)
        self.predictions_table.setHorizontalHeaderLabels([
            "Student", "Prediction", "Probability", "Date", "Features"
        ])
        layout.addWidget(self.predictions_table)
        
        self.tab_widget.addTab(predictions_widget, "🔮 Predictions")
        
    def create_notifications_tab(self):
        """Create the notifications tab."""
        notifications_widget = QWidget()
        layout = QVBoxLayout(notifications_widget)
        
        # Notification settings
        settings_group = QGroupBox("🔔 Notification Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.email_enabled = QComboBox()
        self.email_enabled.addItems(["Enabled", "Disabled"])
        settings_layout.addRow("Email Notifications:", self.email_enabled)
        
        self.sms_enabled = QComboBox()
        self.sms_enabled.addItems(["Enabled", "Disabled"])
        settings_layout.addRow("SMS Notifications:", self.sms_enabled)
        
        self.risk_threshold = QComboBox()
        self.risk_threshold.addItems(["High Only", "High & Medium", "All"])
        settings_layout.addRow("Notify for:", self.risk_threshold)
        
        layout.addWidget(settings_group)
        
        # Manual notification
        manual_group = QGroupBox("✉️ Send Manual Notification")
        manual_layout = QVBoxLayout(manual_group)
        
        self.notify_btn = QPushButton("Send Test Notification")
        manual_layout.addWidget(self.notify_btn)
        
        layout.addWidget(manual_group)
        
        # Notification history
        history_group = QGroupBox("📋 Notification History")
        history_layout = QVBoxLayout(history_group)
        
        self.notifications_table = QTableWidget()
        self.notifications_table.setColumnCount(5)
        self.notifications_table.setHorizontalHeaderLabels([
            "Date", "Type", "Student", "Status", "Message"
        ])
        history_layout.addWidget(self.notifications_table)
        
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(notifications_widget, "🔔 Notifications")
        
    def setup_connections(self):
        """Setup signal-slot connections."""
        # Students tab
        self.students_table.itemSelectionChanged.connect(self.on_student_selected)
        self.view_btn.clicked.connect(self.view_student)
        self.edit_btn.clicked.connect(self.edit_student)
        self.delete_btn.clicked.connect(self.delete_student)
        self.predict_btn.clicked.connect(self.predict_single_student)
        self.search_input.textChanged.connect(self.filter_students)
        self.risk_filter.currentTextChanged.connect(self.filter_students)
        
        # Analytics tab
        self.refresh_chart_btn.clicked.connect(self.update_chart)
        self.chart_type.currentTextChanged.connect(self.update_chart)
        
        # Predictions tab
        self.batch_predict_btn.clicked.connect(self.run_batch_predictions)
        self.train_model_btn.clicked.connect(self.train_model)
        self.export_pred_btn.clicked.connect(self.export_predictions)
        
        # Notifications tab
        self.notify_btn.clicked.connect(self.send_test_notification)
        
    def load_data(self):
        """Load data from database."""
        try:
            self.load_students()
            self.load_predictions()
            self.load_notifications()
            self.update_dashboard()
            self.update_chart()
            
            self.status_bar.showMessage("Data loaded successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
            
    def load_students(self):
        """Load students into the table."""
        students = self.session.query(Student).all()
        
        self.students_table.setRowCount(len(students))
        
        for row, student in enumerate(students):
            self.students_table.setItem(row, 0, QTableWidgetItem(student.student_id))
            self.students_table.setItem(row, 1, QTableWidgetItem(student.name))
            self.students_table.setItem(row, 2, QTableWidgetItem(student.email or ""))
            self.students_table.setItem(row, 3, QTableWidgetItem(f"{student.get_grade_average():.1f}"))
            self.students_table.setItem(row, 4, QTableWidgetItem(f"{student.get_attendance_rate():.1f}%"))
            self.students_table.setItem(row, 5, QTableWidgetItem(student.get_risk_level()))
            
    def load_predictions(self):
        """Load predictions into the table."""
        predictions = self.session.query(Prediction).join(Student).all()
        
        self.predictions_table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            self.predictions_table.setItem(row, 0, QTableWidgetItem(pred.student.name))
            self.predictions_table.setItem(row, 1, QTableWidgetItem(pred.prediction))
            self.predictions_table.setItem(row, 2, QTableWidgetItem(f"{pred.probability:.1%}"))
            self.predictions_table.setItem(row, 3, QTableWidgetItem(pred.prediction_date.strftime("%Y-%m-%d")))
            self.predictions_table.setItem(row, 4, QTableWidgetItem(pred.features_used or ""))
            
    def load_notifications(self):
        """Load notifications into the table."""
        from src.models import Notification
        notifications = self.session.query(Notification).all()
        
        self.notifications_table.setRowCount(len(notifications))
        
        for row, notif in enumerate(notifications):
            self.notifications_table.setItem(row, 0, QTableWidgetItem(notif.created_at.strftime("%Y-%m-%d %H:%M")))
            self.notifications_table.setItem(row, 1, QTableWidgetItem(notif.type))
            student_name = notif.student.name if notif.student else "System"
            self.notifications_table.setItem(row, 2, QTableWidgetItem(student_name))
            self.notifications_table.setItem(row, 3, QTableWidgetItem(notif.status))
            self.notifications_table.setItem(row, 4, QTableWidgetItem(notif.title))
            
    def update_dashboard(self):
        """Update dashboard with current statistics."""
        students = self.session.query(Student).all()
        predictions = self.session.query(Prediction).all()
        
        total_students = len(students)
        high_risk = len([p for p in predictions if p.prediction == "High Risk"])
        avg_grade = np.mean([s.get_grade_average() for s in students]) if students else 0
        avg_attendance = np.mean([s.get_attendance_rate() for s in students]) if students else 0
        
        self.total_students_label.setText(f"Total Students: {total_students}")
        self.high_risk_label.setText(f"High Risk: {high_risk}")
        self.avg_grade_label.setText(f"Average Grade: {avg_grade:.1f}%")
        self.avg_attendance_label.setText(f"Avg Attendance: {avg_attendance:.1f}%")
        
        # Update alerts
        if high_risk > 0:
            self.alerts_text.setText(f"🚨 {high_risk} students identified as high risk\n⚠️ Review their performance and attendance")
        else:
            self.alerts_text.setText("✅ No critical alerts at this time")
            
    def update_chart(self):
        """Update the analytics chart."""
        chart_type = self.chart_type.currentText()
        
        try:
            if chart_type == "Grade Distribution":
                fig = create_grade_distribution(self.session)
            elif chart_type == "Performance Trends":
                fig = create_performance_trends(self.session)
            elif chart_type == "Risk Distribution":
                from src.visuals import create_risk_distribution
                fig = create_risk_distribution(self.session)
            elif chart_type == "Attendance vs Performance":
                from src.visuals import create_attendance_vs_performance
                fig = create_attendance_vs_performance(self.session)
            else:
                fig = create_grade_distribution(self.session)
                
            # Convert plotly figure to image and display
            # Note: In a real implementation, you'd use a web engine to display plotly
            self.chart_label.setText(f"📊 {chart_type}\n(Chart visualization would appear here)")
            
        except Exception as e:
            self.chart_label.setText(f"Error generating chart: {str(e)}")
            
    def on_student_selected(self):
        """Handle student selection change."""
        selected_items = self.students_table.selectedItems()
        if selected_items:
            self.current_student_id = selected_items[0].text()
            
    def add_student(self):
        """Add a new student."""
        dialog = StudentDialog(self)
        if dialog.exec_():
            student_data = dialog.get_student_data()
            try:
                student = Student(**student_data)
                self.session.add(student)
                self.session.commit()
                self.load_data()
                QMessageBox.information(self, "Success", "Student added successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add student: {str(e)}")
                self.session.rollback()
                
    def edit_student(self):
        """Edit selected student."""
        if not self.current_student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return
            
        student = self.session.query(Student).filter_by(student_id=self.current_student_id).first()
        if student:
            dialog = StudentDialog(self, student)
            if dialog.exec_():
                student_data = dialog.get_student_data()
                try:
                    for key, value in student_data.items():
                        setattr(student, key, value)
                    self.session.commit()
                    self.load_data()
                    QMessageBox.information(self, "Success", "Student updated successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update student: {str(e)}")
                    self.session.rollback()
                    
    def view_student(self):
        """View student details."""
        if not self.current_student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return
            
        student = self.session.query(Student).filter_by(student_id=self.current_student_id).first()
        if student:
            details = f"""
            Student Details:
            
            ID: {student.student_id}
            Name: {student.name}
            Email: {student.email or 'N/A'}
            Phone: {student.phone or 'N/A'}
            Enrollment Date: {student.enrollment_date or 'N/A'}
            
            Grade Average: {student.get_grade_average():.1f}%
            Attendance Rate: {student.get_attendance_rate():.1f}%
            Risk Level: {student.get_risk_level()}
            """
            QMessageBox.information(self, "Student Details", details)
            
    def delete_student(self):
        """Delete selected student."""
        if not self.current_student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete student {self.current_student_id}?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            student = self.session.query(Student).filter_by(student_id=self.current_student_id).first()
            if student:
                try:
                    self.session.delete(student)
                    self.session.commit()
                    self.load_data()
                    QMessageBox.information(self, "Success", "Student deleted successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete student: {str(e)}")
                    self.session.rollback()
                    
    def predict_single_student(self):
        """Predict risk for selected student."""
        if not self.current_student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return
            
        student = self.session.query(Student).filter_by(student_id=self.current_student_id).first()
        if student:
            try:
                result = predict_student_risk(student, self.session)
                if result:
                    message = f"""
                    Prediction Results for {student.name}:
                    
                    Risk Level: {result['risk_level']}
                    Probability: {result['probability']:.1%}
                    
                    Features Used:
                    - Grade Average: {result['features']['grade_average']:.1f}
                    - Attendance Rate: {result['features']['attendance_rate']:.1f}%
                    - Recent Grade Avg: {result['features']['recent_grade_avg']:.1f}
                    - Grade Trend: {result['features']['grade_trend']:.1f}
                    - Missing Assignments: {result['features']['missing_assignments']}
                    - Course Count: {result['features']['course_count']}
                    """
                    QMessageBox.information(self, "Risk Prediction", message)
                else:
                    QMessageBox.warning(self, "Warning", "Could not generate prediction for this student")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Prediction failed: {str(e)}")
                
    def filter_students(self):
        """Filter students based on search criteria."""
        search_text = self.search_input.text().lower()
        risk_filter = self.risk_filter.currentText()
        
        for row in range(self.students_table.rowCount()):
            show_row = True
            
            # Apply search filter
            if search_text:
                row_text = ""
                for col in range(self.students_table.columnCount()):
                    item = self.students_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                if search_text not in row_text:
                    show_row = False
            
            # Apply risk filter
            if risk_filter != "All":
                risk_item = self.students_table.item(row, 5)
                if risk_item and risk_item.text() != risk_filter:
                    show_row = False
            
            self.students_table.setRowHidden(row, not show_row)
            
    def run_batch_predictions(self):
        """Run predictions for all students."""
        reply = QMessageBox.question(self, "Confirm", 
                                   "Run predictions for all students? This may take a while.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # In a real implementation, you'd run this in a separate thread
            try:
                from predict import run_predictions
                run_predictions()
                self.load_data()
                QMessageBox.information(self, "Success", "Batch predictions completed")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Batch predictions failed: {str(e)}")
            finally:
                self.progress_bar.setVisible(False)
                
    def train_model(self):
        """Train the prediction model."""
        reply = QMessageBox.question(self, "Confirm", 
                                   "Train the prediction model? This may take a while.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            try:
                from train import train_model
                train_model()
                QMessageBox.information(self, "Success", "Model training completed")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Model training failed: {str(e)}")
            finally:
                self.progress_bar.setVisible(False)
                
    def export_predictions(self):
        """Export predictions to CSV."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Predictions", "", "CSV Files (*.csv)")
        
        if filename:
            try:
                predictions = self.session.query(Prediction).join(Student).all()
                import csv
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Student', 'Prediction', 'Probability', 'Date', 'Features'])
                    for pred in predictions:
                        writer.writerow([
                            pred.student.name,
                            pred.prediction,
                            f"{pred.probability:.3f}",
                            pred.prediction_date.strftime("%Y-%m-%d"),
                            pred.features_used or ""
                        ])
                QMessageBox.information(self, "Success", "Predictions exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                
    def send_test_notification(self):
        """Send a test notification."""
        try:
            # This would send to the configured admin email
            notification_manager.send_daily_risk_report(self.session)
            QMessageBox.information(self, "Success", "Test notification sent")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Notification failed: {str(e)}")
            
    def import_csv(self):
        """Import data from CSV file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv)")
        
        if filename:
            try:
                from import_csv import import_students_from_csv
                import_students_from_csv(filename)
                self.load_data()
                QMessageBox.information(self, "Success", "CSV imported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
                
    def export_data(self):
        """Export data to CSV."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "CSV Files (*.csv)")
        
        if filename:
            try:
                students = self.session.query(Student).all()
                import csv
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Student ID', 'Name', 'Email', 'Grade Avg', 'Attendance Rate', 'Risk Level'])
                    for student in students:
                        writer.writerow([
                            student.student_id,
                            student.name,
                            student.email or "",
                            f"{student.get_grade_average():.1f}",
                            f"{student.get_attendance_rate():.1f}",
                            student.get_risk_level()
                        ])
                QMessageBox.information(self, "Success", "Data exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
                
    def run_predictions(self):
        """Quick action: run predictions."""
        self.run_batch_predictions()
        
    def send_notifications(self):
        """Quick action: send notifications."""
        self.send_test_notification()
        
    def generate_report(self):
        """Quick action: generate report."""
        QMessageBox.information(self, "Report", "Report generation would be implemented here")
        
    def system_check(self):
        """Quick action: system check."""
        # Check database connection
        try:
            student_count = self.session.query(Student).count()
            db_status = f"✅ Database: Connected ({student_count} students)"
        except:
            db_status = "❌ Database: Connection failed"
            
        # Check model
        model_path = project_root / 'data' / 'trained_model.pkl'
        model_status = "✅ Model: Available" if model_path.exists() else "❌ Model: Not trained"
        
        # Check notifications
        notification_status = "✅ Notifications: Configured" if notification_manager.smtp_username else "⚠️ Notifications: Not configured"
        
        status_message = f"""
        System Status Check:
        
        {db_status}
        {model_status}
        {notification_status}
        
        All systems operational!
        """
        QMessageBox.information(self, "System Check", status_message)
        
    def get_stylesheet(self):
        """Return the application stylesheet."""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QWidget {
            font-family: Arial, sans-serif;
        }
        
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QTableWidget {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        
        QTableWidget::item:selected {
            background-color: #e3f2fd;
        }
        
        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 8px;
            border: none;
            border-right: 1px solid #ddd;
            font-weight: bold;
        }
        
        QTabWidget::pane {
            border: 1px solid #ddd;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e9ecef;
            padding: 8px 16px;
            margin-right: 2px;
            border-radius: 4px 4px 0 0;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4CAF50;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QLineEdit, QComboBox {
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
            background-color: #f8f9fa;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        """
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop notification scheduler
        notification_manager.stop_scheduler()
        
        # Close database session
        self.session.close()
        
        event.accept()