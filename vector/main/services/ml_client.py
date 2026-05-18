import os
import requests
import dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

def classify_text(text):
    url_post = os.getenv("ML_SERVICE_URL", "http://localhost:8001/predict")
    body_request = {"text" : text}
    default_category_id = 1
    confidence = 0
    try:
        response = requests.post(url_post, json = body_request, timeout = 2)
        response.raise_for_status()
        data = response.json()
        return data.get("category_id"), data.get("confidence")
    except requests.exceptions.RequestException:
        return default_category_id, confidence