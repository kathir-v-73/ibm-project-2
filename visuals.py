"""
TechKey Analysis - Visualization Module
"""

import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Optional
import io
import base64


def create_grade_distribution(session, course_id: Optional[int] = None):
    """
    Create grade distribution chart.
    
    Args:
        session: Database session
        course_id: Optional course filter
        
    Returns:
        plotly.graph_objects.Figure: Grade distribution chart
    """
    from .models import Grade, Course
    
    query = session.query(Grade)
    if course_id:
        query = query.filter(Grade.course_id == course_id)
    
    grades = query.all()
    
    if not grades:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No grade data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    scores = [grade.score for grade in grades]
    
    fig = px.histogram(
        x=scores,
        nbins=20,
        title="Grade Distribution",
        labels={'x': 'Grade Score', 'y': 'Count'},
        color_discrete_sequence=['#3366CC']
    )
    
    fig.update_layout(
        xaxis_title="Grade Score",
        yaxis_title="Number of Students",
        showlegend=False,
        template="plotly_white"
    )
    
    # Add mean line
    mean_score = np.mean(scores)
    fig.add_vline(
        x=mean_score,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_score:.1f}"
    )
    
    return fig


def create_performance_trends(session, student_id: Optional[int] = None):
    """
    Create performance trends over time.
    
    Args:
        session: Database session
        student_id: Optional student filter
        
    Returns:
        plotly.graph_objects.Figure: Performance trends chart
    """
    from .models import Grade, Student
    
    query = session.query(Grade).join(Student)
    
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    
    grades = query.order_by(Grade.grade_date).all()
    
    if not grades:
        fig = go.Figure()
        fig.add_annotation(
            text="No grade data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Create DataFrame for easier manipulation
    df = pd.DataFrame([{
        'date': grade.grade_date,
        'score': grade.score,
        'student': grade.student.name,
        'assignment': grade.assignment_name
    } for grade in grades])
    
    if student_id:
        # Single student - show all grades
        fig = px.line(
            df, x='date', y='score',
            title=f"Grade Trend - {df['student'].iloc[0]}",
            markers=True
        )
    else:
        # Multiple students - show average trend
        df_avg = df.groupby('date')['score'].mean().reset_index()
        fig = px.line(
            df_avg, x='date', y='score',
            title="Average Grade Trend",
            markers=True
        )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Grade Score",
        template="plotly_white"
    )
    
    return fig


