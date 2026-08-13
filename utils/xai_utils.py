"""
Explainable AI (XAI) utilities for HepatoX.
Includes SHAP and LIME implementations for model interpretability.
"""
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import lime
import lime.lime_tabular
import joblib
import os
from datetime import datetime

from config import Config


class SHAPExplainer:
    """SHAP-based model explanations."""
    
    def __init__(self, model, X_train, feature_names):
        """
        Initialize SHAP explainer.
        
        Args:
            model: Trained ML model
            X_train: Training data for background
            feature_names: List of feature names
        """
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        
        # Use Tree explainer for tree-based models, KernelExplainer otherwise
        model_type = type(model).__name__
        if 'XGB' in model_type or 'LGBM' in model_type or 'Forest' in model_type or 'Tree' in model_type:
            self.explainer = shap.TreeExplainer(model)
        else:
            self.explainer = shap.KernelExplainer(model.predict_proba, shap.sample(X_train, 100))
    
    def explain_prediction(self, X, patient_index=0):
        """
        Explain a single prediction using SHAP.
        
        Args:
            X: Feature data (can be single sample or multiple)
            patient_index: Index of patient to explain (if multiple)
            
        Returns:
            dict: SHAP explanation
        """
        shap_values = self.explainer.shap_values(X)
        
        # Handle different output formats
        if isinstance(shap_values, list):
            # For binary classification, use positive class
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        
        if len(shap_values.shape) > 1:
            shap_values = shap_values[patient_index]
        
        # Get base value
        if hasattr(self.explainer, 'expected_value'):
            base_val = self.explainer.expected_value
            while isinstance(base_val, (list, np.ndarray)):
                base_val = base_val[-1] if len(base_val) > 1 else base_val[0]
            base_value = float(base_val)
        else:
            base_value = 0.0
        
        # Create explanation dictionary
        explanation = {
            'base_value': base_value,
            'shap_values': shap_values.tolist() if hasattr(shap_values, 'tolist') else list(shap_values),
            'features': self.feature_names,
            'feature_values': X.iloc[patient_index].tolist() if hasattr(X, 'iloc') else X[patient_index].tolist(),
        }
        
        # Calculate top features
        feature_importance = []
        for i in range(len(self.feature_names)):
            val = shap_values[i]
            if hasattr(val, 'item'):
                val = val.item()
            elif isinstance(val, (list, np.ndarray)):
                val = float(val[0])
            else:
                val = float(val)
                
            feat_val = explanation['feature_values'][i]
            if hasattr(feat_val, 'item'):
                feat_val = feat_val.item()
            else:
                feat_val = float(feat_val)

            feature_importance.append({
                'feature': self.feature_names[i],
                'shap_value': abs(float(val)),
                'contribution': float(val),
                'feature_value': float(feat_val)
            })
        
        explanation['top_features'] = sorted(
            feature_importance, key=lambda x: x['shap_value'], reverse=True
        )[:10]
        
        return explanation
    
    def plot_summary(self, X, output_path):
        """Generate SHAP summary plot."""
        try:
            shap_values = self.explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, X, feature_names=self.feature_names, show=False)
            plt.tight_layout()
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"Error generating SHAP summary plot: {e}")
            return False
    
    def plot_decision(self, X, patient_index=0, output_path=None):
        """Generate SHAP decision plot."""
        try:
            shap_values = self.explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            plt.figure(figsize=(12, 6))
            shap.decision_plot(
                self.explainer.expected_value if isinstance(self.explainer.expected_value, (int, float)) else 0.5,
                shap_values[patient_index:patient_index+1],
                X.iloc[patient_index:patient_index+1] if hasattr(X, 'iloc') else X[patient_index:patient_index+1],
                feature_names=self.feature_names,
                show=False
            )
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=100, bbox_inches='tight')
            
            plt.close()
            return True
        except Exception as e:
            print(f"Error generating SHAP decision plot: {e}")
            return False


