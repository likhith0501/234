"""
Unit tests for deep learning models.
"""
import pytest
import numpy as np
import pandas as pd
from utils.deep_learning_utils import (
    DeepLearningPredictor,
    EnsembleDeepLearning,
    create_transfer_learning_model
)
from config import Config


@pytest.fixture
def sample_data():
    """Create sample training data."""
    np.random.seed(42)
    n_samples = 100
    n_features = len(Config.FEATURE_COLUMNS)
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    # Split into train/test
    split = int(0.8 * n_samples)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    return X_train, X_test, y_train, y_test


class TestDeepLearningPredictor:
    """Test DeepLearningPredictor class."""
    
    def test_initialization(self):
        """Test model initialization."""
        predictor = DeepLearningPredictor(model_type='dense')
        assert predictor.model_type == 'dense'
        assert predictor.model is None
    
    def test_build_dense_model(self):
        """Test building dense model."""
        predictor = DeepLearningPredictor(model_type='dense', input_dim=10)
        model = predictor.build_model()
        assert model is not None
        assert predictor.model is not None
    
    def test_build_dropout_model(self):
        """Test building dropout model."""
        predictor = DeepLearningPredictor(model_type='dropout', input_dim=10)
        model = predictor.build_model()
        assert model is not None
    
    def test_build_batchnorm_model(self):
        """Test building batch normalization model."""
        predictor = DeepLearningPredictor(model_type='batchnorm', input_dim=10)
        model = predictor.build_model()
        assert model is not None
    
    def test_build_complex_model(self):
        """Test building complex model."""
        predictor = DeepLearningPredictor(model_type='complex', input_dim=10)
        model = predictor.build_model()
        assert model is not None
    
    def test_invalid_model_type(self):
        """Test invalid model type."""
        predictor = DeepLearningPredictor(model_type='invalid', input_dim=10)
        with pytest.raises(ValueError):
            predictor.build_model()
    
    def test_train_model(self, sample_data):
        """Test model training."""
        X_train, X_test, y_train, y_test = sample_data
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X_train.shape[1])
        predictor.build_model()
        
        history = predictor.train(X_train, y_train, epochs=5, batch_size=16)
        assert history is not None
    
    def test_predict(self, sample_data):
        """Test prediction."""
        X_train, X_test, y_train, y_test = sample_data
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X_train.shape[1])
        predictor.build_model()
        predictor.train(X_train, y_train, epochs=5, batch_size=16)
        
        predictions = predictor.predict(X_test)
        assert predictions.shape[0] == X_test.shape[0]
        assert np.all(predictions >= 0) and np.all(predictions <= 1)
    
    def test_evaluate(self, sample_data):
        """Test model evaluation."""
        X_train, X_test, y_train, y_test = sample_data
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X_train.shape[1])
        predictor.build_model()
        predictor.train(X_train, y_train, epochs=5, batch_size=16)
        
        metrics = predictor.evaluate(X_test, y_test)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'roc_auc' in metrics
    
    def test_model_summary(self):
        """Test getting model summary."""
        predictor = DeepLearningPredictor(model_type='dense', input_dim=10)
        predictor.build_model()
        summary = predictor.get_model_summary()
        assert summary is not None
        assert len(summary) > 0


class TestEnsembleDeepLearning:
    """Test EnsembleDeepLearning class."""
    
    def test_initialization(self):
        """Test ensemble initialization."""
        ensemble = EnsembleDeepLearning(input_dim=10)
        assert ensemble.input_dim == 10
        assert len(ensemble.models) == 0
    
    def test_build_all_models(self):
        """Test building all models in ensemble."""
        ensemble = EnsembleDeepLearning(input_dim=10)
        ensemble.build_all_models()
        assert len(ensemble.models) == 4  # dense, dropout, batchnorm, complex
    
    def test_train_all_models(self, sample_data):
        """Test training all ensemble models."""
        X_train, X_test, y_train, y_test = sample_data
        
        ensemble = EnsembleDeepLearning(input_dim=X_train.shape[1])
        results = ensemble.train_all(X_train, y_train, X_test, y_test, epochs=5, batch_size=16)
        
        assert len(results) == 4
        for model_type, history in results.items():
            assert history is not None
    
    def test_evaluate_all_models(self, sample_data):
        """Test evaluating all ensemble models."""
        X_train, X_test, y_train, y_test = sample_data
        
        ensemble = EnsembleDeepLearning(input_dim=X_train.shape[1])
        ensemble.train_all(X_train, y_train, X_test, y_test, epochs=5, batch_size=16)
        
        results = ensemble.evaluate_all(X_test, y_test)
        assert len(results) == 4
        for model_type, metrics in results.items():
            assert 'accuracy' in metrics
            assert 'f1' in metrics
    
    def test_ensemble_prediction_averaging(self, sample_data):
        """Test ensemble prediction with averaging."""
        X_train, X_test, y_train, y_test = sample_data
        
        ensemble = EnsembleDeepLearning(input_dim=X_train.shape[1])
        ensemble.train_all(X_train, y_train, X_test, y_test, epochs=5, batch_size=16)
        
        predictions = ensemble.predict_ensemble(X_test)
        assert predictions.shape[0] == X_test.shape[0]
        assert np.all(predictions >= 0) and np.all(predictions <= 1)
    
    def test_ensemble_prediction_voting(self, sample_data):
        """Test ensemble prediction with voting."""
        X_train, X_test, y_train, y_test = sample_data
        
        ensemble = EnsembleDeepLearning(input_dim=X_train.shape[1])
        ensemble.train_all(X_train, y_train, X_test, y_test, epochs=5, batch_size=16)
        
        predictions = ensemble.predict_ensemble_voting(X_test)
        assert predictions.shape[0] == X_test.shape[0]
        assert np.all(np.isin(predictions, [0, 1]))


class TestTransferLearning:
    """Test transfer learning models."""
    
    def test_create_transfer_learning_model(self):
        """Test creating transfer learning model."""
        model = create_transfer_learning_model(base_model_name='mobilenet', input_dim=10)
        assert model is not None
    
    def test_transfer_learning_model_shape(self):
        """Test transfer learning model output shape."""
        model = create_transfer_learning_model(base_model_name='mobilenet', input_dim=10, num_classes=1)
        assert model is not None
        assert model.input_shape[1] == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
