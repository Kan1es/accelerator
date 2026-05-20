import os
import requests
import dotenv
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

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


def fetch_ml_accuracy(last_n: int = 100) -> dict:
    """
    Запрашивает статистику точности у ML-сервиса.
    При ошибке возвращает структуру с null-значениями.
    """
    ml_url = getattr(settings, 'ML_SERVICE_URL', 'http://ml-service:8000')
    timeout = getattr(settings, 'ML_STATS_TIMEOUT', 5)

    try:
        response = requests.get(
            f"{ml_url}/stats/accuracy",
            params={"last_n": last_n},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("fetch_ml_accuracy: ML-сервис недоступен: %s", exc)
        return {
            "available": False,
            "error": str(exc),
        }