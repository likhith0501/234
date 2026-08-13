#!/usr/bin/env python
"""Check if trained models are in the database."""

from app import app, db
from database import TrainedModel

with app.app_context():
    models = TrainedModel.query.all()
    if models:
        print(f'✓ Found {len(models)} trained models:')
        for m in models:
            print(f'  - {m.model_name}: ROC-AUC={m.roc_auc}, is_best={m.is_best}')
    else:
        print('✗ No trained models in database!')
        print('Running train_models.py should create them...')
