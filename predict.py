import pandas as pd
import numpy as np

def predict_student_risk(student_data):
    """
    Predict student risk based on grade and attendance
    Simple rule-based approach
    """
    try:
        grade = student_data.get('grade', 0)
        attendance = student_data.get('attendance', 0)
        
        # Convert to numeric if they're strings
        try:
            grade = float(grade)
        except (ValueError, TypeError):
            grade = 0
            
        try:
            attendance = float(attendance)
        except (ValueError, TypeError):
            attendance = 0
        
        # Risk assessment rules
        if grade < 60 or attendance < 70:
            return "High Risk"
        elif grade < 75 or attendance < 80:
            return "Medium Risk"
        else:
            return "Low Risk"
            
    except Exception as e:
        print(f"Error in risk prediction: {e}")
        return "Unknown Risk"