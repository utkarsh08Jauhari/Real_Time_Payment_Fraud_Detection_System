import json
import joblib
import pandas as pd

model = joblib.load("model.joblib")

print("Dummy Consumer running...")

# Teansaction
transaction = {
    "step": 1,
    "type": "PAYMENT",
    "amount": 1000,
    "oldbalanceOrg": 5000,
    "newbalanceOrig": 4000,
    "oldbalanceDest": 10000,
    "newbalanceDest": 11000
}

df = pd.DataFrame([transaction])

prediction = model.predict(df)[0]
prob = model.predict_proba(df)[0][1]

result = {
    "transaction": transaction,
    "prediction": int(prediction),
    "probability": float(prob)
}

print("Processed result:", result)
