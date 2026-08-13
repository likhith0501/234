"""
Train machine learning models for liver disease prediction.
Run this script to generate and train models on the dataset.
"""
import os
import sys
import pandas as pd
import joblib
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.dataset_utils import generate_synthetic_dataset, save_dataset, load_dataset
from utils.ml_utils import DataPreprocessor, ModelTrainer


def train_all_models():
    """Train all models and save results."""
    
    print("=" * 70)
    print("LIVER DISEASE PREDICTION - MODEL TRAINING PIPELINE")
    print("=" * 70)
    
    # ========================================================================
    # 1. DATASET GENERATION
    # ========================================================================
    print("\n[1/5] Generating synthetic dataset...")
    dataset = generate_synthetic_dataset(n_samples=1700, random_state=Config.RANDOM_STATE)
    
    # Save dataset
    dataset_path = save_dataset(dataset, format='csv')
    
    # ========================================================================
    # 2. DATA PREPROCESSING
    # ========================================================================
    print("\n[2/5] Preprocessing data...")
    
    preprocessor = DataPreprocessor(
        feature_columns=Config.FEATURE_COLUMNS,
        target_column=Config.TARGET_COLUMN
    )
    
    X, y = preprocessor.preprocess(dataset)
    
    print(f"[OK] Data preprocessed:")
    print(f"  - Features shape: {X.shape}")
    print(f"  - Target shape: {y.shape}")
    print(f"  - Features: {list(X.columns)}")
    
    # Save preprocessor
    preprocessor_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "preprocessor.pkl")
    os.makedirs(Config.TRAINED_MODELS_FOLDER, exist_ok=True)
    preprocessor.save_preprocessor(preprocessor_path)
    print(f"[OK] Preprocessor saved to {preprocessor_path}")
    
    # ========================================================================
    # 3. MODEL TRAINING
    # ========================================================================
    print("\n[3/5] Building and training models...")
    
    trainer = ModelTrainer(
        random_state=Config.RANDOM_STATE,
        test_size=Config.TEST_SIZE
    )
    
    # Split data
    X_train, X_test, y_train, y_test = trainer.prepare_data(X, y)
    
    print(f"[OK] Data split:")
    print(f"  - Training set: {X_train.shape[0]} samples")
    print(f"  - Testing set: {X_test.shape[0]} samples")
    print(f"  - Class distribution in train: {y_train.value_counts().to_dict()}")
    
    # Build and train models
    trainer.build_models()
    trainer.train_models(X_train, X_test, y_train, y_test)
    
    # ========================================================================
    # 4. MODEL COMPARISON & SAVING
    # ========================================================================
    print("\n[4/5] Saving trained models...")
    
    comparison_df = trainer.get_model_comparison()
    print("\n" + comparison_df.to_string())
    
    # Save comparison results
    comparison_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "model_comparison.csv")
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\n[OK] Model comparison saved to {comparison_path}")
    
    # Save all models
    for model_name, model in trainer.models.items():
        model_path = os.path.join(
            Config.TRAINED_MODELS_FOLDER,
            f"{model_name.lower().replace(' ', '_')}.pkl"
        )
        trainer.save_model(model_name, model_path)
    
    # Save best model separately
    best_model_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "best_model.pkl")
    joblib.dump(trainer.best_model, best_model_path)
    print(f"\n[OK] Best model ({trainer.best_model_name}) saved to {best_model_path}")
    
    # ========================================================================
    # 5. DATABASE STORAGE (if Flask app context available)
    # ========================================================================
    print("\n[5/5] Storing model information in database...")
    
    try:
        from app import app, db
        from database import TrainedModel
        
        with app.app_context():
            # Clear previous models
            TrainedModel.query.delete()
            
            # Add new models
            for model_name, metrics in trainer.results.items():
                model_file = f"{model_name.lower().replace(' ', '_')}.pkl"
                model_path = os.path.join(Config.TRAINED_MODELS_FOLDER, model_file)
                
                trained_model = TrainedModel(
                    model_name=model_name,
                    model_type=type(trainer.models[model_name]).__name__,
                    file_path=model_path,
                    accuracy=metrics['accuracy'],
                    precision=metrics['precision'],
                    recall=metrics['recall'],
                    f1_score=metrics['f1_score'],
                    roc_auc=metrics['roc_auc'],
                    is_best=(model_name == trainer.best_model_name)
                )
                
                db.session.add(trained_model)
            
            db.session.commit()
            print("[OK] Model information stored in database")
    
    except Exception as e:
        print(f"[!] Could not store in database (Flask app not initialized): {e}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("[OK] TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nGenerated Files:")
    print(f"  - Dataset: {dataset_path}")
    print(f"  - Preprocessor: {preprocessor_path}")
    print(f"  - Model Comparison: {comparison_path}")
    print(f"  - Individual Models: {Config.TRAINED_MODELS_FOLDER}")
    print(f"  - Best Model: {best_model_path}")
    print(f"\nBest Model: {trainer.best_model_name}")
    print(f"Accuracy: {trainer.results[trainer.best_model_name]['accuracy']:.4f}")
    print(f"ROC-AUC: {trainer.results[trainer.best_model_name]['roc_auc']:.4f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    train_all_models()