def create_correlation_heatmap(session):
    """
    Create correlation heatmap of student metrics.
    
    Args:
        session: Database session
        
    Returns:
        plotly.graph_objects.Figure: Correlation heatmap
    """
    from .models import Student
    
    students = session.query(Student).all()
    
    if not students:
        fig = go.Figure()
        fig.add_annotation(
            text="No student data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    data = []
    for student in students:
        data.append({
            'grade_avg': student.get_grade_average(),
            'attendance_rate': student.get_attendance_rate(),
            'course_count': len(student.enrollments)
        })
    
    df = pd.DataFrame(data)
    
    # Calculate correlation matrix
    corr_matrix = df.corr()
    
    fig = px.imshow(
        corr_matrix,
        title="Feature Correlation Heatmap",
        color_continuous_scale="RdBu_r",
        aspect="auto"
    )
    
    fig.update_layout(
        xaxis_title="Features",
        yaxis_title="Features",
        template="plotly_white"
    )
    
    return fig


def create_attendance_vs_performance(session):
    """
    Create scatter plot of attendance vs performance.
    
    Args:
        session: Database session
        
    Returns:
        plotly.graph_objects.Figure: Scatter plot
    """
    from .models import Student, Prediction
    
    students = session.query(Student).all()
    
    if not students:
        fig = go.Figure()
        fig.add_annotation(
            text="No student data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    data = []
    for student in students:
        prediction = session.query(Prediction).filter_by(student_id=student.id).first()
        risk_level = prediction.prediction if prediction else 'Unknown'
        
        data.append({
            'attendance_rate': student.get_attendance_rate(),
            'grade_avg': student.get_grade_average(),
            'student': student.name,
            'risk_level': risk_level
        })
    
    df = pd.DataFrame(data)
    
    fig = px.scatter(
        df, x='attendance_rate', y='grade_avg',
        color='risk_level',
        title="Attendance vs Performance",
        hover_data=['student'],
        color_discrete_map={
            'High Risk': '#FF4444',
            'Low Risk': '#44FF44',
            'Unknown': '#888888'
        }
    )
    
    fig.update_layout(
        xaxis_title="Attendance Rate (%)",
        yaxis_title="Grade Average (%)",
        template="plotly_white"
    )
    
    # Add trend line
    if len(df) > 1:
        z = np.polyfit(df['attendance_rate'], df['grade_avg'], 1)
        p = np.poly1d(z)
        
        x_range = np.linspace(df['attendance_rate'].min(), df['attendance_rate'].max(), 100)
        fig.add_trace(go.Scatter(
            x=x_range, y=p(x_range),
            mode='lines',
            name='Trend',
            line=dict(dash='dash', color='gray'),
            showlegend=False
        ))
    
    return fig


def create_risk_distribution(session):
    """
    Create risk level distribution chart.
    
    Args:
        session: Database session
        
    Returns:
        plotly.graph_objects.Figure: Risk distribution chart
    """
    from .models import Prediction
    
    predictions = session.query(Prediction).all()
    
    if not predictions:
        fig = go.Figure()
        fig.add_annotation(
            text="No prediction data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    risk_counts = {}
    for pred in predictions:
        risk_counts[pred.prediction] = risk_counts.get(pred.prediction, 0) + 1
    
    fig = px.pie(
        values=list(risk_counts.values()),
        names=list(risk_counts.keys()),
        title="Student Risk Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    return fig


def create_student_comparison(session, student_ids: List[int]):
    """
    Create comparison chart for multiple students.
    
    Args:
        session: Database session
        student_ids: List of student IDs to compare
        
    Returns:
        plotly.graph_objects.Figure: Comparison chart
    """
    from .models import Student
    
    students = session.query(Student).filter(Student.id.in_(student_ids)).all()
    
    if not students:
        fig = go.Figure()
        fig.add_annotation(
            text="No student data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    metrics = ['Grade Average', 'Attendance Rate', 'Course Count']
    values = []
    
    for student in students:
        student_values = [
            student.get_grade_average(),
            student.get_attendance_rate(),
            len(student.enrollments)
        ]
        values.append(student_values)
    
    fig = go.Figure()
    
    for i, student in enumerate(students):
        fig.add_trace(go.Bar(
            name=student.name,
            x=metrics,
            y=values[i]
        ))
    
    fig.update_layout(
        title="Student Comparison",
        xaxis_title="Metrics",
        yaxis_title="Values",
        barmode='group',
        template="plotly_white"
    )
    
    return fig


def fig_to_base64(fig):
    """
    Convert matplotlib figure to base64 string for embedding.
    
    Args:
        fig: matplotlib figure
        
    Returns:
        str: Base64 encoded image
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str


def create_matplotlib_grade_distribution(session):
    """
    Create grade distribution using matplotlib (for static images).
    
    Args:
        session: Database session
        
    Returns:
        matplotlib.figure.Figure: Grade distribution chart
    """
    from .models import Grade
    
    grades = session.query(Grade).all()
    
    if not grades:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No grade data available', 
                ha='center', va='center', transform=ax.transAxes)
        return fig
    
    scores = [grade.score for grade in grades]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    ax.axvline(np.mean(scores), color='red', linestyle='--', 
               label=f'Mean: {np.mean(scores):.1f}')
    
    ax.set_xlabel('Grade Score')
    ax.set_ylabel('Number of Students')
    ax.set_title('Grade Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig