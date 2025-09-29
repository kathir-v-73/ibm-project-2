#!/usr/bin/env python3
"""
TechKey Analysis - Model Training Script
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import get_session
from src.models import Student, Grade
from src.predictor import prepare_training_data


def train_model():
    """Train the prediction model and save it."""
    print("🔬 Starting model training...")
    
    # Get database session
    session = get_session()
    
    try:
        # Prepare training data
        print("📊 Preparing training data...")
        X, y, feature_names = prepare_training_data(session)
        
        if X.shape[0] == 0:
            print("❌ No training data available.")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📈 Training samples: {X_train.shape[0]}")
        print(f"📊 Test samples: {X_test.shape[0]}")
        
        # Train model
        print("🤖 Training Random Forest model...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained successfully!")
        print(f"📊 Accuracy: {accuracy:.3f}")
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        model_path = project_root / 'data' / 'trained_model.pkl'
        joblib.dump(model, model_path)
        print(f"💾 Model saved to: {model_path}")
        
        # Save feature names
        feature_info = {
            'feature_names': feature_names,
            'accuracy': accuracy
        }
        joblib.dump(feature_info, project_root / 'data' / 'feature_info.pkl')
        
        print("🎉 Model training completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during model training: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    train_model()