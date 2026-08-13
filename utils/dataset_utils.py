"""
Generate synthetic liver disease dataset for model training.
Creates 1700 records with realistic liver disease risk factors.
"""
import numpy as np
import pandas as pd
import os
from datetime import datetime

from config import Config


def generate_synthetic_dataset(n_samples=1700, random_state=42):
    """
    Generate synthetic liver disease dataset.
    
    Args:
        n_samples: Number of records to generate
        random_state: Random seed for reproducibility
        
    Returns:
        pd.DataFrame: Synthetic dataset
    """
    np.random.seed(random_state)
    
    print(f"Generating synthetic dataset with {n_samples} records...")
    
    # Generate features
    data = {
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'bmi': np.random.normal(25, 5, n_samples).clip(15, 45),
        'alcohol_consumption': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'smoking': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'genetic_risk': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'physical_activity': np.random.choice([0, 1, 2], n_samples, p=[0.3, 0.4, 0.3]),
        'diabetes': np.random.choice([0, 1], n_samples, p=[0.75, 0.25]),
        'hypertension': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'liver_function_test': np.random.normal(40, 15, n_samples).clip(10, 150),
    }
    
    df = pd.DataFrame(data)
    
    # Generate diagnosis based on risk factors (with some correlation)
    diagnosis = np.zeros(n_samples)
    
    for i in range(n_samples):
        risk_score = 0
        
        # Age factor
        if df.loc[i, 'age'] > 50:
            risk_score += 0.1
        elif df.loc[i, 'age'] > 65:
            risk_score += 0.2
        
        # BMI factor
        if df.loc[i, 'bmi'] > 30:
            risk_score += 0.15
        elif df.loc[i, 'bmi'] > 25:
            risk_score += 0.05
        
        # Alcohol consumption
        if df.loc[i, 'alcohol_consumption'] == 1:
            risk_score += 0.25
        
        # Smoking
        if df.loc[i, 'smoking'] == 1:
            risk_score += 0.1
        
        # Genetic risk
        if df.loc[i, 'genetic_risk'] == 1:
            risk_score += 0.2
        
        # Physical activity (protective)
        if df.loc[i, 'physical_activity'] == 2:
            risk_score -= 0.1
        elif df.loc[i, 'physical_activity'] == 0:
            risk_score += 0.1
        
        # Diabetes
        if df.loc[i, 'diabetes'] == 1:
            risk_score += 0.15
        
        # Hypertension
        if df.loc[i, 'hypertension'] == 1:
            risk_score += 0.1
        
        # Liver function test
        if df.loc[i, 'liver_function_test'] > 60:
            risk_score += 0.15
        elif df.loc[i, 'liver_function_test'] > 50:
            risk_score += 0.1
        
        # Convert risk score to probability
        probability = 1 / (1 + np.exp(-4 * (risk_score - 0.5)))
        
        # Add some randomness
        diagnosis[i] = 1 if np.random.random() < probability else 0
    
    df['diagnosis'] = diagnosis.astype(int)
    
    print(f"[OK] Dataset generated:")
    print(f"  - Total records: {len(df)}")
    print(f"  - Healthy cases: {(df['diagnosis'] == 0).sum()} ({(df['diagnosis'] == 0).sum()/len(df)*100:.1f}%)")
    print(f"  - Disease cases: {(df['diagnosis'] == 1).sum()} ({(df['diagnosis'] == 1).sum()/len(df)*100:.1f}%)")
    print(f"  - Features: {list(df.columns)}")
    
    return df


def save_dataset(df, format='csv'):
    """
    Save dataset to file.
    
    Args:
        df: DataFrame to save
        format: 'csv' or 'excel'
    """
    os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'csv':
        filepath = os.path.join(Config.DATASET_FOLDER, f"liver_disease_data_{timestamp}.csv")
        df.to_csv(filepath, index=False)
        print(f"[OK] Dataset saved to CSV: {filepath}")
        return filepath
    
    elif format == 'excel':
        filepath = os.path.join(Config.DATASET_FOLDER, f"liver_disease_data_{timestamp}.xlsx")
        df.to_excel(filepath, index=False)
        print(f"✓ Dataset saved to Excel: {filepath}")
        return filepath


def load_dataset(filepath):
    """Load dataset from file."""
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    elif filepath.endswith(('.xlsx', '.xls')):
        return pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file format")


if __name__ == "__main__":
    # Generate and save dataset
    dataset = generate_synthetic_dataset(n_samples=1700)
    
    # Save in multiple formats
    csv_path = save_dataset(dataset, format='csv')
    excel_path = save_dataset(dataset, format='excel')
    
    print("\n✓ Dataset generation completed successfully!")
