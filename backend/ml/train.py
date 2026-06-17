import os
import json
import gc
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def main():
    print("Starting ML Model Training Pipeline (Memory Optimized & Constrained)...")
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, "..", "..", "Final_Augmented_dataset_Diseases_and_Symptoms.csv")
    
    if not os.path.exists(dataset_path):
        dataset_path = "Final_Augmented_dataset_Diseases_and_Symptoms.csv"
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")
            
    print(f"Loading dataset from: {dataset_path}")
    
    # Read first line to get all columns
    temp_df = pd.read_csv(dataset_path, nrows=1)
    symptom_columns = [col for col in temp_df.columns if col != 'diseases']
    del temp_df
    
    # Read full CSV, forcing symptom columns to uint8 to save 8x memory
    dtype_dict = {col: 'uint8' for col in symptom_columns}
    dtype_dict['diseases'] = 'str'
    
    df = pd.read_csv(dataset_path, dtype=dtype_dict)
    print(f"Dataset loaded. Shape: {df.shape}")
    
    # Separate features and target
    X = df[symptom_columns]
    y = df["diseases"]
    
    print(f"Number of symptoms (features): {len(symptom_columns)}")
    
    # Encode target variable
    print("Encoding disease labels...")
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Save symptom columns and label encoder
    symptom_columns_path = os.path.join(base_dir, "symptom_columns.json")
    label_encoder_path = os.path.join(base_dir, "label_encoder.joblib")
    
    print(f"Saving symptom columns to {symptom_columns_path}...")
    with open(symptom_columns_path, 'w', encoding='utf-8') as f:
        json.dump(symptom_columns, f, indent=4)
        
    print(f"Saving label encoder to {label_encoder_path}...")
    joblib.dump(label_encoder, label_encoder_path)
    
    # Split dataset
    print("Splitting dataset into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    # Clear large unneeded references and collect garbage
    del df
    gc.collect()
    
    # Train RandomForestClassifier with constraints to prevent memory exhaustion
    # n_estimators=300, max_depth=15, min_samples_leaf=2 prevents tree sizes from blowing up
    print("Training RandomForestClassifier (n_estimators=300, max_depth=15, min_samples_leaf=2, n_jobs=1, random_state=42)...")
    model = RandomForestClassifier(
        n_estimators=300, 
        max_depth=15, 
        min_samples_leaf=2,
        random_state=42, 
        n_jobs=1
    )
    model.fit(X_train, y_train)
    print("Model training completed successfully.")
    
    # Evaluate model
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision_weighted = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall_weighted = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision (Weighted): {precision_weighted:.4f}")
    print(f"Recall (Weighted):    {recall_weighted:.4f}")
    print(f"F1 Score (Weighted):  {f1_weighted:.4f}")
    print("--------------------------\n")
    
    # Save the trained model
    model_path = os.path.join(base_dir, "model.joblib")
    print(f"Saving trained model to {model_path}...")
    # Using compression to optimize disk storage
    joblib.dump(model, model_path, compress=3)
    print("ML Pipeline execution finished successfully!")

if __name__ == "__main__":
    main()
