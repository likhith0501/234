#!/usr/bin/env python
"""Test the prediction API endpoint."""

from app import app, db
from database import User
from flask_login import login_user
import json

print("Testing Prediction API...\n")

# Use app context to create a test user and make requests
with app.app_context():
    # Get or create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("✗ Admin user not found!")
        exit(1)
    
    with app.test_client() as client:
        # Login through the web form or login route
        login_resp = client.post('/login', data={
            'username': 'admin',
            'password': 'Admin@123'
        }, follow_redirects=True)
        
        print(f"[1] Login attempt - Status: {login_resp.status_code}")
        
        # Test prediction without explanation
        print("\n[2] Testing prediction API (without explanation)...")
        response = client.post('/api/v1/predict',
            json={'patient_id': 1, 'explain': False},
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print("[OK] Prediction successful!")
            print(f"  Prediction: {data.get('prediction_label')}")
            print(f"  Probability: {data.get('probability'):.4f}")
            print(f"  Risk Level: {data.get('risk_level')}")
        else:
            data = response.get_json() if response.is_json else {}
            print(f"[ERR] Error (status {response.status_code}): {data.get('error') if data else response.data}")
        
        # Test prediction with explanation
        print("\n[3] Testing prediction API (with explanation)...")
        response = client.post('/api/v1/predict',
            json={'patient_id': 1, 'explain': True},
            content_type='application/json'
        )
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print("[OK] Prediction with XAI successful!")
            print(f"  Has SHAP: {'shap' in data}")
            print(f"  Has LIME: {'lime' in data}")
        else:
            data = response.get_json() if response.is_json else {}
            print(f"[ERR] Error (status {response.status_code}): {data.get('error') if data else response.data}")

        # Test Patient PDF Report API
        print("\n[4] Testing Patient PDF Report API...")
        pdf_resp = client.get('/api/v1/patients/1/report/pdf')
        print(f"PDF Report Status: {pdf_resp.status_code}")
        if pdf_resp.status_code == 200 and pdf_resp.mimetype == 'application/pdf':
            print(f"[OK] Patient PDF report API returned {len(pdf_resp.data)} bytes")
        else:
            print(f"[ERR] PDF Report API failed: {pdf_resp.status_code}")

        # Test Patient CSV Report API
        print("\n[5] Testing Patient CSV Report API...")
        csv_resp = client.get('/api/v1/patients/1/report/csv')
        print(f"CSV Report Status: {csv_resp.status_code}")
        if csv_resp.status_code == 200 and csv_resp.mimetype == 'text/csv':
            print(f"[OK] Patient CSV report API returned {len(csv_resp.data)} bytes")
        else:
            print(f"[ERR] CSV Report API failed: {csv_resp.status_code}")

    print("\n[OK] API VERIFICATION COMPLETE!")