class LIMEExplainer:
    """LIME-based model explanations."""
    
    def __init__(self, model, X_train, feature_names, mode='classification'):
        """
        Initialize LIME explainer.
        
        Args:
            model: Trained ML model
            X_train: Training data
            feature_names: List of feature names
            mode: 'classification' or 'regression'
        """
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        self.mode = mode
        
        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X_train.values if hasattr(X_train, 'values') else X_train,
            feature_names=feature_names,
            class_names=['Healthy', 'Liver Disease'],
            mode=mode,
            random_state=42
        )
    
    def explain_prediction(self, X, patient_index=0, num_features=10):
        """
        Explain a single prediction using LIME.
        
        Args:
            X: Feature data
            patient_index: Index of patient to explain
            num_features: Number of features to explain
            
        Returns:
            dict: LIME explanation
        """
        # Get instance to explain
        if hasattr(X, 'values'):
            instance = X.values[patient_index]
        else:
            instance = X[patient_index]
        
        # Get explanation
        exp = self.explainer.explain_instance(
            instance,
            self.model.predict_proba,
            num_features=num_features
        )
        
        # Extract explanation
        lime_explanation = exp.as_list()
        
        # Parse and structure explanation
        features_with_values = []
        for feature_desc, weight in lime_explanation:
            features_with_values.append({
                'feature_description': feature_desc,
                'weight': float(weight),
                'importance': 'positive' if weight > 0 else 'negative'
            })
        
        # Get prediction
        pred_proba = self.model.predict_proba([instance])
        prediction = np.argmax(pred_proba[0])
        
        explanation = {
            'prediction': int(prediction),
            'prediction_label': 'Liver Disease' if prediction == 1 else 'Healthy',
            'probabilities': {
                'healthy': float(pred_proba[0, 0]),
                'disease': float(pred_proba[0, 1])
            },
            'top_features': features_with_values[:5],
            'all_features': features_with_values,
        }
        
        return explanation
    
    def plot_explanation(self, X, patient_index=0, output_path=None):
        """Generate LIME explanation visualization."""
        try:
            if hasattr(X, 'values'):
                instance = X.values[patient_index]
            else:
                instance = X[patient_index]
            
            exp = self.explainer.explain_instance(
                instance,
                self.model.predict_proba,
                num_features=10
            )
            
            # Save plot
            if output_path:
                fig = exp.as_pyplot_figure()
                fig.savefig(output_path, dpi=100, bbox_inches='tight')
                plt.close(fig)
            
            return True
        except Exception as e:
            print(f"Error generating LIME plot: {e}")
            return False


class FeatureImportance:
    """Extract feature importance from different model types."""
    
    @staticmethod
    def get_importance(model, feature_names):
        """
        Extract feature importance from model.
        
        Args:
            model: Trained ML model
            feature_names: List of feature names
            
        Returns:
            pd.DataFrame: Feature importance ranking
        """
        importance_dict = {}
        model_type = type(model).__name__
        
        try:
            # Tree-based models
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(feature_names, model.feature_importances_))
            
            # Coefficient-based models (Logistic Regression, SVM)
            elif hasattr(model, 'coef_'):
                coef = np.abs(model.coef_[0] if model.coef_.ndim > 1 else model.coef_)
                importance_dict = dict(zip(feature_names, coef))
            
            # Permutation importance (fallback)
            else:
                return pd.DataFrame({
                    'Feature': feature_names,
                    'Importance': [0] * len(feature_names)
                })
        
        except Exception as e:
            print(f"Error extracting importance: {e}")
            return pd.DataFrame({
                'Feature': feature_names,
                'Importance': [0] * len(feature_names)
            })
        
        # Create dataframe and sort
        if importance_dict:
            df = pd.DataFrame({
                'Feature': list(importance_dict.keys()),
                'Importance': list(importance_dict.values())
            })
            df['Importance'] = df['Importance'].abs()
            df = df.sort_values('Importance', ascending=False)
            df['Normalized_Importance'] = df['Importance'] / df['Importance'].sum()
            return df
        
        return pd.DataFrame({
            'Feature': feature_names,
            'Importance': [0] * len(feature_names)
        })


def plot_feature_importance(feature_importance_df, output_path, top_n=10):
    """Plot top N most important features."""
    try:
        df = feature_importance_df.head(top_n).copy()
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, y='Feature', x='Importance', palette='viridis')
        plt.title(f'Top {top_n} Most Important Features')
        plt.xlabel('Importance Score')
        plt.ylabel('Features')
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"Error plotting feature importance: {e}")
        return False
