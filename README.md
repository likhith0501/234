# HepatoX - AI-Powered Liver Disease Prediction System

A cutting-edge web application that uses machine learning and explainable AI to predict liver disease with high accuracy. Built on peer-reviewed research with SHAP and LIME interpretability features.

## 🎯 Features

### Core Features
- **10+ ML Models**: Logistic Regression, Decision Tree, Random Forest, AdaBoost, XGBoost, LightGBM, SVM, KNN, Bagging, and Stacking
- **Explainable AI**: SHAP and LIME implementations for transparent model decisions
- **Patient Management**: Register and manage patient records with medical history
- **Real-time Predictions**: Generate predictions with probability scores and risk levels
- **Analytics Dashboard**: Comprehensive statistics and visualization charts
- **Admin Panel**: Manage users, patients, predictions, and models

### Technical Features
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Secure Authentication**: Password hashing, session management, CSRF protection
- **REST API**: Complete API endpoints for programmatic access
- **Database**: SQLite for development, PostgreSQL (Neon) for production
- **Deployment Ready**: Configured for Render with Gunicorn

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip or conda
- Git
- (Optional) PostgreSQL/Neon account for production deployment

### Installation

1. **Clone the repository** (or extract the project):
```bash
cd HepatoX
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create .env file** (copy from .env.example):
```bash
cp .env.example .env
```

5. **Initialize the database**:
```bash
python -c "from app import app; app.cli.invoke(['init_db'])"
```

Or manually:
```bash
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>>     print("Database initialized")
```

6. **Generate and train models**:
```bash
python train_models.py
```

7. **Run the application**:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Default Admin Credentials
- **Username**: admin
- **Password**: Admin@123
- **Email**: admin@hepatox.com

⚠️ **Change these credentials immediately in production!**

## 📊 Dataset

The system includes a synthetic dataset generator with 1700 patient records containing:
- Age, Gender, BMI
- Alcohol Consumption, Smoking
- Genetic Risk, Physical Activity
- Diabetes, Hypertension
- Liver Function Test Results
- Diagnosis Labels

Generate the dataset:
```bash
python -c "from utils.dataset_utils import generate_synthetic_dataset, save_dataset; df = generate_synthetic_dataset(); save_dataset(df)"
```

## 🤖 Machine Learning Models

All models are trained with:
- **Cross-validation**: 5-fold CV for robust evaluation
- **Hyperparameter tuning**: Optimized for best performance
- **Metrics**: Accuracy, Precision, Recall, F1-Score, ROC-AUC
- **Automatic selection**: Best model is automatically selected

Models are saved to `trained_models/` folder.

## 🔍 Explainability

### SHAP (SHapley Additive exPlanations)
- Global feature importance
- Individual prediction explanations
- Force plots, decision plots, summary plots

### LIME (Local Interpretable Model-agnostic Explanations)
- Local feature importance
- Top contributing features
- Positive and negative contributions

## 📁 Project Structure

```
HepatoX/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── database.py                 # Database models
├── train_models.py            # Model training script
├── requirements.txt           # Python dependencies
├── Procfile                   # Render deployment config
├── runtime.txt                # Python version
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── routes/
│   └── api_routes.py          # REST API endpoints
├── models/                    # ML model definitions
├── static/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   ├── js/
│   │   └── main.js           # JavaScript utilities
│   └── images/               # Images and illustrations
├── templates/
│   ├── base.html             # Base template
│   ├── index.html            # Home page
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # Main dashboard
│   ├── patients.html         # Patients list
│   ├── register_patient.html # Patient registration
│   ├── predict.html          # Prediction page
│   ├── forgot_password.html  # Password reset
│   ├── errors/               # Error pages
│   └── admin/                # Admin templates
├── utils/
│   ├── ml_utils.py          # ML utilities
│   ├── xai_utils.py         # XAI implementations
│   └── dataset_utils.py     # Dataset generation
├── trained_models/          # Saved ML models
├── dataset/                 # Dataset files
├── uploads/                 # User uploads
├── reports/                 # Generated reports
├── instance/                # Instance folder (DB, temp files)
└── xai/                     # XAI visualizations
```

## 🌐 REST API

### Authentication
- `POST /api/v1/login` - User login
- `POST /api/v1/register` - User registration

### Patients
- `GET /api/v1/patients` - List patients
- `POST /api/v1/patients` - Create patient
- `GET /api/v1/patients/<id>` - Get patient details
- `PUT /api/v1/patients/<id>` - Update patient

### Predictions
- `POST /api/v1/predict` - Make prediction
- `GET /api/v1/predictions/<id>` - Get prediction details

### Dashboard
- `GET /api/v1/dashboard/stats` - Get statistics
- `GET /api/v1/dashboard/recent-predictions` - Recent predictions

### Models
- `GET /api/v1/models` - List all models
- `GET /api/v1/models/best` - Get best model

### Analytics
- `GET /api/v1/analytics/age-distribution` - Age distribution
- `GET /api/v1/analytics/gender-distribution` - Gender distribution
- `GET /api/v1/analytics/model-comparison` - Model metrics

## 🚀 Deployment to Render

### Prerequisites
- Render account
- Neon account (PostgreSQL)

### Step-by-Step Deployment

1. **Create Neon Database**:
   - Go to https://console.neon.tech
   - Create a new project
   - Copy the database connection URL

2. **Create Render Service**:
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure as follows:

   **Build Command**:
   ```
   pip install -r requirements.txt && python train_models.py
   ```

   **Start Command**:
   ```
   gunicorn app:app
   ```

3. **Set Environment Variables** in Render:
   ```
   DATABASE_URL=postgresql://user:password@host/database
   SECRET_KEY=your-random-secret-key
   FLASK_ENV=production
   DEFAULT_ADMIN_PASSWORD=your-secure-password
   ```

4. **Deploy**:
   - Render will automatically deploy when you push to main branch
   - Monitor logs in Render dashboard

### Important Notes
- First deployment takes 10-15 minutes (model training)
- Subsequent deployments are faster (models are cached)
- Database is created automatically on first deployment
- Keep `.env` file secure - never commit to Git

## 📊 Database Schema

### Users
- id, username, email, password_hash, role, full_name, reset_token, is_active_flag, created_at

### Patients
- id, name, age, gender, bmi, alcohol_consumption, smoking, genetic_risk, physical_activity, diabetes, hypertension, liver_function_test, created_by, created_at

### Predictions
- id, patient_id, model_used, prediction, probability, confidence_score, risk_level, shap_summary, lime_summary, created_at

### TrainedModels
- id, model_name, model_type, file_path, accuracy, precision, recall, f1_score, roc_auc, is_best, created_at, updated_at

### Reports
- id, patient_id, prediction_id, report_type, file_path, created_at

### Logs
- id, user_id, action, description, status, created_at

## 🔐 Security

- **Password Hashing**: Bcrypt for secure password storage
- **Session Management**: Secure cookies with HTTPONLY flag
- **CSRF Protection**: Flask-WTF CSRF tokens
- **SQL Injection Prevention**: SQLAlchemy ORM
- **Input Validation**: Server-side validation on all inputs
- **CORS**: Configured for API security

## 🛠️ Development

### Running Tests
```bash
# Unit tests (to be added)
pytest tests/
```

### Code Style
```bash
# Format code
black .

# Lint code
pylint routes/ utils/
```

### Database Migrations
```bash
flask db init          # Initialize migrations
flask db migrate       # Create migration
flask db upgrade       # Apply migration
```

## 📈 Performance Optimization

- Model predictions cached in memory
- Database queries optimized with indexes
- Frontend assets minified
- Lazy loading for charts and visualizations
- Pagination for large datasets

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 👨‍💼 Support

For issues, questions, or suggestions:
- Create an Issue on GitHub
- Contact: support@hepatox.com

## 🔗 References

Based on the research paper:
"Machine Learning and Explainable AI for Liver Disease Prediction: An Integrated Interpretability Framework"

## 📚 Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **ML**: Scikit-learn, XGBoost, LightGBM
- **XAI**: SHAP, LIME
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JS
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Deployment**: Render, Gunicorn, Neon
- **Data Processing**: Pandas, NumPy, Matplotlib

---

**HepatoX** - Advancing Healthcare with Explainable AI 🏥🤖

