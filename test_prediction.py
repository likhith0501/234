#!/usr/bin/env python
"""Test prediction flow to debug errors."""

from app import app, db
from database import Patient, TrainedModel
from utils.ml_utils import DataPreprocessor, Predictor
from config import Config
import joblib
import os
import pandas as pd

with app.app_context():
    print("Testing prediction flow...\n")
    
    # 1. Check patients
    print("[1] Checking patients...")
    patients = Patient.query.all()
    if patients:
        print(f"[OK] Found {len(patients)} patient(s)")
        patient = patients[0]
        print(f"  Using patient: {patient.name} (ID: {patient.id})")
    else:
        print("[ERR] No patients found! Register a patient first.")
        exit(1)
    
    # 2. Check best model
    print("\n[2] Checking best model...")
    best_model = TrainedModel.query.filter_by(is_best=True).first()
    if best_model:
        print(f"[OK] Best model: {best_model.model_name}")
        print(f"  File: {best_model.file_path}")
        print(f"  Exists: {os.path.exists(best_model.file_path)}")
    else:
        print("[ERR] No best model found!")
        exit(1)
    
    # 3. Load model
    print("\n[3] Loading model...")
    try:
        model = joblib.load(best_model.file_path)
        print(f"[OK] Model loaded: {type(model).__name__}")
    except Exception as e:
        print(f"[ERR] Error loading model: {e}")
        exit(1)
    
    # 4. Load preprocessor
    print("\n[4] Loading preprocessor...")
    try:
        preprocessor_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "preprocessor.pkl")
        preprocessor = DataPreprocessor.load_preprocessor(preprocessor_path)
        print(f"[OK] Preprocessor loaded")
        print(f"  Feature columns: {preprocessor.feature_columns}")
    except Exception as e:
        print(f"[ERR] Error loading preprocessor: {e}")
        exit(1)
    
    # 5. Prepare patient data
    print("\n[5] Preparing patient data...")
    try:
        patient_data = {
            'age': patient.age,
            'gender': patient.gender,
            'bmi': patient.bmi,
            'alcohol_consumption': patient.alcohol_consumption,
            'smoking': patient.smoking,
            'genetic_risk': patient.genetic_risk,
            'physical_activity': patient.physical_activity,
            'diabetes': patient.diabetes,
            'hypertension': patient.hypertension,
            'liver_function_test': patient.liver_function_test,
        }
        print(f"[OK] Patient data prepared:")
        for key, val in patient_data.items():
            print(f"  {key}: {val} ({type(val).__name__})")
    except Exception as e:
        print(f"[ERR] Error preparing patient data: {e}")
        exit(1)
    
    # 6. Make prediction
    print("\n[6] Making prediction...")
    try:
        predictor = Predictor(model, preprocessor)
        result = predictor.predict(patient_data)
        print(f"[OK] Prediction successful!")
        print(f"  Prediction: {result['prediction_label']}")
        print(f"  Probability: {result['probability']:.4f}")
        print(f"  Confidence: {result['confidence_score']:.4f}")
        print(f"  Risk Level: {result['risk_level']}")
    except Exception as e:
        print(f"[ERR] Error making prediction: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n[OK] ALL TESTS PASSED!")
