import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Load data
data_path = os.path.join(os.path.dirname(__file__), 'dataset_malawi.csv')
df = pd.read_csv(data_path)

# Preprocessing
df['date'] = pd.to_datetime(df['date'])
df['month_num'] = (df['date'].dt.year - df['date'].dt.year.min()) * 12 + df['date'].dt.month

le = LabelEncoder()
df['item_encoded'] = le.fit_transform(df['item'])

# Train Model
X = df[['month_num', 'item_encoded']]
y = df['price']

model = LinearRegression()
model.fit(X, y)

# Save artifacts
joblib.dump(model, os.path.join(os.path.dirname(__file__), 'price_model.pkl'))
joblib.dump(le, os.path.join(os.path.dirname(__file__), 'item_encoder.pkl'))

print("Price prediction model trained and saved.")
