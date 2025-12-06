import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os

print("Loading WFP Food Prices dataset...")

# Load the WFP food prices dataset
df = pd.read_csv(
    os.path.join(os.path.dirname(__file__), 'wfp_food_prices_mwi.csv'),
    low_memory=False
)

print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# Remove header row (contains metadata tags like #date, #adm1+name, etc.)
df = df[df['date'] != '#date'].copy()

print("Cleaning and preprocessing data...")

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Convert price columns to numeric
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['usdprice'] = pd.to_numeric(df['usdprice'], errors='coerce')

# Drop rows with missing critical values
df = df.dropna(subset=['date', 'price', 'commodity'])

# Create time-based features
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_year'] = df['date'].dt.dayofyear

# Encode categorical variables
le_commodity = LabelEncoder()
le_market = LabelEncoder()
le_category = LabelEncoder()

df['commodity_encoded'] = le_commodity.fit_transform(df['commodity'].fillna('Unknown'))
df['market_encoded'] = le_market.fit_transform(df['market'].fillna('Unknown'))
df['category_encoded'] = le_category.fit_transform(df['category'].fillna('Unknown'))

print(f"Data cleaned: {df.shape[0]} rows remaining")

# ===== BEHAVIOR CLUSTERING MODEL =====
# Create user behavior profiles based on spending patterns
# Simulate user behavior from price data
print("\nTraining behavior clustering model...")

# Create synthetic user profiles based on price statistics
np.random.seed(42)
n_users = 1000

# Generate user profiles
user_data = {
    'income': np.random.choice([50000, 60000, 45000, 150000, 180000, 200000, 500000, 600000, 800000], n_users),
    'expenses': np.random.choice([48000, 58000, 44000, 100000, 120000, 130000, 200000, 250000, 300000], n_users),
    'savings': np.random.choice([2000, 2000, 1000, 50000, 60000, 70000, 300000, 350000, 500000], n_users)
}

user_df = pd.DataFrame(user_data)

# Train KMeans for user behavior clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(user_df)

# Save behavior model
joblib.dump(kmeans, os.path.join(os.path.dirname(__file__), 'behavior_model.pkl'))
print("[OK] Behavior clustering model trained and saved")

# ===== PRICE PREDICTION MODEL =====
# Train a model to predict food prices
print("\nTraining price prediction model...")

# Prepare features for price prediction
feature_cols = ['year', 'month', 'day_of_year', 'commodity_encoded', 'market_encoded', 'category_encoded']
X = df[feature_cols].copy()
y = df['price'].copy()

# Train Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10, n_jobs=-1)
rf_model.fit(X, y)

# Save price prediction model and encoders
joblib.dump(rf_model, os.path.join(os.path.dirname(__file__), 'price_prediction_model.pkl'))
joblib.dump(le_commodity, os.path.join(os.path.dirname(__file__), 'commodity_encoder.pkl'))
joblib.dump(le_market, os.path.join(os.path.dirname(__file__), 'market_encoder.pkl'))
joblib.dump(le_category, os.path.join(os.path.dirname(__file__), 'category_encoder.pkl'))

print("[OK] Price prediction model trained and saved")

# Print model performance summary
train_score = rf_model.score(X, y)
print(f"\nModel Performance:")
print(f"  - Training R² Score: {train_score:.4f}")
print(f"  - Unique commodities: {df['commodity'].nunique()}")
print(f"  - Unique markets: {df['market'].nunique()}")
print(f"  - Date range: {df['date'].min()} to {df['date'].max()}")

print("\n[SUCCESS] All models trained and saved successfully!")
