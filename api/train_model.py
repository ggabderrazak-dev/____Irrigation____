from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from fastapi import FastAPI
import numpy as np

model = RandomForestClassifier()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
joblib.dump(model, 'models/model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')  # Sauvegardez le scaler aussi

app = FastAPI()
model = joblib.load("models/model.pkl")
scaler = joblib.load("models/scaler.pkl")

@app.post("/predict")
def predict(soil_moisture: float, temperature: float, rainfall: float, humidity: float, sunlight_hours: float, soil_pH: float, pesticide_usage: float, NDVI_index: float):
    # Préparez les données d'entrée (ajustez selon vos features)
    input_data = np.array([[soil_moisture, temperature, rainfall, humidity, sunlight_hours, soil_pH, pesticide_usage, NDVI_index]])
    input_scaled = scaler.transform(input_data)
    result = model.predict(input_scaled)[0]
    return {"irrigation_needed": int(result)}