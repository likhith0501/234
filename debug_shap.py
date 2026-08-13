from app import app
from database import TrainedModel
from utils.xai_utils import SHAPExplainer
from utils.ml_utils import DataPreprocessor
from config import Config
import pandas as pd
import joblib
import os
import shap

with app.app_context():
    model_record = TrainedModel.query.filter_by(is_best=True).first()
    model = joblib.load(model_record.file_path)
    preprocessor = DataPreprocessor.load_preprocessor(os.path.join(Config.TRAINED_MODELS_FOLDER, "preprocessor.pkl"))
    
    patient_data = {
        'age': 45, 'gender': 1, 'bmi': 28.4, 'alcohol_consumption': 1,
        'smoking': 1, 'genetic_risk': 1, 'physical_activity': 1,
        'diabetes': 1, 'hypertension': 0, 'liver_function_test': 233.9
    }
    X = pd.DataFrame([patient_data])
    X_processed, _ = preprocessor.preprocess(X)
    
    background_data = pd.DataFrame({
        col: [X_processed[col].mean()] if col in X_processed.columns else [0]
        for col in Config.FEATURE_COLUMNS
    })
    
    try:
        shap_explainer = SHAPExplainer(model, background_data, Config.FEATURE_COLUMNS)
        shap_explanation = shap_explainer.explain_prediction(X_processed)
        print("Success! SHAP Base Value:", shap_explanation['base_value'])
    except Exception as e:
        import traceback
        traceback.print_exc()
