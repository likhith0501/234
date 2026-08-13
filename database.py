"""
Database module for HepatoX.
Defines the SQLAlchemy instance and all ORM models:
Users, Patients, Predictions, Models, Reports, Logs.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' or 'admin'
    full_name = db.Column(db.String(120))
    reset_token = db.Column(db.String(255))
    is_active_flag = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patients = db.relationship("Patient", backref="created_by_user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # Male / Female
    bmi = db.Column(db.Float, nullable=False)
    alcohol_consumption = db.Column(db.Integer, nullable=False)  # 0/1
    smoking = db.Column(db.Integer, nullable=False)  # 0/1
    genetic_risk = db.Column(db.Integer, nullable=False)  # 0/1
    physical_activity = db.Column(db.Integer, nullable=False)  # 0=Low,1=Moderate,2=High
    diabetes = db.Column(db.Integer, nullable=False)  # 0/1
    hypertension = db.Column(db.Integer, nullable=False)  # 0/1
    liver_function_test = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    predictions = db.relationship(
        "Prediction", backref="patient", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "bmi": self.bmi,
            "alcohol_consumption": self.alcohol_consumption,
            "smoking": self.smoking,
            "genetic_risk": self.genetic_risk,
            "physical_activity": self.physical_activity,
            "diabetes": self.diabetes,
            "hypertension": self.hypertension,
            "liver_function_test": self.liver_function_test,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    model_used = db.Column(db.String(80))
    prediction = db.Column(db.Integer, nullable=False)  # 0=Healthy 1=Disease
    probability = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20))  # Low / Moderate / High
    shap_summary = db.Column(db.Text)  # JSON string of top SHAP features
    lime_summary = db.Column(db.Text)  # JSON string of top LIME features
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "model_used": self.model_used,
            "prediction": "Liver Disease" if self.prediction == 1 else "Healthy",
            "probability": round(self.probability, 4),
            "confidence_score": round(self.confidence_score, 4),
            "risk_level": self.risk_level,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class TrainedModel(db.Model):
    __tablename__ = "trained_models"

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(80), unique=True, nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    roc_auc = db.Column(db.Float)
    is_best = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "accuracy": round(self.accuracy, 4) if self.accuracy else None,
            "precision": round(self.precision, 4) if self.precision else None,
            "recall": round(self.recall, 4) if self.recall else None,
            "f1_score": round(self.f1_score, 4) if self.f1_score else None,
            "roc_auc": round(self.roc_auc, 4) if self.roc_auc else None,
            "is_best": self.is_best,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"), nullable=False)
    report_type = db.Column(db.String(20))  # 'pdf' or 'csv'
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "prediction_id": self.prediction_id,
            "report_type": self.report_type,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(255))
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # 'success' or 'error'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }
