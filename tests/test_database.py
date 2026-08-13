"""
Unit tests for database models and operations.
"""
import pytest
from datetime import datetime
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


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, app):
        """Test creating a user."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            retrieved_user = User.query.filter_by(username='testuser').first()
            assert retrieved_user is not None
            assert retrieved_user.email == 'test@example.com'
    
    def test_user_password_hashing(self, app):
        """Test password hashing."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('SecurePassword123!')
            
            assert user.check_password('SecurePassword123!')
            assert not user.check_password('WrongPassword')
    
    def test_user_unique_email(self, app):
        """Test email uniqueness constraint."""
        with app.app_context():
            user1 = User(username='user1', email='duplicate@example.com')
            user1.set_password('pass123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='user2', email='duplicate@example.com')
            user2.set_password('pass123')
            db.session.add(user2)
            
            with pytest.raises(Exception):
                db.session.commit()


class TestPatientModel:
    """Test Patient model."""
    
    def test_create_patient(self, app):
        """Test creating a patient."""
        with app.app_context():
            # Create user first
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            # Create patient
            patient = Patient(
                name='John Doe',
                age=45,
                gender='M',
                email='patient@example.com',
                user_id=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            retrieved = Patient.query.filter_by(name='John Doe').first()
            assert retrieved is not None
            assert retrieved.age == 45
    
    def test_patient_relationships(self, app):
        """Test patient relationships."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                name='Jane Doe',
                age=50,
                gender='F',
                email='jane@example.com',
                user_id=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            retrieved_user = User.query.get(user.id)
            assert len(retrieved_user.patients) > 0
            assert retrieved_user.patients[0].name == 'Jane Doe'


class TestPredictionModel:
    """Test Prediction model."""
    
    def test_create_prediction(self, app):
        """Test creating a prediction."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                name='John Doe',
                age=45,
                gender='M',
                email='patient@example.com',
                user_id=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            prediction = Prediction(
                patient_id=patient.id,
                prediction_value=0.75,
                risk_level='high',
                model_used='random_forest'
            )
            db.session.add(prediction)
            db.session.commit()
            
            retrieved = Prediction.query.filter_by(patient_id=patient.id).first()
            assert retrieved is not None
            assert retrieved.prediction_value == 0.75
    
    def test_prediction_relationships(self, app):
        """Test prediction relationships."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                name='Jane Doe',
                age=50,
                gender='F',
                email='jane@example.com',
                user_id=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            prediction = Prediction(
                patient_id=patient.id,
                prediction_value=0.85,
                risk_level='high',
                model_used='xgboost'
            )
            db.session.add(prediction)
            db.session.commit()
            
            retrieved_patient = Patient.query.get(patient.id)
            assert len(retrieved_patient.predictions) > 0


class TestDatabaseOperations:
    """Test database operations."""
    
    def test_bulk_create_users(self, app):
        """Test bulk creating users."""
        with app.app_context():
            users = []
            for i in range(10):
                user = User(
                    username=f'user{i}',
                    email=f'user{i}@example.com'
                )
                user.set_password('pass123')
                users.append(user)
            
            db.session.add_all(users)
            db.session.commit()
            
            count = User.query.count()
            assert count == 10
    
    def test_query_filtering(self, app):
        """Test query filtering."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            patients = []
            for i in range(5):
                patient = Patient(
                    name=f'Patient {i}',
                    age=40 + i,
                    gender='M' if i % 2 == 0 else 'F',
                    email=f'patient{i}@example.com',
                    user_id=user.id
                )
                patients.append(patient)
            
            db.session.add_all(patients)
            db.session.commit()
            
            male_patients = Patient.query.filter_by(gender='M').all()
            assert len(male_patients) > 0
    
    def test_update_operation(self, app):
        """Test updating records."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                name='John Doe',
                age=45,
                gender='M',
                email='patient@example.com',
                user_id=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            patient.age = 46
            db.session.commit()
            
            updated = Patient.query.get(patient.id)
            assert updated.age == 46
    
    def test_delete_operation(self, app):
        """Test deleting records."""
        with app.app_context():
            user = User(username='doctor', email='doctor@example.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            user_id = user.id
            User.query.filter_by(id=user_id).delete()
            db.session.commit()
            
            deleted = User.query.get(user_id)
            assert deleted is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
