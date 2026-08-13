"""
Machine Learning utilities for HepatoX.
Includes preprocessing, model training, and evaluation functions.
"""
import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, BaggingClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
import xgboost as xgb
import lightgbm as lgb

from config import Config


class DataPreprocessor:
    """Handle data preprocessing tasks."""
    
    def __init__(self, feature_columns=None, target_column="diagnosis"):
        self.feature_columns = feature_columns or Config.FEATURE_COLUMNS
        self.target_column = target_column
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
    
    def preprocess(self, df):
        """
        Preprocess dataset: handle missing values, encode, scale.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            tuple: (X, y) preprocessed features and target
        """
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Encode categorical variables
        df = self._encode_categorical(df)
        
        # Extract features and target
        X = df[self.feature_columns].copy()
        y = df[self.target_column].copy() if self.target_column in df.columns else None
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X = pd.DataFrame(X_scaled, columns=self.feature_columns)
        
        return X, y
    
    def _handle_missing_values(self, df):
        """Handle missing values in dataframe."""
        # Fill numeric columns with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Fill categorical columns with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna(df[col].mode()[0] if len(df[col].mode()) > 0 else 'Unknown')
        
        return df
    
    def _encode_categorical(self, df):
        """Encode categorical variables."""
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))
        
        return df
    
    def save_preprocessor(self, filepath):
        """Save preprocessor for future use."""
        joblib.dump({
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
        }, filepath)
    
    @staticmethod
    def load_preprocessor(filepath):
        """Load saved preprocessor."""
        data = joblib.load(filepath)
        preprocessor = DataPreprocessor(
            feature_columns=data['feature_columns']
        )
        preprocessor.scaler = data['scaler']
        preprocessor.label_encoders = data['label_encoders']
        return preprocessor


class ModelTrainer:
    """Train and evaluate multiple ML models."""
    
    def __init__(self, random_state=Config.RANDOM_STATE, test_size=Config.TEST_SIZE):
        self.random_state = random_state
        self.test_size = test_size
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None
    
    def prepare_data(self, X, y):
        """Split data into train and test sets."""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
        )
        return X_train, X_test, y_train, y_test
    
    def build_models(self):
        """Build all ML models."""
        self.models = {
            'Logistic Regression': LogisticRegression(random_state=self.random_state, max_iter=1000),
            'Decision Tree': DecisionTreeClassifier(random_state=self.random_state),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=self.random_state),
            'AdaBoost': AdaBoostClassifier(n_estimators=50, random_state=self.random_state),
            'XGBoost': xgb.XGBClassifier(random_state=self.random_state, eval_metric='logloss'),
            'LightGBM': lgb.LGBMClassifier(random_state=self.random_state, verbose=-1),
            'SVM': SVC(probability=True, random_state=self.random_state),
            'KNN': KNeighborsClassifier(n_neighbors=5),
            'Bagging': BaggingClassifier(random_state=self.random_state),
        }
    
    def train_models(self, X_train, X_test, y_train, y_test):
        """Train all models and evaluate."""
        self.results = {}
        
        for model_name, model in self.models.items():
            try:
                print(f"Training {model_name}...")
                
                # Train model
                model.fit(X_train, y_train)
                
                # Predictions
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                
                # Metrics
                metrics = {
                    'accuracy': accuracy_score(y_test, y_pred),
                    'precision': precision_score(y_test, y_pred),
                    'recall': recall_score(y_test, y_pred),
                    'f1_score': f1_score(y_test, y_pred),
                    'roc_auc': roc_auc_score(y_test, y_pred_proba),
                    'y_pred': y_pred,
                    'y_pred_proba': y_pred_proba,
                    'y_test': y_test,
                }
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
                metrics['cv_mean'] = cv_scores.mean()
                metrics['cv_std'] = cv_scores.std()
                
                self.results[model_name] = metrics
                print(f"[OK] {model_name}: Accuracy={metrics['accuracy']:.4f}, ROC-AUC={metrics['roc_auc']:.4f}")
                
            except Exception as e:
                print(f"[ERR] Error training {model_name}: {str(e)}")
        
        # Find best model
        self._find_best_model()
    
    def _find_best_model(self):
        """Find the best performing model based on ROC-AUC."""
        if not self.results:
            return
        
        best_roc_auc = -1
        for model_name, metrics in self.results.items():
            if metrics['roc_auc'] > best_roc_auc:
                best_roc_auc = metrics['roc_auc']
                self.best_model_name = model_name
        
        self.best_model = self.models[self.best_model_name]
        print(f"\n[OK] Best Model: {self.best_model_name} (ROC-AUC: {best_roc_auc:.4f})")
    
    def get_model_comparison(self):
        """Get comparison of all models."""
        comparison = []
        for model_name, metrics in self.results.items():
            comparison.append({
                'Model': model_name,
                'Accuracy': round(metrics['accuracy'], 4),
                'Precision': round(metrics['precision'], 4),
                'Recall': round(metrics['recall'], 4),
                'F1-Score': round(metrics['f1_score'], 4),
                'ROC-AUC': round(metrics['roc_auc'], 4),
                'CV Mean': round(metrics['cv_mean'], 4),
            })
        
        return pd.DataFrame(comparison).sort_values('ROC-AUC', ascending=False)
    
    def save_model(self, model_name, filepath):
        """Save trained model."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        joblib.dump(self.models[model_name], filepath)
        print(f"[OK] Model saved to {filepath}")
    
    @staticmethod
    def load_model(filepath):
        """Load saved model."""
        return joblib.load(filepath)


class Predictor:
    """Make predictions with trained model."""
    
    def __init__(self, model, preprocessor):
        self.model = model
        self.preprocessor = preprocessor
    
    def predict(self, patient_data):
        """
        Make prediction for patient.
        
        Args:
            patient_data (dict): Patient features
            
        Returns:
            dict: Prediction results
        """
        # Convert to dataframe
        df = pd.DataFrame([patient_data])
        
        # Preprocess
        X, _ = self.preprocessor.preprocess(df)
        
        # Predict
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0, 1]
        
        # Confidence score
        confidence = max(self.model.predict_proba(X)[0])
        
        # Risk level
        if probability >= 0.7:
            risk_level = "High"
        elif probability >= 0.4:
            risk_level = "Moderate"
        else:
            risk_level = "Low"
        
        return {
            'prediction': int(prediction),
            'prediction_label': 'Liver Disease' if prediction == 1 else 'Healthy',
            'probability': float(probability),
            'confidence_score': float(confidence),
            'risk_level': risk_level,
        }
