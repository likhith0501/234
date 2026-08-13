"""
Configuration module for the HepatoX Liver Disease Prediction System.
Reads environment variables (with sensible defaults) so the same
codebase runs locally (SQLite + debug) and on Render (env-driven, secure).
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""

    # ---- Core ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "hepatox-dev-secret-key-change-me")

    # ---- Database ----
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = (
        _db_url or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'hepatox.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # ---- Sessions / Security ----
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_TIME_LIMIT = None

    # ---- File storage ----
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
    DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")
    TRAINED_MODELS_FOLDER = os.path.join(BASE_DIR, "trained_models")
    XAI_PLOTS_FOLDER = os.path.join(BASE_DIR, "static", "xai_plots")

    # ---- Admin bootstrap credentials (used only if no admin exists yet) ----
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@hepatox.com")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")

    # ---- ML ----
    RANDOM_STATE = 42
    TEST_SIZE = 0.2
    TARGET_COLUMN = "diagnosis"
    FEATURE_COLUMNS = [
        "age",
        "gender",
        "bmi",
        "alcohol_consumption",
        "smoking",
        "genetic_risk",
        "physical_activity",
        "diabetes",
        "hypertension",
        "liver_function_test",
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
