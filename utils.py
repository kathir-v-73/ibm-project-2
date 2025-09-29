"""
TechKey Analysis - Utility Functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json
import csv
import io


def calculate_academic_metrics(grades: List[float], attendance: List[bool]) -> Dict[str, Any]:
    """
    Calculate comprehensive academic metrics.
    
    Args:
        grades: List of grade scores
        attendance: List of attendance records (True for present)
        
    Returns:
        Dict with calculated metrics
    """
    if not grades:
        return {
            'grade_average': 0,
            'grade_std': 0,
            'attendance_rate': 0,
            'total_assignments': 0,
            'completion_rate': 0
        }
    
    grade_array = np.array(grades)
    attendance_array = np.array(attendance)
    
    metrics = {
        'grade_average': float(np.mean(grade_array)),
        'grade_std': float(np.std(grade_array)),
        'grade_min': float(np.min(grade_array)),
        'grade_max': float(np.max(grade_array)),
        'attendance_rate': float(np.mean(attendance_array) * 100) if attendance_array.size > 0 else 0,
        'total_assignments': len(grades),
        'completion_rate': 100.0  # All grades are completed assignments
    }
    
    return metrics


def generate_student_report(student_data: Dict, include_charts: bool = True) -> Dict[str, Any]:
    """
    Generate a comprehensive student report.
    
    Args:
        student_data: Student information and metrics
        include_charts: Whether to include chart data
        
    Returns:
        Dict with report data
    """
    report = {
        'student_info': {
            'name': student_data.get('name', ''),
            'student_id': student_data.get('student_id', ''),
            'email': student_data.get('email', ''),
            'enrollment_date': student_data.get('enrollment_date', '')
        },
        'academic_metrics': student_data.get('metrics', {}),
        'risk_assessment': student_data.get('risk_assessment', {}),
        'recommendations': [],
        'generated_at': datetime.now().isoformat()
    }
    
    # Generate recommendations based on metrics
    metrics = student_data.get('metrics', {})
    risk_level = student_data.get('risk_assessment', {}).get('level', 'Unknown')
    
    recommendations = []
    
    if metrics.get('grade_average', 0) < 60:
        recommendations.append({
            'type': 'academic',
            'priority': 'high',
            'action': 'Schedule academic intervention',
            'reason': f'Low grade average ({metrics["grade_average"]:.1f}%)'
        })
    
    if metrics.get('attendance_rate', 0) < 75:
        recommendations.append({
            'type': 'attendance',
            'priority': 'high',
            'action': 'Address attendance issues',
            'reason': f'Low attendance rate ({metrics["attendance_rate"]:.1f}%)'
        })
    
    if risk_level == 'High Risk':
        recommendations.append({
            'type': 'general',
            'priority': 'high',
            'action': 'Immediate advisor consultation',
            'reason': 'High risk classification'
        })
    
    if not recommendations:
        recommendations.append({
            'type': 'general',
            'priority': 'low',
            'action': 'Continue current support',
            'reason': 'Student performing adequately'
        })
    
    report['recommendations'] = recommendations
    
    return report


def export_to_csv(data: List[Dict], filename: str = None) -> str:
    """
    Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        filename: Optional filename for download
        
    Returns:
        str: CSV data as string
    """
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def export_to_json(data: Any, filename: str = None) -> str:
    """
    Export data to JSON format.
    
    Args:
        data: Data to export
        filename: Optional filename for download
        
    Returns:
        str: JSON data as string
    """
    return json.dumps(data, indent=2, default=str)


def validate_student_data(student_data: Dict) -> tuple[bool, List[str]]:
    """
    Validate student data before saving.
    
    Args:
        student_data: Student data to validate
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ['student_id', 'name']
    for field in required_fields:
        if not student_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate email format
    email = student_data.get('email')
    if email and '@' not in email:
        errors.append("Invalid email format")
    
    # Validate student ID format
    student_id = student_data.get('student_id', '')
    if student_id and not student_id.startswith(('S', 's')):
        errors.append("Student ID should start with 'S'")
    
    return len(errors) == 0, errors


def calculate_semester_progress(start_date: date, end_date: date = None) -> float:
    """
    Calculate semester progress percentage.
    
    Args:
        start_date: Semester start date
        end_date: Semester end date (defaults to today + 4 months)
        
    Returns:
        float: Progress percentage (0-100)
    """
    if end_date is None:
        end_date = start_date + timedelta(days=120)  # ~4 months
    
    today = date.today()
    
    if today < start_date:
        return 0.0
    elif today > end_date:
        return 100.0
    
    total_days = (end_date - start_date).days
    elapsed_days = (today - start_date).days
    
    return (elapsed_days / total_days) * 100


def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard format.
    
    Args:
        phone: Raw phone number
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if format is unknown


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        int: Converted value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


class DataCleaner:
    """Utility class for data cleaning operations."""
    
    @staticmethod
    def clean_student_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean student data DataFrame.
        
        Args:
            df: Raw student data
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Remove duplicates
        cleaned_df = cleaned_df.drop_duplicates(subset=['student_id'], keep='first')
        
        # Clean email addresses
        if 'email' in cleaned_df.columns:
            cleaned_df['email'] = cleaned_df['email'].str.lower().str.strip()
        
        # Clean names (title case)
        if 'name' in cleaned_df.columns:
            cleaned_df['name'] = cleaned_df['name'].str.title().str.strip()
        
        # Fill missing values
        if 'email' in cleaned_df.columns:
            cleaned_df['email'] = cleaned_df['email'].fillna('')
        
        return cleaned_df
    
    @staticmethod
    def validate_grade_data(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
        """
        Validate grade data and return cleaned data with warnings.
        
        Args:
            df: Raw grade data
            
        Returns:
            tuple: (cleaned_df, warnings)
        """
        warnings = []
        cleaned_df = df.copy()
        
        # Check for missing scores
        if 'score' in cleaned_df.columns:
            missing_scores = cleaned_df['score'].isna().sum()
            if missing_scores > 0:
                warnings.append(f"Found {missing_scores} records with missing scores")
                cleaned_df = cleaned_df.dropna(subset=['score'])
        
        # Validate score range
        if 'score' in cleaned_df.columns:
            invalid_scores = cleaned_df[(cleaned_df['score'] < 0) | (cleaned_df['score'] > 100)]
            if len(invalid_scores) > 0:
                warnings.append(f"Found {len(invalid_scores)} records with scores outside 0-100 range")
                cleaned_df = cleaned_df[(cleaned_df['score'] >= 0) & (cleaned_df['score'] <= 100)]
        
        return cleaned_df, warnings