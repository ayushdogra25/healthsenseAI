import os
import json
import joblib
import numpy as np
import pandas as pd

class DiseasePredictor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.base_dir, "model.joblib")
        self.le_path = os.path.join(self.base_dir, "label_encoder.joblib")
        self.symptoms_path = os.path.join(self.base_dir, "symptom_columns.json")
        
        self.model = None
        self.label_encoder = None
        self.symptom_columns = None
        self.symptom_to_idx = {}
        
        # Load assets if they exist
        self.load_assets()

    def load_assets(self):
        if (os.path.exists(self.model_path) and 
            os.path.exists(self.le_path) and 
            os.path.exists(self.symptoms_path)):
            
            self.model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.le_path)
            with open(self.symptoms_path, 'r', encoding='utf-8') as f:
                self.symptom_columns = json.load(f)
            
            # Map symptom names to column index for quick lookup
            self.symptom_to_idx = {symptom.lower().strip(): idx for idx, symptom in enumerate(self.symptom_columns)}
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

# Global predictor instance
predictor = DiseasePredictor()
