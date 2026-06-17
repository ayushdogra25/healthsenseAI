import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class DiseasePredictor:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.model_path = self.base_dir / "model.joblib"
        self.le_path = self.base_dir / "label_encoder.joblib"
        self.symptoms_path = self.base_dir / "symptom_columns.json"

        self.model = None
        self.label_encoder = None
        self.symptom_columns = None
        self.symptom_to_idx = {}

    def load_symptom_columns_only(self):
        """
        Load only the symptom vocabulary without touching the heavy model artifacts.
        This is used by the symptom dropdown endpoint to avoid slow or failing
        model loads on production deployments.
        """
        if self.symptom_columns is not None:
            return self.symptom_columns

        symptoms_path = Path(self.symptoms_path).resolve()
        if not symptoms_path.is_file():
            raise FileNotFoundError(f"Symptoms file not found: {symptoms_path}")

        with symptoms_path.open('r', encoding='utf-8') as f:
            self.symptom_columns = json.load(f)

        self.symptom_to_idx = {
            symptom.lower().strip(): idx
            for idx, symptom in enumerate(self.symptom_columns)
        }
        return self.symptom_columns

    def load_assets(self):
        if (self.model_path.is_file() and
            self.le_path.is_file() and
            self.symptoms_path.is_file()):

            self.model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.le_path)
            with self.symptoms_path.open('r', encoding='utf-8') as f:
                self.symptom_columns = json.load(f)

            # Map symptom names to column index for quick lookup
            self.symptom_to_idx = {
                symptom.lower().strip(): idx
                for idx, symptom in enumerate(self.symptom_columns)
            }
            return True
        return False

    def predict_diseases(self, user_symptoms):
        """
        Accepts a list of symptom names, constructs a binary vector,
        and returns the top 3 predicted diseases using only the saved artifacts.
        """
        if self.model is None or self.label_encoder is None or self.symptom_columns is None:
            # Try reloading in case they were generated after initialization
            if not self.load_assets():
                raise RuntimeError(
                    "ML model assets not found. Make sure backend/ml/model.joblib, "
                    "backend/ml/label_encoder.joblib, and backend/ml/symptom_columns.json exist."
                )
        
        # Build binary vector
        binary_vector = np.zeros(len(self.symptom_columns))
        matched_symptoms = []
        
        for symptom in user_symptoms:
            cleaned_symptom = symptom.lower().replace('_', ' ').replace('-', ' ').strip()
            
            # Direct match
            if cleaned_symptom in self.symptom_to_idx:
                idx = self.symptom_to_idx[cleaned_symptom]
                binary_vector[idx] = 1.0
                matched_symptoms.append(self.symptom_columns[idx])
            else:
                # Try fuzzy matching - check if the user symptom is a substring of any vocabulary symptom, or vice versa
                found = False
                for vocab_symptom in self.symptom_columns:
                    vocab_clean = vocab_symptom.lower().strip()
                    if cleaned_symptom in vocab_clean or vocab_clean in cleaned_symptom:
                        idx = self.symptom_to_idx[vocab_clean]
                        binary_vector[idx] = 1.0
                        matched_symptoms.append(vocab_symptom)
                        found = True
                        break
        
        # Build a DataFrame with the saved symptom schema so inference uses only artifacts.
        input_data = pd.DataFrame([binary_vector], columns=self.symptom_columns)
        
        # Get probability estimates
        probabilities = self.model.predict_proba(input_data)[0]
        
        # Get indices of top 3 classes sorted by probability
        top_indices = np.argsort(probabilities)[::-1][:3]
        
        # Decode and format results
        results = []
        for idx in top_indices:
            disease_name = self.label_encoder.classes_[idx]
            confidence_percentage = round(float(probabilities[idx]) * 100, 2)
            results.append({
                "disease": disease_name,
                "confidence": confidence_percentage
            })
            
        return {
            "predictions": results,
            "matched_symptoms": list(set(matched_symptoms)) # Remove duplicates if any
        }


