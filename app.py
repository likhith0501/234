"""
HepatoX - AI-Powered Liver Disease Prediction System
Main application file with Flask setup and core routes.
"""
import os
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_cors import CORS

from config import Config
from database import db, bcrypt, User, Patient, Prediction, TrainedModel, Report, Log
from utils.report_utils import generate_patient_pdf_report, generate_patient_csv_report, generate_prediction_pdf_report

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
CORS(app)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register blueprints
from routes.api_routes import api
app.register_blueprint(api)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def log_action(action, description, status="success", user_id=None):
    """Log user actions to database."""
    try:
        if user_id is None and current_user.is_authenticated:
            user_id = current_user.id
        log_entry = Log(user_id=user_id, action=action, description=description, status=status)
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")


# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================

@app.context_processor
def inject_user():
    """Inject current user into template context."""
    return {"current_user": current_user}


@app.context_processor
def utility_processor():
    """Inject utility functions into templates."""
    return dict(datetime=datetime)


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route("/")
def index():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page and logic."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("login"))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_active_flag:
                login_user(user, remember=request.form.get("remember_me"))
                log_action("login", f"User {username} logged in", "success", user.id)
                next_page = request.args.get("next")
                return redirect(next_page) if next_page else redirect(url_for("dashboard"))
            else:
                flash("Your account has been deactivated.", "error")
                log_action("login_attempt", f"Attempt to login with deactivated account: {username}", "error")
        else:
            flash("Invalid username or password.", "error")
            log_action("login_attempt", f"Failed login attempt for username: {username}", "error")
    
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration page and logic."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        full_name = request.form.get("full_name", "").strip()
        
        # Validation
        if not all([username, email, password, password_confirm]):
            flash("All fields are required.", "error")
            return redirect(url_for("register"))
        
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("register"))
        
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("register"))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("register"))
        
        # Create new user
        try:
            user = User(username=username, email=email, full_name=full_name, role="user")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            log_action("register", f"New user registered: {username}", "success", user.id)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Registration error: {str(e)}", "error")
            log_action("register", f"Registration error for {username}: {str(e)}", "error")
    
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    """User logout."""
    username = current_user.username
    logout_user()
    log_action("logout", f"User {username} logged out", "success")
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Forgot password page - placeholder for email integration."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # TODO: Implement email sending functionality
            flash("Check your email for password reset instructions.", "info")
            log_action("forgot_password", f"Password reset requested for {email}", "success")
        else:
            # Security: don't reveal whether email exists
            flash("If an account exists with that email, you will receive reset instructions.", "info")
    
    return render_template("forgot_password.html")


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard - shows stats and recent predictions."""
    try:
        total_patients = Patient.query.count()
        total_predictions = Prediction.query.count()
        disease_cases = Prediction.query.filter_by(prediction=1).count()
        healthy_cases = Prediction.query.filter_by(prediction=0).count()
        recent_predictions = (
            Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all()
        )
        
        # Get best model
        best_model = TrainedModel.query.filter_by(is_best=True).first()
        
        stats = {
            "total_patients": total_patients,
            "total_predictions": total_predictions,
            "disease_cases": disease_cases,
            "healthy_cases": healthy_cases,
            "accuracy": round(best_model.accuracy, 4) if best_model else 0,
            "roc_auc": round(best_model.roc_auc, 4) if best_model else 0,
        }
        
        return render_template(
            "dashboard.html",
            stats=stats,
            recent_predictions=recent_predictions,
            best_model=best_model
        )
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "error")
        return render_template("dashboard.html", stats={}, recent_predictions=[])


# ============================================================================
# PATIENT MANAGEMENT
# ============================================================================

@app.route("/patients")
@login_required
def patients():
    """List all patients."""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    
    pagination = Patient.query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=per_page)
    patients_list = pagination.items
    
    return render_template("patients.html", patients=patients_list, pagination=pagination)


@app.route("/patients/register", methods=["GET", "POST"])
@login_required
def register_patient():
    """Register a new patient."""
    if request.method == "POST":
        try:
            def safe_int(val):
                return int(float(val)) if val else 0
            
            patient = Patient(
                name=request.form.get("name", "").strip(),
                age=safe_int(request.form.get("age", 0)),
                gender=request.form.get("gender", ""),
                bmi=float(request.form.get("bmi", 0)),
                alcohol_consumption=safe_int(request.form.get("alcohol_consumption", 0)),
                smoking=safe_int(request.form.get("smoking", 0)),
                genetic_risk=safe_int(request.form.get("genetic_risk", 0)),
                physical_activity=safe_int(request.form.get("physical_activity", 0)),
                diabetes=safe_int(request.form.get("diabetes", 0)),
                hypertension=safe_int(request.form.get("hypertension", 0)),
                liver_function_test=float(request.form.get("liver_function_test", 0)),
                created_by=current_user.id,
            )
            
            db.session.add(patient)
            db.session.commit()
            
            log_action("patient_register", f"Patient registered: {patient.name}", "success", current_user.id)
            flash(f"Patient {patient.name} registered successfully!", "success")
            return redirect(url_for("patients"))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering patient: {str(e)}", "error")
            log_action("patient_register", f"Error: {str(e)}", "error", current_user.id)
    
    return render_template("register_patient.html")


@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    """View patient details and predictions."""
    patient = Patient.query.get_or_404(patient_id)
    predictions = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.created_at.desc()).all()
    
    return render_template("patient_detail.html", patient=patient, predictions=predictions)


@app.route("/patients/<int:patient_id>/delete", methods=["POST"])
@login_required
def delete_patient(patient_id):
    """Delete a patient and associated records."""
    try:
        patient = Patient.query.get_or_404(patient_id)
        patient_name = patient.name
        
        db.session.delete(patient)
        db.session.commit()
        
        log_action("patient_delete", f"Deleted patient: {patient_name} (ID: {patient_id})", "success", current_user.id)
        flash(f"Patient '{patient_name}' deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting patient: {str(e)}", "error")
        log_action("patient_delete", f"Error deleting patient ID {patient_id}: {str(e)}", "error", current_user.id)
        
    return redirect(url_for("patients"))


@app.route("/predictions/<int:prediction_id>/delete", methods=["POST"])
@login_required
def delete_prediction(prediction_id):
    """Delete a prediction record."""
    patient_id = None
    try:
        prediction = Prediction.query.get_or_404(prediction_id)
        patient_id = prediction.patient_id
        
        db.session.delete(prediction)
        db.session.commit()
        
        log_action("prediction_delete", f"Deleted prediction ID: {prediction_id}", "success", current_user.id)
        flash("Prediction record deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting prediction: {str(e)}", "error")
        
    if patient_id:
        return redirect(url_for("patient_detail", patient_id=patient_id))
    return redirect(url_for("dashboard"))


# ============================================================================
# PREDICTION
# ============================================================================

@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    """Prediction page - select patient and model."""
    patients_list = Patient.query.order_by(Patient.name).all()
    models_list = TrainedModel.query.order_by(TrainedModel.roc_auc.desc()).all()
    return render_template("predict.html", patients=patients_list, models=models_list)


# ============================================================================
# REPORT DOWNLOAD ROUTES
# ============================================================================

@app.route("/patients/<int:patient_id>/report/pdf")
@login_required
def download_patient_pdf_report(patient_id):
    """Download PDF diagnostic report for patient."""
    try:
        patient = Patient.query.get_or_404(patient_id)
        predictions = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.created_at.desc()).all()
        logo_path = os.path.join(app.static_folder, "images", "liver_logo.jpg")
        
        pdf_bytes = generate_patient_pdf_report(patient, predictions, logo_path)
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Report_Patient_{patient_id}.pdf'
        
        log_action("report_download_pdf", f"Downloaded PDF report for patient #{patient_id}", "success", current_user.id)
        return response
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", "error")
        return redirect(url_for("patient_detail", patient_id=patient_id))


@app.route("/patients/<int:patient_id>/report/csv")
@login_required
def download_patient_csv_report(patient_id):
    """Download CSV clinical data report for patient."""
    try:
        patient = Patient.query.get_or_404(patient_id)
        predictions = Prediction.query.filter_by(patient_id=patient_id).order_by(Prediction.created_at.desc()).all()
        
        csv_data = generate_patient_csv_report(patient, predictions)
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Data_Patient_{patient_id}.csv'
        
        log_action("report_download_csv", f"Downloaded CSV report for patient #{patient_id}", "success", current_user.id)
        return response
    except Exception as e:
        flash(f"Error generating CSV report: {str(e)}", "error")
        return redirect(url_for("patient_detail", patient_id=patient_id))


@app.route("/predictions/<int:prediction_id>/report/pdf")
@login_required
def download_prediction_pdf_report(prediction_id):
    """Download PDF report for a single prediction scan."""
    try:
        prediction = Prediction.query.get_or_404(prediction_id)
        patient = Patient.query.get(prediction.patient_id)
        logo_path = os.path.join(app.static_folder, "images", "liver_logo.jpg")
        
        pdf_bytes = generate_prediction_pdf_report(prediction, patient, logo_path)
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=HepatoX_Scan_{prediction_id}_Report.pdf'
        
        log_action("prediction_report_download", f"Downloaded PDF report for prediction scan #{prediction_id}", "success", current_user.id)
        return response
    except Exception as e:
        flash(f"Error generating prediction PDF report: {str(e)}", "error")
        return redirect(url_for("dashboard"))



# ============================================================================
# ADMIN PANEL
# ============================================================================

@app.route("/admin")
@login_required
@admin_required
def admin():
    """Admin dashboard."""
    users_count = User.query.count()
    patients_count = Patient.query.count()
    predictions_count = Prediction.query.count()
    models_count = TrainedModel.query.count()
    
    stats = {
        "users_count": users_count,
        "patients_count": patients_count,
        "predictions_count": predictions_count,
        "models_count": models_count,
    }
    
    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """Manage users."""
    page = request.args.get("page", 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template("admin/users.html", users=users)


@app.route("/admin/models")
@login_required
@admin_required
def admin_models():
    """Manage trained models."""
    models = TrainedModel.query.all()
    return render_template("admin/models.html", models=models)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template("errors/500.html"), 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return render_template("errors/403.html"), 403


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def setup_db():
    """Initialize the database and create default admin user."""
    db.create_all()
    
    # Create default admin if it doesn't exist
    admin_exists = User.query.filter_by(username=app.config["DEFAULT_ADMIN_USERNAME"]).first()
    
    if not admin_exists:
        admin = User(
            username=app.config["DEFAULT_ADMIN_USERNAME"],
            email=app.config["DEFAULT_ADMIN_EMAIL"],
            full_name="Administrator",
            role="admin"
        )
        admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        print(f"[OK] Database initialized and admin user created (username: {admin.username})")
    else:
        print("[OK] Database initialized (admin user already exists)")


@app.cli.command("init-db")
def init_db():
    """Initialize the database and create default admin user."""
    setup_db()


# ============================================================================
# CREATE REQUIRED FOLDERS
# ============================================================================

def create_app_folders():
    """Create required application folders."""
    folders = [
        app.config["UPLOAD_FOLDER"],
        app.config["REPORTS_FOLDER"],
        app.config["DATASET_FOLDER"],
        app.config["TRAINED_MODELS_FOLDER"],
        app.config["XAI_PLOTS_FOLDER"],
        os.path.join(app.root_path, "instance"),
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

# Ensure folders exist when application starts
with app.app_context():
    create_app_folders()


# ============================================================================
# APP CONTEXT
# ============================================================================

@app.before_request
def before_request():
    """Run before each request."""
    session.permanent = True
    app.permanent_session_lifetime = app.config["PERMANENT_SESSION_LIFETIME"]


if __name__ == "__main__":
    with app.app_context():
        setup_db()
    
    app.run(debug=True, host="0.0.0.0", port=5000)

