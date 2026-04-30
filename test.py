import joblib
import os
scaler = joblib.load('backend/src/models/saved/scaler.pkl')
print(scaler.feature_names_in_)