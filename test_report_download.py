#!/usr/bin/env python
"""
Test report download generation for HepatoX.
Verifies that PDF and CSV clinical reports are correctly built without errors.
"""
import os
import sys

from app import app, db
from database import Patient, Prediction
from utils.report_utils import (
    generate_patient_pdf_report,
    generate_patient_csv_report,
    generate_prediction_pdf_report
)

def test_reports():
    print("=" * 60)
    print("HEPATOX REPORT GENERATION VERIFICATION TEST")
    print("=" * 60)
    
    with app.app_context():
        # Fetch or create a test patient
        patient = Patient.query.first()
        if not patient:
            print("[!] No patient found in database. Creating test patient...")
            patient = Patient(
                name="John Doe",
                age=45,
                gender="Male",
                bmi=26.4,
                alcohol_consumption=1,
                smoking=0,
                genetic_risk=1,
                physical_activity=1,
                diabetes=0,
                hypertension=1,
                liver_function_test=3.25
            )
            db.session.add(patient)
            db.session.commit()
            print(f"[OK] Created test patient: {patient.name} (ID: {patient.id})")
        else:
            print(f"[OK] Using existing patient: {patient.name} (ID: {patient.id})")
            
        predictions = Prediction.query.filter_by(patient_id=patient.id).all()
        print(f"[OK] Found {len(predictions)} prediction scan(s) for patient #{patient.id}")
        
        # 1. Test Patient PDF Report Generation
        print("\n[1] Testing Patient PDF Report Generation...")
        logo_path = os.path.join(app.static_folder, "images", "liver_logo.jpg")
        pdf_bytes = generate_patient_pdf_report(patient, predictions, logo_path=logo_path)
        assert pdf_bytes and len(pdf_bytes) > 500, "PDF bytes generation failed or output too small"
        print(f"[OK] Patient PDF generated successfully ({len(pdf_bytes)} bytes)")
        
        # 2. Test Patient CSV Report Generation
        print("\n[2] Testing Patient CSV Report Generation...")
        csv_data = generate_patient_csv_report(patient, predictions)
        assert "PATIENT INFORMATION" in csv_data and patient.name in csv_data, "CSV report generation failed"
        print(f"[OK] Patient CSV generated successfully ({len(csv_data)} bytes)")
        
        # 3. Test Prediction PDF Report Generation
        if predictions:
            pred = predictions[0]
            print(f"\n[3] Testing Single Prediction Scan PDF Generation for Prediction #{pred.id}...")
            pred_pdf_bytes = generate_prediction_pdf_report(pred, patient, logo_path=logo_path)
            assert pred_pdf_bytes and len(pred_pdf_bytes) > 500, "Single Prediction PDF generation failed"
            print(f"[OK] Prediction PDF generated successfully ({len(pred_pdf_bytes)} bytes)")
        else:
            print("\n[3] Creating temporary prediction record for single scan PDF test...")
            pred = Prediction(
                patient_id=patient.id,
                model_used="Logistic Regression",
                prediction=1,
                probability=0.7850,
                confidence_score=0.8200,
                risk_level="High"
            )
            db.session.add(pred)
            db.session.commit()
            pred_pdf_bytes = generate_prediction_pdf_report(pred, patient, logo_path=logo_path)
            assert pred_pdf_bytes and len(pred_pdf_bytes) > 500, "Single Prediction PDF generation failed"
            print(f"[OK] Prediction PDF generated successfully ({len(pred_pdf_bytes)} bytes)")

        print("\n" + "=" * 60)
        print("[OK] ALL REPORT TESTS PASSED PERFECTLY!")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    test_reports()
