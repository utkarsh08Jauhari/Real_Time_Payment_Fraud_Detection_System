from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from kafka import KafkaProducer  # type: ignore
import json
import pandas as pd  # type: ignore
import joblib  # type: ignore
import redis  # type: ignore
import hashlib

# ── Load ML Model ──────────────────────────────────────────────────────────────
model = joblib.load("model.joblib")

# ── Kafka Producer ─────────────────────────────────────────────────────────────
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# ── Redis Connection ───────────────────────────────────────────────────────────
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(title="SafetyPay Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Helper: Password Hashing ───────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Request Schemas ────────────────────────────────────────────────────────────
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


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def serve_login():
    return FileResponse("static/login.html")

@app.get("/register")
def serve_register():
    return FileResponse("static/register.html")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("static/dashboard.html")


# ── Register Endpoint ──────────────────────────────────────────────────────────
@app.post("/register")
def register(req: RegisterRequest):
    username = req.username.strip().lower()
    email    = req.email.strip().lower()

    if r.exists(f"user:{username}"):
        return {"status": "error", "message": "Username already exists!"}

    if r.exists(f"email:{email}"):
        return {"status": "error", "message": "Email already registered!"}

    r.hset(f"user:{username}", mapping={
        "username": username,
        "email":    email,
        "password": hash_password(req.password)
    })

    r.set(f"email:{email}", username)

    return {"status": "success", "message": "Registration successful!"}


# --------------- Login ------------- > 

@app.post("/login")
def login(req: LoginRequest):
    identifier = req.username.strip().lower()

    # email se login
    if r.exists(f"email:{identifier}"):
        username = r.get(f"email:{identifier}")
    else:
        username = identifier

    if not r.exists(f"user:{username}"):
        return {"status": "error", "message": "User not found"}

    stored_password = r.hget(f"user:{username}", "password")

    if stored_password != hash_password(req.password):
        return {"status": "error", "message": "Wrong password"}

    return {
        "status": "success",
        "username": username,
        "email": r.hget(f"user:{username}", "email")
    }



# ── Predict Endpoint ───────────────────────────────────────────────────────────
@app.post("/predict")
def predict(tx: TransactionRequest):

    # ❌ Insufficient balance
    if tx.amount > tx.oldbalanceOrg:
        return {
            "status": "error",
            "message": "Insufficient Balance"
        }

    receiver_balance   = 10000.0
    new_sender_balance = tx.oldbalanceOrg - tx.amount
    new_recv_balance   = receiver_balance + tx.amount

    transaction = {
        "step":           1,
        "type":           tx.type,
        "amount":         tx.amount,
        "oldbalanceOrg":  tx.oldbalanceOrg,
        "newbalanceOrig": new_sender_balance,
        "oldbalanceDest": receiver_balance,
        "newbalanceDest": new_recv_balance,
    }

    df         = pd.DataFrame([transaction])
    prediction = int(model.predict(df)[0])
    prob       = float(model.predict_proba(df)[0][1])

    if prediction == 1:
        return {
            "status":      "fraud",
            "message":     "FRAUD DETECTED - Transaction Blocked",
            "probability": round(prob, 4),
            "transaction": transaction
        }
    else:
        producer.send("fraud_detection", transaction)
        return {
            "status":      "approved",
            "message":     "Transaction Approved",
            "probability": round(prob, 4),
            "transaction": transaction
        }
    
# User History 
@app.get("/history/{username}")
def get_history(username: str):
    data = r.lrange(f"fraud_results:{username}", 0, 20)

    return [json.loads(item) for item in data]

# ── Run ────────────────────────────────────────────────────────────────────────
# python -m uvicorn app:app --reload --port 8000
