# HepatoX - Quick Start Guide

## Project Overview

HepatoX is an **AI-Powered Liver Disease Prediction System** that uses machine learning and explainable AI to predict liver disease risk with 10 trained models (Logistic Regression, Decision Tree, Random Forest, XGBoost, LightGBM, SVM, AdaBoost, KNN, Bagging, and Stacking).

**Key Features:**
- 🔐 User authentication with role-based access control
- 👥 Patient management system
- 🧠 10 ML models for disease prediction
- 📊 Interactive dashboard with analytics
- 🔍 Explainable AI using SHAP and LIME
- 👨‍💼 Admin panel for user and model management
- 🌐 REST API for programmatic access
- 📱 Responsive Bootstrap 5 frontend

## Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)
- Modern web browser

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/hepatox.git
cd hepatox
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and set:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/hepatox.db
DEBUG=True
```

### 5. Initialize Database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
```

### 6. Train Models (Optional)
```bash
python train_models.py
```
This trains all 10 models and saves them to `trained_models/` (takes 5-10 minutes).

### 7. Run Application
```bash
python app.py
```

Visit: http://localhost:5000

### Default Credentials
- **Username:** `admin`
- **Password:** `admin123` (change immediately!)

## Project Structure

```
hepatox/
├── app.py                    # Main Flask application
├── config.py                # Configuration management
├── database.py              # SQLAlchemy ORM models
├── train_models.py          # ML model training pipeline
├── test_setup.py            # Setup verification script
│
├── routes/
│   └── api_routes.py        # 20+ REST API endpoints
│
├── utils/
│   ├── ml_utils.py          # ML pipeline (preprocessing, training, prediction)
│   ├── xai_utils.py         # SHAP and LIME explainability
│   └── dataset_utils.py     # Synthetic dataset generation
│
├── templates/
│   ├── base.html            # Navigation and layout
│   ├── index.html           # Home page with features
│   ├── login.html           # Login form
│   ├── register.html        # User registration
│   ├── dashboard.html       # Main dashboard
│   ├── patients.html        # Patient list
│   ├── register_patient.html# Add new patient
│   ├── patient_detail.html  # Patient info and predictions
│   ├── predict.html         # Make predictions
│   ├── forgot_password.html # Password reset
│   ├── admin/
│   │   ├── dashboard.html   # Admin statistics
│   │   ├── users.html       # User management
│   │   └── models.html      # Model comparison
│   └── errors/
│       ├── 404.html         # Not found
│       ├── 403.html         # Access denied
│       └── 500.html         # Server error
│
├── static/
│   ├── css/style.css        # Main stylesheet
│   ├── js/main.js           # JavaScript utilities
│   ├── images/              # Image assets
│   └── xai_plots/           # SHAP/LIME visualizations
│
├── trained_models/          # Saved ML models (generated)
├── instance/                # SQLite database (generated)
├── uploads/                 # Patient data uploads (generated)
├── reports/                 # Generated reports (generated)
│
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── Procfile                # Render deployment config
├── README.md               # Full documentation
└── DEPLOYMENT_GUIDE.md     # Step-by-step deployment
```

## Core Features

### 1. User Management
- Register new users
- Login/logout with session management
- Admin role-based access control
- Password reset functionality

### 2. Patient Management
- Register new patients with comprehensive medical history
- View patient details and medical conditions
- Search and filter patients
- Track prediction history

### 3. Predictions
- Select patient and make predictions
- Display prediction results with confidence scores
- Risk level classification (Low/Moderate/High)
- SHAP and LIME explanations for transparency

### 4. Dashboard
- Key statistics (patients, predictions, disease distribution)
- Best model performance metrics
- Prediction distribution chart
- Recent predictions table

### 5. Admin Panel
- User management (view, edit, delete)
- Model performance comparison
- System statistics and monitoring

### 6. REST API
Access all features programmatically:
```bash
# Example: Make a prediction via API
curl -X POST http://localhost:5000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "explain": true
  }'
```

