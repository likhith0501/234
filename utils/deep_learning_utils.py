"""
Deep Learning utilities for HepatoX.
Includes TensorFlow/Keras neural network models for liver disease prediction.
"""
import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Sequential, models
    from tensorflow.keras.optimizers import Adam, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input
    from tensorflow.keras.regularizers import l2
    HAS_TENSORFLOW = True
except ImportError:
    tf = None
    keras = None
    HAS_TENSORFLOW = False

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)

from config import Config


class DeepLearningPredictor:
    """Manage deep learning models for binary classification."""
    
    def __init__(self, model_type='dense', input_dim=None):
        """
        Initialize deep learning model.
        
        Args:
            model_type (str): Type of model ('dense', 'dropout', 'batchnorm', 'complex')
            input_dim (int): Number of input features
        """
        self.model_type = model_type
        self.input_dim = input_dim or len(Config.FEATURE_COLUMNS)
        self.model = None
        self.scaler = StandardScaler()
        self.history = None
        self.metrics = {}
        
    def build_dense_model(self):
        """Build a simple dense neural network."""
        model = Sequential([
            Input(shape=(self.input_dim,)),
            Dense(128, activation='relu'),
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        return model
    
    def build_dropout_model(self):
        """Build a neural network with dropout for regularization."""
        model = Sequential([
            Input(shape=(self.input_dim,)),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(128, activation='relu'),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        return model
    
    def build_batchnorm_model(self):
        """Build a neural network with batch normalization."""
        model = Sequential([
            Input(shape=(self.input_dim,)),
            Dense(256, activation='relu'),
            BatchNormalization(),
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dense(32, activation='relu'),
            BatchNormalization(),
            Dense(1, activation='sigmoid')
        ])
        return model
    
    def build_complex_model(self):
        """Build a complex neural network with multiple regularization techniques."""
        model = Sequential([
            Input(shape=(self.input_dim,)),
            Dense(512, activation='relu', kernel_regularizer=l2(0.001)),
            BatchNormalization(),
            Dropout(0.4),
            Dense(256, activation='relu', kernel_regularizer=l2(0.001)),
            BatchNormalization(),
            Dropout(0.3),
            Dense(128, activation='relu', kernel_regularizer=l2(0.001)),
            BatchNormalization(),
            Dropout(0.2),
            Dense(64, activation='relu', kernel_regularizer=l2(0.001)),
            Dropout(0.1),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        return model
    
    def build_model(self):
        """Build model based on specified type."""
        if self.model_type == 'dense':
            self.model = self.build_dense_model()
        elif self.model_type == 'dropout':
            self.model = self.build_dropout_model()
        elif self.model_type == 'batchnorm':
            self.model = self.build_batchnorm_model()
        elif self.model_type == 'complex':
            self.model = self.build_complex_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Compile model
        optimizer = Adam(learning_rate=0.001)
        self.model.compile(
            optimizer=optimizer,
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )
        
        return self.model
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=100, batch_size=32):
        """
        Train the neural network.
        
        Args:
            X_train (np.array): Training features
            y_train (np.array): Training labels
            X_val (np.array): Validation features
            y_val (np.array): Validation labels
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            
        Returns:
            dict: Training history
        """
        if self.model is None:
            self.build_model()
        
        # Prepare callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
            ModelCheckpoint('best_model.h5', monitor='val_auc', save_best_only=True, mode='max')
        ]
        
        # Train model
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return self.history
    
    def predict(self, X):
        """
        Make predictions.
        
        Args:
            X (np.array): Features to predict
            
        Returns:
            np.array: Probability predictions
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        predictions = self.model.predict(X)
        return predictions.flatten()
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance.
        
        Args:
            X_test (np.array): Test features
            y_test (np.array): Test labels
            
        Returns:
            dict: Evaluation metrics
        """
        # Get predictions
        y_pred_proba = self.predict(X_test)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        self.metrics = metrics
        return metrics
    
    def save_model(self, filepath):
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save")
        self.model.save(filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load model from disk."""
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")
    
    def get_model_summary(self):
        """Get model summary."""
        if self.model is None:
            return None
        summary_list = []
        self.model.summary(print_fn=lambda x: summary_list.append(x))
        return '\n'.join(summary_list)


class EnsembleDeepLearning:
    """Ensemble of multiple deep learning models."""
    
    def __init__(self, input_dim=None):
        """Initialize ensemble."""
        self.input_dim = input_dim or len(Config.FEATURE_COLUMNS)
        self.models = {}
        self.model_types = ['dense', 'dropout', 'batchnorm', 'complex']
        
    def build_all_models(self):
        """Build all model variants."""
        for model_type in self.model_types:
            predictor = DeepLearningPredictor(model_type=model_type, input_dim=self.input_dim)
            predictor.build_model()
            self.models[model_type] = predictor
    
    def train_all(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32):
        """Train all models."""
        if not self.models:
            self.build_all_models()
        
        results = {}
        for model_type, predictor in self.models.items():
            print(f"\nTraining {model_type} model...")
            predictor.train(X_train, y_train, X_val, y_val, epochs, batch_size)
            results[model_type] = predictor.history
        
        return results
    
    def evaluate_all(self, X_test, y_test):
        """Evaluate all models."""
        results = {}
        for model_type, predictor in self.models.items():
            results[model_type] = predictor.evaluate(X_test, y_test)
        return results
    
    def predict_ensemble(self, X):
        """Make ensemble predictions (average of all models)."""
        predictions = []
        for predictor in self.models.values():
            pred = predictor.predict(X)
            predictions.append(pred)
        
        # Average predictions
        ensemble_pred = np.mean(predictions, axis=0)
        return ensemble_pred
    
    def predict_ensemble_voting(self, X):
        """Make ensemble predictions (majority voting)."""
        predictions = []
        for predictor in self.models.values():
            pred = (predictor.predict(X) > 0.5).astype(int)
            predictions.append(pred)
        
        # Majority voting
        voting_pred = np.round(np.mean(predictions, axis=0)).astype(int)
        return voting_pred
    
    def save_all_models(self, directory):
        """Save all models to directory."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        for model_type, predictor in self.models.items():
            filepath = os.path.join(directory, f'dl_{model_type}_model.h5')
            predictor.save_model(filepath)
    
    def load_all_models(self, directory):
        """Load all models from directory."""
        for model_type in self.model_types:
            filepath = os.path.join(directory, f'dl_{model_type}_model.h5')
            if os.path.exists(filepath):
                predictor = DeepLearningPredictor(model_type=model_type, input_dim=self.input_dim)
                predictor.load_model(filepath)
                self.models[model_type] = predictor


def create_transfer_learning_model(base_model_name='mobilenet', input_dim=None, num_classes=1):
    """
    Create a transfer learning model using pre-trained architecture.
    
    Args:
        base_model_name (str): Name of base model
        input_dim (int): Number of input features
        num_classes (int): Number of output classes
        
    Returns:
        keras.Model: Transfer learning model
    """
    # For tabular data, we'll use a pre-built architecture as base
    # This is simplified; for true transfer learning, use image models
    
    if base_model_name == 'mobilenet':
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(128, activation='relu'),
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(num_classes, activation='sigmoid' if num_classes == 1 else 'softmax')
        ])
    else:
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(100, activation='relu'),
            Dense(50, activation='relu'),
            Dense(num_classes, activation='sigmoid' if num_classes == 1 else 'softmax')
        ])
    
    return model


if __name__ == "__main__":
    print("Deep Learning utilities loaded successfully")
