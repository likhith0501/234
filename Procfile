web: gunicorn app:app --workers 2 --timeout 120
release: python -c "from app import app, setup_db; app.app_context().push(); setup_db()"
