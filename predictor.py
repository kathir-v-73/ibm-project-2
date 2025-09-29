import pickle
import pandas as pd
from .models import Student

def predict_student_risk(student_data):
    """
    Predict student risk level based on their data
    """
    try:
        # Load trained model
        model_path = 'data/trained_model.pkl'
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Prepare features for prediction
        features = [
            student_data.grade_average,
            student_data.attendance_rate,
            # Add other features as needed
        ]
        
        prediction = model.predict([features])[0]
        
        # Map prediction to risk level
        risk_levels = {0: 'Low Risk', 1: 'Medium Risk', 2: 'High Risk'}
        return risk_levels.get(prediction, 'Unknown Risk')
    
    except Exception as e:
        # Fallback to rule-based risk assessment
        return calculate_risk_level(student_data)

def calculate_risk_level(student):
    """
    Rule-based risk assessment fallback
    """
    if student.grade_average < 50 or student.attendance_rate < 60:
        return 'High Risk'
    elif student.grade_average < 70 or student.attendance_rate < 75:
        return 'Medium Risk'
    else:
        return 'Low Risk'

def update_all_student_risks():
    """
    Update risk levels for all students
    """
    students = Student.query.all()
    for student in students:
        risk_level = predict_student_risk(student)
        student.risk_level = risk_level
    
    from .models import db
    db.session.commit()