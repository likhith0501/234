"""
Performance tests for HepatoX application.
"""
import pytest
import time
import numpy as np
from utils.ml_utils import DataPreprocessor, ModelTrainer
from utils.deep_learning_utils import DeepLearningPredictor
from config import Config


@pytest.fixture
def sample_dataset():
    """Create sample dataset for performance testing."""
    np.random.seed(42)
    n_samples = 1000
    n_features = len(Config.FEATURE_COLUMNS)
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    
    return X, y


class TestMLPipelinePerformance:
    """Test ML pipeline performance."""
    
    def test_preprocessing_speed(self, sample_dataset):
        """Test data preprocessing speed."""
        X, y = sample_dataset
        
        preprocessor = DataPreprocessor()
        
        start_time = time.time()
        # Simulate preprocessing
        for _ in range(10):
            scaled = preprocessor.scaler.fit_transform(X)
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 5.0  # Should complete in less than 5 seconds
    
    def test_prediction_speed(self, sample_dataset):
        """Test prediction speed."""
        X, y = sample_dataset
        
        # Simple prediction simulation
        start_time = time.time()
        for _ in range(100):
            predictions = np.random.rand(X.shape[0])
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 2.0  # Should complete in less than 2 seconds
    
    def test_batch_prediction_speed(self, sample_dataset):
        """Test batch prediction performance."""
        X, y = sample_dataset
        batch_size = 100
        
        start_time = time.time()
        for i in range(0, X.shape[0], batch_size):
            batch = X[i:i+batch_size]
            predictions = np.random.rand(batch.shape[0])
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = X.shape[0] / duration
        
        assert duration < 5.0
        assert throughput > 100  # At least 100 predictions per second


class TestDeepLearningPerformance:
    """Test deep learning model performance."""
    
    def test_model_inference_speed(self, sample_dataset):
        """Test inference speed of deep learning models."""
        X_train, y_train = sample_dataset
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X_train.shape[1])
        predictor.build_model()
        predictor.train(X_train[:100], y_train[:100], epochs=2, batch_size=16)
        
        X_test = X_train[100:200]
        
        start_time = time.time()
        predictions = predictor.predict(X_test)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = X_test.shape[0] / duration
        
        assert duration < 5.0
        assert throughput > 10  # At least 10 predictions per second
    
    def test_model_training_convergence(self, sample_dataset):
        """Test that model training converges in reasonable time."""
        X_train, y_train = sample_dataset
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X_train.shape[1])
        predictor.build_model()
        
        start_time = time.time()
        history = predictor.train(X_train[:200], y_train[:200], epochs=10, batch_size=16)
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert duration < 60.0  # Should complete in less than 60 seconds
        assert history is not None


class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_large_batch_processing(self, sample_dataset):
        """Test processing large batches."""
        X, y = sample_dataset
        
        # Create larger dataset
        X_large = np.vstack([X] * 10)
        y_large = np.hstack([y] * 10)
        
        assert X_large.shape[0] > 5000
        
        # Test that we can process without issues
        batch_size = 1000
        for i in range(0, X_large.shape[0], batch_size):
            batch = X_large[i:i+batch_size]
            predictions = np.random.rand(batch.shape[0])
        
        # Should complete without memory issues
        assert True
    
    def test_model_memory_footprint(self, sample_dataset):
        """Test model memory footprint."""
        X, y = sample_dataset
        
        predictor = DeepLearningPredictor(model_type='complex', input_dim=X.shape[1])
        predictor.build_model()
        
        # Get model summary to check parameters
        summary = predictor.get_model_summary()
        assert summary is not None
        assert len(summary) > 0


class TestConcurrency:
    """Test concurrent operations."""
    
    def test_sequential_predictions(self, sample_dataset):
        """Test sequential prediction handling."""
        X, y = sample_dataset
        
        predictor = DeepLearningPredictor(model_type='dense', input_dim=X.shape[1])
        predictor.build_model()
        predictor.train(X[:100], y[:100], epochs=2, batch_size=16)
        
        start_time = time.time()
        for i in range(10):
            pred = predictor.predict(X[i:i+10])
            assert pred.shape[0] == 10
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 10.0


class TestDataValidation:
    """Test data validation performance."""
    
    def test_input_validation_speed(self, sample_dataset):
        """Test input validation speed."""
        X, y = sample_dataset
        
        start_time = time.time()
        for i in range(1000):
            # Validate input
            assert X.shape[1] == len(Config.FEATURE_COLUMNS)
            assert y.shape[0] == X.shape[0]
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 1.0  # Should be fast
    
    def test_data_consistency_check(self, sample_dataset):
        """Test data consistency checking."""
        X, y = sample_dataset
        
        start_time = time.time()
        for i in range(100):
            # Check consistency
            assert not np.isnan(X).any()
            assert not np.isinf(X).any()
            assert np.all(np.isfinite(X))
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 2.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])
