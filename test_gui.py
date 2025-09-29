"""
TechKey Analysis - GUI Tests
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gui.main_window import MainWindow
from gui.student_dialog import StudentDialog


class TestGUI:
    """Test cases for GUI components."""
    
    @pytest.fixture(scope="session")
    def qapp(self):
        """Create QApplication instance."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
    
    @pytest.fixture
    def main_window(self, qapp):
        """Create main window instance."""
        with patch('gui.main_window.get_session') as mock_session:
            mock_session.return_value = Mock()
            window = MainWindow()
            yield window
            window.close()
    
    @pytest.fixture
    def student_dialog(self, qapp):
        """Create student dialog instance."""
        dialog = StudentDialog()
        yield dialog
        dialog.close()
    
    def test_main_window_creation(self, main_window):
        """Test main window creation and basic properties."""
        assert main_window is not None
        assert main_window.windowTitle() == "TechKey Analysis - Student Performance System"
        assert main_window.tab_widget is not None
    
    def test_main_window_tabs(self, main_window):
        """Test that all main tabs are created."""
        tab_count = main_window.tab_widget.count()
        assert tab_count == 5  # Dashboard, Students, Analytics, Predictions, Notifications
        
        # Check tab names
        tab_names = []
        for i in range(tab_count):
            tab_names.append(main_window.tab_widget.tabText(i))
        
        expected_tabs = ["🏠 Dashboard", "👥 Students", "📊 Analytics", "🔮 Predictions", "🔔 Notifications"]
        for expected_tab in expected_tabs:
            assert expected_tab in tab_names
    
    def test_student_dialog_creation(self, student_dialog):
        """Test student dialog creation."""
        assert student_dialog is not None
        assert student_dialog.windowTitle() == "Add/Edit Student"
        
        # Check that form fields exist
        assert student_dialog.student_id_input is not None
        assert student_dialog.name_input is not None
        assert student_dialog.email_input is not None
        assert student_dialog.phone_input is not None
        assert student_dialog.enrollment_date_input is not None
        assert student_dialog.address_input is not None
    
    def test_student_dialog_validation(self, student_dialog):
        """Test student dialog form validation."""
        # Test empty form
        student_dialog.student_id_input.setText("")
        student_dialog.name_input.setText("")
        
        # Should fail validation
        with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
            student_dialog.accept()
            assert mock_warning.called
        
        # Test valid form
        student_dialog.student_id_input.setText("TEST001")
        student_dialog.name_input.setText("Test Student")
        student_dialog.email_input.setText("test@example.com")
        
        # Should pass validation
        with patch('PyQt5.QtWidgets.QDialog.accept') as mock_accept:
            student_dialog.accept()
            # In real implementation, this would call the parent accept
    
    def test_student_dialog_get_data(self, student_dialog):
        """Test student dialog data retrieval."""
        # Set form values
        student_dialog.student_id_input.setText("TEST002")
        student_dialog.name_input.setText("John Doe")
        student_dialog.email_input.setText("john@example.com")
        student_dialog.phone_input.setText("+1234567890")
        student_dialog.address_input.setText("123 Test Street")
        
        # Get data
        data = student_dialog.get_student_data()
        
        # Verify data
        assert data['student_id'] == "TEST002"
        assert data['name'] == "John Doe"
        assert data['email'] == "john@example.com"
        assert data['phone'] == "+1234567890"
        assert data['address'] == "123 Test Street"
    
    @patch('gui.main_window.QMessageBox')
    def test_main_window_add_student(self, mock_messagebox, main_window):
        """Test add student functionality."""
        # Mock the student dialog
        with patch('gui.main_window.StudentDialog') as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog_instance.exec_.return_value = True
            mock_dialog_instance.get_student_data.return_value = {
                'student_id': 'TEST003',
                'name': 'New Student',
                'email': 'new@example.com'
            }
            mock_dialog.return_value = mock_dialog_instance
            
            # Mock session operations
            main_window.session.add = Mock()
            main_window.session.commit = Mock()
            main_window.load_data = Mock()
            
            # Trigger add student
            main_window.add_student()
            
            # Verify student was added
            main_window.session.add.assert_called_once()
            main_window.session.commit.assert_called_once()
            main_window.load_data.assert_called_once()
    
    @patch('gui.main_window.QMessageBox')
    def test_main_window_delete_student(self, mock_messagebox, main_window):
        """Test delete student functionality."""
        # Mock confirmation dialog to return Yes
        mock_messagebox.question.return_value = mock_messagebox.Yes
        
        # Mock student data
        mock_student = Mock()
        mock_student.student_id = "TEST004"
        mock_student.name = "Student to Delete"
        
        main_window.current_student_id = "TEST004"
        main_window.session.query.return_value.filter_by.return_value.first.return_value = mock_student
        main_window.session.delete = Mock()
        main_window.session.commit = Mock()
        main_window.load_data = Mock()
        
        # Trigger delete student
        main_window.delete_student()
        
        # Verify student was deleted
        main_window.session.delete.assert_called_once_with(mock_student)
        main_window.session.commit.assert_called_once()
        main_window.load_data.assert_called_once()
    
    def test_main_window_search_filter(self, main_window):
        """Test student search and filter functionality."""
        # Mock students data
        mock_students = [
            Mock(student_id="S001", name="Alice Johnson", email="alice@example.com", 
                 get_grade_average=Mock(return_value=85.0), 
                 get_attendance_rate=Mock(return_value=90.0),
                 get_risk_level=Mock(return_value="Low Risk")),
            Mock(student_id="S002", name="Bob Smith", email="bob@example.com",
                 get_grade_average=Mock(return_value=45.0),
                 get_attendance_rate=Mock(return_value=60.0),
                 get_risk_level=Mock(return_value="High Risk"))
        ]
        
        main_window.session.query.return_value.all.return_value = mock_students
        main_window.load_students()
        
        # Test search filter
        main_window.search_input.setText("Alice")
        main_window.filter_students()
        
        # Test risk filter
        main_window.risk_filter.setCurrentText("High Risk")
        main_window.filter_students()
    
    @patch('gui.main_window.create_grade_distribution')
    def test_main_window_chart_update(self, mock_chart, main_window):
        """Test chart update functionality."""
        mock_chart.return_value = Mock()
        
        # Test different chart types
        chart_types = [
            "Grade Distribution",
            "Performance Trends", 
            "Risk Distribution",
            "Attendance vs Performance"
        ]
        
        for chart_type in chart_types:
            main_window.chart_type.setCurrentText(chart_type)
            main_window.update_chart()
        
        assert mock_chart.called


if __name__ == "__main__":
    pytest.main([__file__])