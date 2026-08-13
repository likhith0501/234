"""
Sync trained model files and their metrics into the database.
Run this script when the .pkl files exist on disk but the database
has no TrainedModel records (e.g. after a fresh DB or git clone).
"""
import os
import sys
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from database import TrainedModel
from config import Config

# Map CSV model names -> pkl file name stems
MODEL_FILE_MAP = {
    "Logistic Regression": "logistic_regression",
    "AdaBoost":            "adaboost",
    "Random Forest":       "random_forest",
    "SVM":                 "svm",
    "XGBoost":             "xgboost",
    "LightGBM":            "lightgbm",
    "KNN":                 "knn",
    "Bagging":             "bagging",
    "Decision Tree":       "decision_tree",
}

# Map CSV model names -> sklearn class names (for model_type column)
MODEL_CLASS_MAP = {
    "Logistic Regression": "LogisticRegression",
    "AdaBoost":            "AdaBoostClassifier",
    "Random Forest":       "RandomForestClassifier",
    "SVM":                 "SVC",
    "XGBoost":             "XGBClassifier",
    "LightGBM":            "LGBMClassifier",
    "KNN":                 "KNeighborsClassifier",
    "Bagging":             "BaggingClassifier",
    "Decision Tree":       "DecisionTreeClassifier",
}


def sync():
    comparison_path = os.path.join(Config.TRAINED_MODELS_FOLDER, "model_comparison.csv")

    if not os.path.exists(comparison_path):
        print(f"[ERROR] model_comparison.csv not found at {comparison_path}")
        print("  Please run train_models.py first to generate the models.")
        sys.exit(1)

    df = pd.read_csv(comparison_path)
    print(f"[OK] Loaded metrics for {len(df)} models from {comparison_path}")

    # Determine best model by ROC-AUC
    best_row = df.loc[df["ROC-AUC"].idxmax()]
    best_model_name = best_row["Model"]
    print(f"[OK] Best model: {best_model_name} (ROC-AUC={best_row['ROC-AUC']:.4f})")

    with app.app_context():
        existing_count = TrainedModel.query.count()
        if existing_count > 0:
            print(f"[!] {existing_count} model(s) already in database. Clearing and re-syncing...")
            TrainedModel.query.delete()
            db.session.commit()

        added = 0
        skipped = 0
        for _, row in df.iterrows():
            model_name = row["Model"]
            file_stem = MODEL_FILE_MAP.get(model_name)

            if file_stem is None:
                print(f"  [SKIP] Unknown model name '{model_name}' - not in MODEL_FILE_MAP")
                skipped += 1
                continue

            model_file = f"{file_stem}.pkl"
            model_path = os.path.join(Config.TRAINED_MODELS_FOLDER, model_file)

            if not os.path.exists(model_path):
                print(f"  [SKIP] {model_file} not found on disk at {model_path}")
                skipped += 1
                continue

            trained_model = TrainedModel(
                model_name=model_name,
                model_type=MODEL_CLASS_MAP.get(model_name, "Unknown"),
                file_path=model_path,
                accuracy=float(row["Accuracy"]),
                precision=float(row["Precision"]),
                recall=float(row["Recall"]),
                f1_score=float(row["F1-Score"]),
                roc_auc=float(row["ROC-AUC"]),
                is_best=(model_name == best_model_name),
            )
            db.session.add(trained_model)
            added += 1
            best_marker = " <-- BEST" if model_name == best_model_name else ""
            print(f"  [+] {model_name}: ROC-AUC={row['ROC-AUC']:.4f}{best_marker}")

        db.session.commit()
        print(f"\n[OK] Synced {added} model(s) to database ({skipped} skipped).")
        print("[OK] Refresh the dashboard — the warning should be gone.")


if __name__ == "__main__":
    sync()
