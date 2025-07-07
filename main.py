from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import joblib
import os

app = FastAPI()

# Load models
model_likes = tf.keras.models.load_model("models/gru_best_model_likes.keras")
model_views = tf.keras.models.load_model("models/gru_best_model_views.keras")
model_comments = tf.keras.models.load_model("models/gru_best_model_comments.keras")

# Load scalers
scaler_likes = joblib.load("scalers/likes_scaler.pkl")
scaler_views = joblib.load("scalers/views_scaler.pkl")
scaler_comments = joblib.load("scalers/comments_scaler.pkl")

# Request schema
class EngagementInput(BaseModel):
    recent_engagement: list  # e.g., [1200, 1240, 1270, ...]
    prediction_type: str     # One of: "likes", "views", "comments"

@app.get("/")
def root():
    return {"message": "YouTube GRU engagement prediction API is live 🚀"}

@app.post("/predict")
def predict_engagement(data: EngagementInput):
    # Validate prediction_type
    pred_type = data.prediction_type.lower()
    if pred_type not in {"likes", "views", "comments"}:
        raise HTTPException(status_code=400, detail="prediction_type must be one of: likes, views, comments")

    # Convert and reshape input
    sequence = np.array(data.recent_engagement).reshape(-1, 1)

    # Select model and scaler
    if pred_type == "likes":
        model = model_likes
        scaler = scaler_likes
    elif pred_type == "views":
        model = model_views
        scaler = scaler_views
    elif pred_type == "comments":
        model = model_comments
        scaler = scaler_comments

    try:
        # Scale input and reshape for GRU
        scaled_seq = scaler.transform(sequence)
        input_seq = scaled_seq.reshape(1, -1, 1)  # Shape: (1, time_steps, 1)

        # Make prediction
        scaled_pred = model.predict(input_seq)[0][0]
        actual_pred = scaler.inverse_transform([[scaled_pred]])[0][0]

        return {
            "prediction_type": pred_type,
            "next_day_prediction": round(actual_pred, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
