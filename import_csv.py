#!/usr/bin/env python3
"""
TechKey Analysis - CSV Import Script
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import get_session
from src.models import Student


def import_students_from_csv(csv_path=None):
    """Import students from CSV file."""
    if csv_path is None:
        csv_path = project_root / 'data' / 'sample_students.csv'
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📥 Importing students from {csv_path}...")
    
    session = get_session()
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        print(f"📊 Found {len(df)} records in CSV")
        
        imported_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            try:
                # Check if student already exists
                existing_student = session.query(Student).filter_by(
                    student_id=row['student_id']
                ).first()
                
                if existing_student:
                    # Update existing student
                    existing_student.name = row['name']
                    existing_student.email = row.get('email', '')
                    updated_count += 1
                else:
                    # Create new student
                    student = Student(
                        student_id=row['student_id'],
                        name=row['name'],
                        email=row.get('email', ''),
                        enrollment_date=datetime.now().date()
                    )
                    session.add(student)
                    imported_count += 1
                    
            except Exception as e:
                print(f"⚠️  Error processing student {row['student_id']}: {e}")
                continue
        
        # Commit changes
        session.commit()
        
        print(f"✅ Import completed successfully!")
        print(f"🆕 New students imported: {imported_count}")
        print(f"🔄 Existing students updated: {updated_count}")
        
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import_students_from_csv()