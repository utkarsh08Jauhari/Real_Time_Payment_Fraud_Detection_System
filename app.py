from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import pandas as pd
import joblib
import hashlib

# ── Load ML Model ─────────────────────────────────────────────

model = joblib.load("model.joblib")

# ── FastAPI App ──────────────────────────────────────────────

app = FastAPI(title="SafetyPay Fraud Detection API")

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["*"],
allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Helper ───────────────────────────────────────────────────

def hash_password(password: str) -> str:
return hashlib.sha256(password.encode()).hexdigest()

# ── Schemas ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
username: str
email: str
password: str

class LoginRequest(BaseModel):
username: str
password: str

class TransactionRequest(BaseModel):
type: str
amount: float
oldbalanceOrg: float
sender_id: str
receiver_id: str

# ── Routes ───────────────────────────────────────────────────

@app.get("/")
def serve_login():
return FileResponse("static/login.html")

@app.get("/register")
def serve_register():
return FileResponse("static/register.html")

@app.get("/dashboard")
def serve_dashboard():
return FileResponse("static/dashboard.html")

# ── Register Ka Code ──────────────────────────────

@app.post("/register")
def register(req: RegisterRequest):
return {
"status": "success",
"message": "Registration disabled in deployed version"
}

# ── Login Ka Code ─────────────────────────────────

@app.post("/login")
def login(req: LoginRequest):
return {
"status": "success",
"username": "demo_user",
"email": "[demo@email.com](mailto:demo@email.com)"
}

# ── Predict Model se ──────────────────────────────────────────

@app.post("/predict")
def predict(tx: TransactionRequest):

```
if tx.amount > tx.oldbalanceOrg:
    return {
        "status": "error",
        "message": "Insufficient Balance"
    }

receiver_balance   = 10000.0
new_sender_balance = tx.oldbalanceOrg - tx.amount
new_recv_balance   = receiver_balance + tx.amount

transaction = {
    "step": 1,
    "type": tx.type,
    "amount": tx.amount,
    "oldbalanceOrg": tx.oldbalanceOrg,
    "newbalanceOrig": new_sender_balance,
    "oldbalanceDest": receiver_balance,
    "newbalanceDest": new_recv_balance,
}

df = pd.DataFrame([transaction])
prediction = int(model.predict(df)[0])
prob = float(model.predict_proba(df)[0][1])

if prediction == 1:
    return {
        "status": "fraud",
        "message": "FRAUD DETECTED - Transaction Blocked",
        "probability": round(prob, 4),
        "transaction": transaction
    }
else:
    return {
        "status": "approved",
        "message": "Transaction Approved",
        "probability": round(prob, 4),
        "transaction": transaction
    }
```

# ── History Payments ki ────────────────

@app.get("/history/{username}")
def get_history(username: str):
return []
