from kafka import KafkaConsumer # type: ignore
import json
import joblib  # type: ignore
import pandas as pd # type: ignore
import redis # type: ignore

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

model = joblib.load("model.joblib")

consumer = KafkaConsumer(
    "fraud_detection",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("Consumer running...")

for message in consumer:

    transaction = message.value

    df = pd.DataFrame([transaction])

    prediction = model.predict(df)[0]
    prob = model.predict_proba(df)[0][1]

    result = {
        "transaction": transaction,
        "prediction": int(prediction),
        "probability": float(prob)
    }
    
    r.lpush(f"fraud_results:{transaction['sender_id']}", json.dumps(result))

    if prediction == 1:
        print("🚨 FRAUD DETECTED")
    else:
        print("✅ Legitimate Transaction")

    print("Stored in Redis:", result)