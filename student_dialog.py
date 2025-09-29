"""
TechKey Analysis - Student Dialog for Add/Edit Operations
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLineEdit, QPushButton, QLabel, QDateEdit,
                            QTextEdit, QMessageBox)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime


class StudentDialog(QDialog):
    """Dialog for adding/editing students."""
    
    def __init__(self, parent=None, student=None):
        super().__init__(parent)
        self.student = student
        self.setup_ui()
        self.load_student_data()
        
    def setup_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Add/Edit Student")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.student_id_input = QLineEdit()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.enrollment_date_input = QDateEdit()
        self.enrollment_date_input.setDate(QDate.currentDate())
        self.enrollment_date_input.setCalendarPopup(True)
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        
        form_layout.addRow("Student ID*:", self.student_id_input)
        form_layout.addRow("Name*:", self.name_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Enrollment Date:", self.enrollment_date_input)
        form_layout.addRow("Address:", self.address_input)
        
        layout.addLayout(form_layout)
        
        # Required fields note
        required_note = QLabel("* Required fields")
        required_note.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(required_note)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save")
        self.cancel_btn = QPushButton("❌ Cancel")
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_student_data(self):
        """Load student data if editing."""
        if self.student:
            self.student_id_input.setText(self.student.student_id)
            self.name_input.setText(self.student.name)
            self.email_input.setText(self.student.email or "")
            self.phone_input.setText(self.student.phone or "")
            
            if self.student.enrollment_date:
                qdate = QDate(
                    self.student.enrollment_date.year,
                    self.student.enrollment_date.month,
                    self.student.enrollment_date.day
                )
                self.enrollment_date_input.setDate(qdate)
            
            self.address_input.setText(self.student.address or "")
            
            # Make student ID read-only when editing
            self.student_id_input.setReadOnly(True)
            
    def get_student_data(self):
        """Get student data from form inputs."""
        return {
            'student_id': self.student_id_input.text().strip(),
            'name': self.name_input.text().strip(),
            'email': self.email_input.text().strip() or None,
            'phone': self.phone_input.text().strip() or None,
            'enrollment_date': self.enrollment_date_input.date().toPyDate(),
            'address': self.address_input.toPlainText().strip() or None
        }
        
    def accept(self):
        """Validate and accept the dialog."""
        data = self.get_student_data()
        
        # Validate required fields
        if not data['student_id']:
            QMessageBox.warning(self, "Validation Error", "Student ID is required")
            return
            
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return
            
        # Validate email format
        if data['email'] and '@' not in data['email']:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address")
            return
            
        super().accept()