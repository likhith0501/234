from app import app, db
from database import User
from flask_login import login_user
import json
from routes.api_routes import predict

with app.test_request_context(
    '/api/v1/predict', 
    method='POST', 
    json={'patient_id': 1, 'explain': True}
):
    user = User.query.first()
    login_user(user)
    try:
        response = predict()
        print("Response:", response)
        if hasattr(response, 'get_json'):
            print("JSON:", response.get_json())
    except Exception as e:
        import traceback
        traceback.print_exc()
