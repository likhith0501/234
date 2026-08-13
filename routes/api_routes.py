"""
REST API routes for HepatoX.
Provides endpoints for authentication, predictions, patients, and analytics.
"""
import os
import json
import joblib
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required, current_user
import pandas as pd
import numpy as np

from database import db, User, Patient, Prediction, TrainedModel, Report, Log
from config import Config
from utils.ml_utils import DataPreprocessor, Predictor
from utils.xai_utils import SHAPExplainer, LIMEExplainer, FeatureImportance
from utils.report_utils import generate_patient_pdf_report, generate_patient_csv_report, generate_prediction_pdf_report

api = Blueprint('api', __name__, url_prefix='/api/v1')


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api.route('/login', methods=['POST'])
def api_login():
    """API login endpoint."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']) and user.is_active_flag:
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'full_name': user.full_name
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401


@api.route('/register', methods=['POST'])
def api_register():
    """API registration endpoint."""
    data = request.get_json()
    
    # Validation
    required_fields = ['username', 'email', 'password', 'password_confirm']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    if data['password'] != data['password_confirm']:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', ''),
            role='user'
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration error: {str(e)}'}), 500


# ============================================================================
# PATIENT ENDPOINTS
# ============================================================================

@api.route('/patients', methods=['GET'])
@login_required
def get_patients():
    """Get all patients."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Patient.query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=per_page)
    
    patients_data = [p.to_dict() for p in pagination.items]
    
    return jsonify({
        'patients': patients_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@api.route('/patients', methods=['POST'])
@login_required
def create_patient():
    """Create a new patient."""
    data = request.get_json()
    
    try:
        patient = Patient(
            name=data.get('name', ''),
            age=int(data.get('age', 0)),
            gender=data.get('gender', ''),
            bmi=float(data.get('bmi', 0)),
            alcohol_consumption=int(data.get('alcohol_consumption', 0)),
            smoking=int(data.get('smoking', 0)),
            genetic_risk=int(data.get('genetic_risk', 0)),
            physical_activity=int(data.get('physical_activity', 0)),
            diabetes=int(data.get('diabetes', 0)),
            hypertension=int(data.get('hypertension', 0)),
            liver_function_test=float(data.get('liver_function_test', 0)),
            created_by=current_user.id
        )
        
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'message': 'Patient created successfully',
            'patient': patient.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating patient: {str(e)}'}), 500


@api.route('/patients/<int:patient_id>', methods=['GET'])
@login_required
def get_patient(patient_id):
    """Get patient details."""
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict()), 200


@api.route('/patients/<int:patient_id>', methods=['PUT'])
@login_required
def update_patient(patient_id):
    """Update patient information."""
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        patient.name = data['name']
    if 'age' in data:
        patient.age = int(data['age'])
    if 'bmi' in data:
        patient.bmi = float(data['bmi'])
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Patient updated successfully',
            'patient': patient.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating patient: {str(e)}'}), 500


@api.route('/patients/<int:patient_id>', methods=['DELETE'])
@login_required
def delete_patient_api(patient_id):
    """Delete patient and associated records via API."""
    patient = Patient.query.get_or_404(patient_id)
    patient_name = patient.name
    try:
        db.session.delete(patient)
        db.session.commit()
        return jsonify({
            'message': f'Patient {patient_name} deleted successfully',
            'patient_id': patient_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting patient: {str(e)}'}), 500


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@api.route('/predict', methods=['POST'])
@login_required
def predict():
    """Make a prediction for patient."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    patient_id = data.get('patient_id')
    requested_model = data.get('model_name')
    explain = data.get('explain', False)
    
    if not patient_id:
        return jsonify({'error': 'patient_id is required'}), 400
    
    try:
        # Get patient
        patient = Patient.query.get_or_404(patient_id)
        
        # Load model and preprocessor
        selected_model = None
        if requested_model:
            selected_model = TrainedModel.query.filter_by(model_name=requested_model).first()
        if not selected_model:
            selected_model = TrainedModel.query.filter_by(is_best=True).first()
        if not selected_model:
            selected_model = TrainedModel.query.first()
            
        if not selected_model:
            return jsonify({'error': 'No trained model available. Run train_models.py first.'}), 500
        
        if not os.path.exists(selected_model.file_path):
            return jsonify({'error': f'Model file not found: {selected_model.file_path}'}), 500
        
        model = joblib.load(selected_model.file_path)
        preprocessor_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "preprocessor.pkl")
        
        if not os.path.exists(preprocessor_path):
            return jsonify({'error': f'Preprocessor file not found: {preprocessor_path}'}), 500
        
        preprocessor = DataPreprocessor.load_preprocessor(preprocessor_path)
        
        # Prepare patient data
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
        
        # Make prediction
        predictor = Predictor(model, preprocessor)
        prediction_result = predictor.predict(patient_data)
        
        # Save prediction to database
        prediction = Prediction(
            patient_id=patient_id,
            model_used=selected_model.model_name,
            prediction=prediction_result['prediction'],
            probability=prediction_result['probability'],
            confidence_score=prediction_result['confidence_score'],
            risk_level=prediction_result['risk_level'],
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        response = {
            'prediction_id': prediction.id,
            'patient_id': patient_id,
            'model_used': selected_model.model_name,
            'prediction': prediction_result['prediction'],
            'prediction_label': prediction_result['prediction_label'],
            'probability': prediction_result['probability'],
            'confidence_score': prediction_result['confidence_score'],
            'risk_level': prediction_result['risk_level'],
            'timestamp': prediction.created_at.isoformat()
        }
        
        # Add explanations if requested
        if explain:
            try:
                # Prepare data for explanations
                X = pd.DataFrame([patient_data])
                X_processed, _ = preprocessor.preprocess(X)
                
                # For SHAP/LIME, we need to use the preprocessed model predictions
                # Create a simple background data (mean values of features)
                background_data = pd.DataFrame({
                    col: [X_processed[col].mean()] if col in X_processed.columns else [0]
                    for col in Config.FEATURE_COLUMNS
                })
                
                try:
                    # SHAP explanation - use KernelExplainer with background
                    def predict_proba_fn(X):
                        return model.predict_proba(X)
                    
                    shap_explainer = SHAPExplainer(model, background_data, Config.FEATURE_COLUMNS)
                    shap_explanation = shap_explainer.explain_prediction(X_processed)
                    response['shap'] = shap_explanation
                except Exception as shap_error:
                    print(f"SHAP explanation error: {shap_error}")
                    response['shap_error'] = str(shap_error)
                
                try:
                    # LIME explanation
                    lime_explainer = LIMEExplainer(model, X_processed, Config.FEATURE_COLUMNS)
                    lime_explanation = lime_explainer.explain_prediction(X_processed[0:1])
                    response['lime'] = lime_explanation
                except Exception as lime_error:
                    print(f"LIME explanation error: {lime_error}")
                    response['lime_error'] = str(lime_error)
            
            except Exception as e:
                print(f"Error generating explanations: {e}")
                response['explanation_error'] = str(e)
        
        return jsonify(response), 200
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Prediction error: {str(e)}\n{error_trace}")
        db.session.rollback()
        return jsonify({
            'error': f'Prediction error: {str(e)}',
            'details': error_trace if Config.DEBUG else 'Check server logs for details'
        }), 500


@api.route('/predictions/<int:prediction_id>', methods=['GET'])
@login_required
def get_prediction(prediction_id):
    """Get prediction details."""
    prediction = Prediction.query.get_or_404(prediction_id)
    return jsonify(prediction.to_dict()), 200


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@api.route('/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    """Get dashboard statistics for logged-in user."""
    total_patients = Patient.query.count()
    total_predictions = Prediction.query.count()
    disease_cases = Prediction.query.filter_by(prediction=1).count()
    healthy_cases = Prediction.query.filter_by(prediction=0).count()
    
    best_model = TrainedModel.query.filter_by(is_best=True).first()
    
    stats = {
        'total_patients': total_patients,
        'total_predictions': total_predictions,
        'disease_cases': disease_cases,
        'healthy_cases': healthy_cases,
        'accuracy': round(best_model.accuracy, 4) if best_model else 0,
        'roc_auc': round(best_model.roc_auc, 4) if best_model else 0,
        'best_model': best_model.model_name if best_model else None,
    }
    
    return jsonify(stats), 200


@api.route('/dashboard/recent-predictions', methods=['GET'])
@login_required
def recent_predictions():
    """Get recent predictions."""
    limit = request.args.get('limit', 10, type=int)
    predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'predictions': [p.to_dict() for p in predictions]
    }), 200


@api.route('/dashboard/prediction-distribution', methods=['GET'])
@login_required
def prediction_distribution():
    """Get distribution of predictions by risk level."""
    distribution = db.session.query(
        Prediction.risk_level,
        db.func.count(Prediction.id)
    ).group_by(Prediction.risk_level).all()
    
    data = {
        'labels': [d[0] for d in distribution],
        'values': [d[1] for d in distribution]
    }
    
    return jsonify(data), 200


# ============================================================================
# MODEL ENDPOINTS
# ============================================================================

@api.route('/models', methods=['GET'])
@login_required
def get_models():
    """Get all trained models."""
    models = TrainedModel.query.all()
    return jsonify({
        'models': [m.to_dict() for m in models]
    }), 200


@api.route('/models/best', methods=['GET'])
@login_required
def get_best_model():
    """Get best trained model."""
    best_model = TrainedModel.query.filter_by(is_best=True).first()
    
    if not best_model:
        return jsonify({'error': 'No model found'}), 404
    
    return jsonify(best_model.to_dict()), 200


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@api.route('/analytics/age-distribution', methods=['GET'])
@login_required
def age_distribution():
    """Get distribution of patient ages."""
    age_bins = [0, 20, 30, 40, 50, 60, 70, 80, 100]
    age_labels = ['<20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80+']
    
    ages = [p.age for p in Patient.query.all()]
    
    if not ages:
        return jsonify({'labels': age_labels, 'values': [0] * len(age_labels)}), 200
    
    df = pd.DataFrame({'age': ages})
    distribution = pd.cut(df['age'], bins=age_bins, labels=age_labels).value_counts().sort_index()
    
    return jsonify({
        'labels': list(distribution.index.astype(str)),
        'values': list(distribution.values)
    }), 200


@api.route('/analytics/gender-distribution', methods=['GET'])
@login_required
def gender_distribution():
    """Get distribution of patient genders."""
    distribution = db.session.query(
        Patient.gender,
        db.func.count(Patient.id)
    ).group_by(Patient.gender).all()
    
    return jsonify({
        'labels': [d[0] for d in distribution],
        'values': [d[1] for d in distribution]
    }), 200


@api.route('/analytics/model-comparison', methods=['GET'])
@login_required
def model_comparison():
    """Get model comparison metrics."""
    models = TrainedModel.query.all()
    
    metrics = {
        'labels': [m.model_name for m in models],
        'accuracy': [m.accuracy or 0 for m in models],
        'precision': [m.precision or 0 for m in models],
        'recall': [m.recall or 0 for m in models],
        'f1_score': [m.f1_score or 0 for m in models],
        'roc_auc': [m.roc_auc or 0 for m in models],
    }
    
    return jsonify(metrics), 200


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================

@api.route('/history/predictions', methods=['GET'])
@login_required
def prediction_history():
    """Get prediction history with optional filters."""
    patient_id = request.args.get('patient_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    query = Prediction.query
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    # Filter by date
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Prediction.created_at >= start_date)
    
    predictions = query.order_by(Prediction.created_at.desc()).all()
    
    return jsonify({
        'predictions': [p.to_dict() for p in predictions],
        'total': len(predictions)
    }), 200


# ============================================================================
# HEALTH CHECK
# ============================================================================

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============================================================================
# REPORT API ENDPOINTS
# ============================================================================

@api.route('/patients/<int:patient_id>/report/pdf', methods=['GET'])
@login_required
def api_patient_pdf_report(patient_id):
    """API endpoint to download patient PDF report."""
    patient = Patient.query.get_or_404(patient_id)
    predictions = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.created_at.desc()).all()
    pdf_bytes = generate_patient_pdf_report(patient, predictions)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Report_Patient_{patient_id}.pdf'
    return response


@api.route('/patients/<int:patient_id>/report/csv', methods=['GET'])
@login_required
def api_patient_csv_report(patient_id):
    """API endpoint to download patient CSV data."""
    patient = Patient.query.get_or_404(patient_id)
    predictions = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.created_at.desc()).all()
    csv_data = generate_patient_csv_report(patient, predictions)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Data_Patient_{patient_id}.csv'
    return response


@api.route('/predictions/<int:prediction_id>/report/pdf', methods=['GET'])
@login_required
def api_prediction_pdf_report(prediction_id):
    """API endpoint to download single prediction PDF report."""
    prediction = Prediction.query.get_or_404(prediction_id)
    patient = Patient.query.get(prediction.patient_id)
    pdf_bytes = generate_prediction_pdf_report(prediction, patient)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Scan_{prediction_id}_Report.pdf'
    return response

