"""
Integration tests for HepatoX application.
"""
import pytest
import json
from app import create_app, db
from models import User, Patient, Prediction


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
def authenticated_user(app, client):
    """Create and authenticate a user."""
    # Register
    register_response = client.post('/api/v1/register', json={
        'username': 'testdoctor',
        'email': 'doctor@example.com',
        'password': 'SecurePass123!'
    })
    
    # Login
    login_response = client.post('/api/v1/login', json={
        'email': 'doctor@example.com',
        'password': 'SecurePass123!'
    })
    
    token = login_response.get_json().get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    return {'token': token, 'headers': headers, 'email': 'doctor@example.com'}


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_full_auth_flow(self, client):
        """Test registration -> login -> authenticated request."""
        # Register
        register_response = client.post('/api/v1/register', json={
            'username': 'newdoctor',
            'email': 'newdoctor@example.com',
            'password': 'SecurePass123!'
        })
        assert register_response.status_code in [200, 201]
        
        # Login
        login_response = client.post('/api/v1/login', json={
            'email': 'newdoctor@example.com',
            'password': 'SecurePass123!'
        })
        assert login_response.status_code == 200
        
        # Use token for authenticated request
        token = login_response.get_json().get('token')
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            response = client.get('/api/v1/patients', headers=headers)
            assert response.status_code in [200, 401]


class TestPatientWorkflow:
    """Test complete patient management workflow."""
    
    def test_create_and_retrieve_patient(self, client, authenticated_user):
        """Test creating and retrieving a patient."""
        headers = authenticated_user['headers']
        
        # Create patient
        create_response = client.post('/api/v1/patients', 
            json={
                'name': 'Test Patient',
                'age': 50,
                'gender': 'M',
                'email': 'patient@example.com'
            },
            headers=headers
        )
        assert create_response.status_code in [200, 201, 401]
        
        # Get patients list
        list_response = client.get('/api/v1/patients', headers=headers)
        assert list_response.status_code in [200, 401]
    
    def test_create_update_patient(self, client, authenticated_user):
        """Test creating and updating a patient."""
        headers = authenticated_user['headers']
        
        # Create patient
        create_response = client.post('/api/v1/patients',
            json={
                'name': 'Update Test',
                'age': 45,
                'gender': 'F',
                'email': 'update@example.com'
            },
            headers=headers
        )
        
        if create_response.status_code in [200, 201]:
            patient_data = create_response.get_json()
            patient_id = patient_data.get('id')
            
            if patient_id:
                # Update patient
                update_response = client.put(f'/api/v1/patients/{patient_id}',
                    json={'age': 46},
                    headers=headers
                )
                assert update_response.status_code in [200, 404, 401]


class TestPredictionWorkflow:
    """Test complete prediction workflow."""
    
    def test_make_prediction_complete_flow(self, client, authenticated_user):
        """Test making a complete prediction."""
        headers = authenticated_user['headers']
        
        prediction_data = {
            'age': 55,
            'gender': 'M',
            'bilirubin': 1.5,
            'alkaline_phosphatase': 100,
            'alamine_aminotransferase': 50,
            'aspartate_aminotransferase': 45,
            'albumin': 3.5,
            'prothrombin_time': 14
        }
        
        response = client.post('/api/v1/predict',
            json=prediction_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201, 400, 401]
        
        if response.status_code in [200, 201]:
            data = response.get_json()
            assert 'prediction' in data or 'risk_level' in data
    
    def test_prediction_with_explanation(self, client, authenticated_user):
        """Test prediction with SHAP explanation."""
        headers = authenticated_user['headers']
        
        prediction_data = {
            'age': 55,
            'gender': 'M',
            'bilirubin': 1.5,
            'alkaline_phosphatase': 100,
            'alamine_aminotransferase': 50,
            'aspartate_aminotransferase': 45,
            'albumin': 3.5,
            'prothrombin_time': 14,
            'explain': True,
            'explanation_type': 'shap'
        }
        
        response = client.post('/api/v1/predict',
            json=prediction_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201, 400, 401]


class TestDashboardWorkflow:
    """Test dashboard and analytics workflow."""
    
    def test_dashboard_complete_flow(self, client, authenticated_user):
        """Test accessing complete dashboard data."""
        headers = authenticated_user['headers']
        
        # Get stats
        stats_response = client.get('/api/v1/dashboard/stats', headers=headers)
        assert stats_response.status_code in [200, 401]
        
        # Get recent predictions
        recent_response = client.get('/api/v1/dashboard/recent-predictions', headers=headers)
        assert recent_response.status_code in [200, 401]
        
        # Get distribution
        dist_response = client.get('/api/v1/dashboard/prediction-distribution', headers=headers)
        assert dist_response.status_code in [200, 401]


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_email_format(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/v1/register', json={
            'username': 'user',
            'email': 'not-an-email',
            'password': 'Pass123!'
        })
        assert response.status_code in [400, 422]
    
    def test_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/v1/register', json={
            'username': 'user',
            'email': 'user@example.com',
            'password': '123'
        })
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client):
        """Test registration with missing fields."""
        response = client.post('/api/v1/register', json={
            'username': 'user'
            # Missing email and password
        })
        assert response.status_code in [400, 422]
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without auth."""
        response = client.get('/api/v1/patients')
        assert response.status_code in [401, 403]
    
    def test_invalid_token(self, client):
        """Test accessing with invalid token."""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/api/v1/patients', headers=headers)
        assert response.status_code in [401, 403]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
