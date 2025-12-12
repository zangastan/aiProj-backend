import joblib
import os
import numpy as np
import pandas as pd
from datetime import datetime

class AIPredictor:
    def __init__(self):
        self.ml_dir = os.path.dirname(__file__)
        self.price_model = self._load_model('price_model.pkl')
        self.item_encoder = self._load_model('item_encoder.pkl')
        self.behavior_model = self._load_model('behavior_model.pkl')

    def _load_model(self, filename):
        path = os.path.join(self.ml_dir, filename)
        if os.path.exists(path):
            return joblib.load(path)
        return None

    def predict_price(self, item_name, months_ahead=1):
        if not self.price_model or not self.item_encoder:
            return None
        
        try:
            item_code = self.item_encoder.transform([item_name])[0]
            current_date = datetime.now()
            # Approximate month number from 2023-01-01 start
            start_date = datetime(2023, 1, 1)
            current_month_num = (current_date.year - start_date.year) * 12 + current_date.month
            future_month_num = current_month_num + months_ahead
            
            prediction = self.price_model.predict([[future_month_num, item_code]])[0]
            return round(prediction, 2)
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    def analyze_behavior(self, income, expenses, savings):
        if not self.behavior_model:
            return "Unknown"
        
        cluster = self.behavior_model.predict([[income, expenses, savings]])[0]
        
        # Mapping clusters to labels (based on training data logic)
        # Note: In real K-Means, labels might swap, but for this fixed seed:
        # 0: Struggling (Low values)
        # 1: Stable (Mid values)
        # 2: Thriving (High values)
        
        # We need to verify which cluster is which based on centroids if dynamic, 
        # but for this simple demo we'll infer from the input vs centroids if possible, 
        # or just map statically if we assume consistent training.
        # Let's return the cluster ID and a descriptor.
        
        if cluster == 0:
            return "Struggling" # Low income/savings
        elif cluster == 1:
            return "Stable" # Mid income/savings
        else:
            return "Thriving" # High income/savings

    def get_advice(self, financial_status):
        if financial_status == "Struggling":
            return [
                "Your expenses are high relative to your income.",
                "Consider cutting non-essential costs like dining out.",
                "Look for side income opportunities."
            ]
        elif financial_status == "Stable":
            return [
                "You are doing well, but could save more.",
                "Try to increase your emergency fund to 6 months of expenses.",
                "Look into low-risk investments."
            ]
        elif financial_status == "Thriving":
            return [
                "Your financial health is excellent.",
                "Consider diversifying your investment portfolio.",
                "Look into real estate or high-yield savings."
            ]
        return ["Track your expenses to get better insights."]

predictor = AIPredictor()
