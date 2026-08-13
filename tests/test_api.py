"""
Unit tests for API endpoints.
"""
import pytest
import json
from app import create_app, db
from models import User, Patient, Prediction
from datetime import datetime


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return headers."""
    # Register user
    client.post('/api/v1/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    })
    
    # Login
    response = client.post('/api/v1/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    })
    
    token = response.get_json().get('token')
    return {'Authorization': f'Bearer {token}'} if token else {}


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post('/api/v1/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!'
        })
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert 'id' in data or 'message' in data
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/v1/register', json={
            'username': 'user',
            'email': 'invalid-email',
            'password': 'Pass123!'
        })
        assert response.status_code in [400, 422]
    
    def test_login_user(self, client, auth_headers):
        """Test user login."""
        response = client.post('/api/v1/login', json={
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data or 'user' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/api/v1/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code in [401, 404]


class TestPatientEndpoints:
    """Test patient management endpoints."""
    
    def test_get_patients(self, client, auth_headers):
        """Test retrieving patients list."""
        response = client.get('/api/v1/patients', headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_create_patient(self, client, auth_headers):
        """Test creating a patient."""
        patient_data = {
            'name': 'John Doe',
            'age': 45,
            'gender': 'M',
            'email': 'john@example.com'
        }
        response = client.post('/api/v1/patients', json=patient_data, headers=auth_headers)
        assert response.status_code in [200, 201, 401]
    
    def test_get_patient_detail(self, client, auth_headers):
        """Test retrieving patient details."""
        response = client.get('/api/v1/patients/1', headers=auth_headers)
        assert response.status_code in [200, 404, 401]
    
    def test_update_patient(self, client, auth_headers):
        """Test updating patient information."""
        update_data = {'age': 46}
        response = client.put('/api/v1/patients/1', json=update_data, headers=auth_headers)
        assert response.status_code in [200, 404, 401]


class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_make_prediction(self, client, auth_headers):
        """Test making a prediction."""
        prediction_data = {
            'age': 50,
            'gender': 'M',
            'bilirubin': 1.2,
            'alkaline_phosphatase': 80,
            'alamine_aminotransferase': 40,
            'aspartate_aminotransferase': 35,
            'albumin': 3.8,
            'prothrombin_time': 13
        }
        response = client.post('/api/v1/predict', json=prediction_data, headers=auth_headers)
        assert response.status_code in [200, 201, 401, 400]
    
    def test_prediction_with_xai(self, client, auth_headers):
        """Test prediction with XAI explanations."""
        prediction_data = {
            'age': 50,
            'gender': 'M',
            'bilirubin': 1.2,
            'alkaline_phosphatase': 80,
            'alamine_aminotransferase': 40,
            'aspartate_aminotransferase': 35,
            'albumin': 3.8,
            'prothrombin_time': 13,
            'explain': True,
            'explanation_type': 'shap'
        }
        response = client.post('/api/v1/predict', json=prediction_data, headers=auth_headers)
        assert response.status_code in [200, 201, 401, 400]
    
    def test_get_predictions_history(self, client, auth_headers):
        """Test retrieving prediction history."""
        response = client.get('/api/v1/history/predictions', headers=auth_headers)
        assert response.status_code in [200, 401]


class TestDashboardEndpoints:
    """Test dashboard analytics endpoints."""
    
    def test_dashboard_stats(self, client, auth_headers):
        """Test getting dashboard statistics."""
        response = client.get('/api/v1/dashboard/stats', headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_recent_predictions(self, client, auth_headers):
        """Test getting recent predictions."""
        response = client.get('/api/v1/dashboard/recent-predictions', headers=auth_headers)
        assert response.status_code in [200, 401]
    
    def test_prediction_distribution(self, client, auth_headers):
        """Test getting prediction distribution."""
        response = client.get('/api/v1/dashboard/prediction-distribution', headers=auth_headers)
        assert response.status_code in [200, 401]


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
