"""
TechKey Analysis - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import get_session
from src.models import Student, Grade, Course
from src.visuals import create_grade_distribution, create_performance_trends
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init_session():
    """Initialize database session."""
    return get_session()


def load_student_data(session):
    """Load student data from database."""
    students = session.query(Student).all()
    data = []
    for student in students:
        data.append({
            'student_id': student.student_id,
            'name': student.name,
            'email': student.email,
            'grade_avg': student.get_grade_average(),
            'attendance_rate': student.get_attendance_rate(),
            'risk_level': student.get_risk_level()
        })
    return pd.DataFrame(data)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="TechKey Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🎓 TechKey Analytics Dashboard")
    st.markdown("---")
    
    # Initialize session
    session = init_session()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_student_data(session)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Students",
            len(df),
            help="Total number of students in the system"
        )
    
    with col2:
        at_risk = len(df[df['risk_level'] == 'High Risk'])
        st.metric(
            "At-Risk Students",
            at_risk,
            delta=f"-{len(df) - at_risk}",
            delta_color="inverse",
            help="Students identified as high risk"
        )
    
    with col3:
        avg_grade = df['grade_avg'].mean()
        st.metric(
            "Average Grade",
            f"{avg_grade:.1f}%",
            help="Average grade across all students"
        )
    
    with col4:
        avg_attendance = df['attendance_rate'].mean()
        st.metric(
            "Average Attendance",
            f"{avg_attendance:.1f}%",
            help="Average attendance rate"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Grade Distribution")
        fig = create_grade_distribution(session)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Performance Trends")
        fig = create_performance_trends(session)
        st.plotly_chart(fig, use_container_width=True)
    
    # Student data table
    st.subheader("Student Overview")
    
    # Risk level filter
    risk_filter = st.selectbox(
        "Filter by Risk Level",
        ["All", "High Risk", "Medium Risk", "Low Risk"]
    )
    
    if risk_filter != "All":
        filtered_df = df[df['risk_level'] == risk_filter]
    else:
        filtered_df = df
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export options
    st.sidebar.header("Export Data")
    if st.sidebar.button("Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.sidebar.download_button(
            "Download CSV",
            csv,
            "student_data.csv",
            "text/csv"
        )


if __name__ == "__main__":
    main()