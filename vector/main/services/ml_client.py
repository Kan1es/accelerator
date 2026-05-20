import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def classify_text(text: str):
    """
    Отправляет текст в ML-сервис и возвращает (category_id, confidence).
    При недоступности сервиса возвращает дефолтные значения из settings.
    """
    base_url = getattr(settings, 'ML_SERVICE_URL', 'http://ml-service:8000')
    url_post = f"{base_url}/predict"
    timeout = getattr(settings, 'ML_PREDICT_TIMEOUT', 3)
    default_category_id = getattr(settings, 'ML_DEFAULT_CATEGORY_ID', 1)

    try:
        response = requests.post(url_post, json={"text": text}, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("category_id"), data.get("confidence")
    except requests.exceptions.RequestException as exc:
        logger.warning("classify_text: ML-сервис недоступен: %s", exc)
        return default_category_id, 0


def fetch_ml_accuracy(last_n: int = 100) -> dict:
    """
    Запрашивает статистику точности у ML-сервиса.
    При ошибке возвращает структуру с флагом available=False.
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