See README.md for all API endpoints.

## Common Tasks

### Add Demo Data
```bash
python -c "
from app import app, db
from database import Patient
from datetime import datetime

with app.app_context():
    patient = Patient(
        name='John Doe',
        age=45,
        gender='Male',
        bmi=28.5,
        alcohol_consumption=True,
        smoking=False,
        genetic_risk=False,
        physical_activity=1,
        diabetes=False,
        hypertension=True,
        liver_function_test=45,
        created_by=1
    )
    db.session.add(patient)
    db.session.commit()
    print(f'Patient {patient.id} created')
"
```

### Change Admin Password
1. Login as admin
2. Go to profile settings
3. Update password

### View Logs
```bash
tail -f logs/app.log  # Real-time log viewing
```

### Reset Database
```bash
rm instance/hepatox.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Deployment

### Deploy to Render (Production)

See `DEPLOYMENT_GUIDE.md` for detailed instructions:

1. **Setup Neon PostgreSQL database**
   - Create account at https://console.neon.tech
   - Get connection string

2. **Deploy to Render**
   - Create account at https://render.com
   - Connect GitHub repository
   - Set environment variables
   - Deploy (takes 10-15 minutes first time)

3. **Access Production**
   - URL: `https://hepatox-xxxx.onrender.com`
   - Change default admin password immediately

## Testing

### Run Application Tests
```bash
python test_setup.py
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:5000/api/v1/health

# Get dashboard stats
curl http://localhost:5000/api/v1/dashboard/stats

# List all models
curl http://localhost:5000/api/v1/models
```

## Troubleshooting

### Port Already in Use
```bash
# Use different port
python -c "from app import app; app.run(port=5001)"
```

### Database Errors
```bash
# Reset database
rm instance/hepatox.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Model Training Issues
```bash
# Clear old models
rm trained_models/*
# Retrain
python train_models.py
```

## Performance Tips

- **First Load:** Model training on startup takes 10-15 minutes
- **Predictions:** Average prediction time: 100-500ms
- **SHAP Explanations:** ~1-2 seconds per explanation
- **Large Datasets:** Use pagination for lists with 1000+ records

## Security Checklist

- [ ] Changed default admin password
- [ ] Set strong `SECRET_KEY`
- [ ] Updated `DATABASE_URL` for production
- [ ] Enabled HTTPS (automatic on Render)
- [ ] Configured firewall rules
- [ ] Regular database backups enabled
- [ ] Monitor logs for suspicious activity

## Technologies Used

**Backend:**
- Flask 3.0.0 - Web framework
- SQLAlchemy - ORM
- Flask-SQLAlchemy 3.1.1
- Flask-Login - Authentication
- Flask-Bcrypt - Password hashing
- Gunicorn - WSGI server

**Machine Learning:**
- scikit-learn - ML algorithms
- XGBoost, LightGBM - Gradient boosting
- SHAP 0.52.0 - Model explanability
- LIME - Local explanations
- Pandas, NumPy - Data processing

**Frontend:**
- Bootstrap 5 - CSS framework
- Chart.js - Data visualization
- JavaScript - Interactivity
- Font Awesome - Icons

**Database:**
- SQLite - Development
- PostgreSQL (Neon) - Production

**Deployment:**
- Render - Application hosting
- Neon - PostgreSQL database hosting

## Getting Help

- **Documentation:** See README.md for comprehensive guide
- **API Docs:** See REST API section in README.md
- **Deployment:** See DEPLOYMENT_GUIDE.md
- **Issues:** Create GitHub issue
- **Questions:** Check FAQ in README.md

## Next Steps

1. ✅ Run locally: `python app.py`
2. ✅ Test features: Login and explore
3. ✅ Train models: `python train_models.py`
4. ✅ Deploy: Follow DEPLOYMENT_GUIDE.md
5. ✅ Monitor: Check logs in Render dashboard

---

**Ready to predict liver disease with AI? Let's go!** 🚀

For detailed documentation, see [README.md](README.md)
