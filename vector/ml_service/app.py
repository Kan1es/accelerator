import os
import logging
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ml_service")

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "classifier.joblib"),
)

ml_model = None

def load_model():
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Файл модели не найден: {MODEL_PATH}. "
            "Убедитесь, что модель обучена и размещена по указанному пути, "
            "либо задайте переменную окружения MODEL_PATH."
        )

    logger.info("Загрузка модели из %s …", MODEL_PATH)

    try:
        if MODEL_PATH.endswith(".joblib"):
            model = joblib.load(MODEL_PATH)
        elif MODEL_PATH.endswith(".pkl"):
            import pickle

            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
        else:
            # По умолчанию пробуем joblib
            model = joblib.load(MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"Не удалось загрузить модель из {MODEL_PATH}: {exc}"
        ) from exc

    logger.info("Модель успешно загружена ✔")
    return model


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_model

    logger.info("🚀 Запуск ML-сервиса …")
    ml_model = load_model()
    logger.info("ML-сервис готов к приёму запросов.")

    yield 

    logger.info("🛑 Остановка ML-сервиса …")
    ml_model = None
    logger.info("Ресурсы освобождены.")


app = FastAPI(
    title="Вектор — ML Service",
    description=(
        "Микросервис классификации обращений сотрудников. "
        "Определяет категорию и приоритет по тексту тикета."
    ),
    version="0.1.0",
    lifespan=lifespan,
)



class PredictRequest(BaseModel):

    text: str


class PredictResponse(BaseModel):

    category_id: int
    confidence: float


@app.get("/health")
async def health_check():
    return {
        "status": "ok" if ml_model is not None else "model_not_loaded",
        "model_loaded": ml_model is not None,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if ml_model is None:
        raise RuntimeError("Модель не загружена. Перезапустите сервис.")

    prediction = ml_model.predict([request.text])
    category_id = int(prediction[0])

    confidence = 0.0
    if hasattr(ml_model, "predict_proba"):
        probabilities = ml_model.predict_proba([request.text])
        confidence = float(probabilities.max())

    return PredictResponse(
        category_id=category_id,
        confidence=round(confidence, 4),
    )
