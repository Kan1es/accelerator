import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from transformers import AutoModel, AutoTokenizer

import psycopg
from psycopg_pool import ConnectionPool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ml_service")


# ─── Конфигурация ─────────────────────────────────────────────────────────────

_BASE = os.path.dirname(__file__)

MODEL_CHECKPOINT  = os.getenv("MODEL_CHECKPOINT",  os.path.join(_BASE, "artifacts", "best_model.pth"))
CLASS_MAPPING     = os.getenv("CLASS_MAPPING",     os.path.join(_BASE, "artifacts", "class_mapping.json"))
CATEGORY_NAMES    = os.getenv("CATEGORY_NAMES",    os.path.join(_BASE, "artifacts", "category_names.json"))
RUBERT_MODEL_NAME = os.getenv("RUBERT_MODEL_NAME", "cointegrated/rubert-tiny2")
NUM_CLASSES_ENV   = int(os.getenv("NUM_CLASSES", "14"))
DEVICE_ENV        = os.getenv("DEVICE", "auto")
INFERENCE_TIMEOUT = float(os.getenv("INFERENCE_TIMEOUT", "30.0"))  # секунды
FEEDBACK_DB_PATH  = os.getenv("FEEDBACK_DB_PATH",  os.path.join(_BASE, "feedback_buffer.db"))
FEEDBACK_DB_DSN = os.getenv("FEEDBACK_DB_DSN") or (
    f"host={os.getenv('FEEDBACK_DB_HOST', 'localhost')} "
    f"port={os.getenv('FEEDBACK_DB_PORT', '5432')} "
    f"dbname={os.getenv('FEEDBACK_DB_NAME', 'vector')} "
    f"user={os.getenv('FEEDBACK_DB_USER', 'postgres')} "
    f"password={os.getenv('FEEDBACK_DB_PASSWORD', 'postgres')}"
)
db_pool: ConnectionPool | None = None
MAX_LENGTH = 512


# ─── Состояние модели (dataclass вместо глобальных переменных) ────────────────

class ModelState:
    def __init__(self):
        self.bert_model:      Optional[nn.Module]           = None
        self.classifier_head: Optional[nn.Linear]           = None
        self.tokenizer:       Optional[AutoTokenizer]       = None
        self.device:          Optional[torch.device]        = None
        self.id_to_category:  dict[int, str]                = {}
        self.index_to_db_id:  dict[int, int]                = {}
        self.category_names:  dict[int, str]                = {}
        self.num_classes:     int                           = NUM_CLASSES_ENV
        self.load_error:      str                           = ""
        self.db_pool: Optional[ConnectionPool] = None

    @property
    def is_ready(self) -> bool:
        return self.bert_model is not None

    def release(self):
        self.bert_model      = None
        self.classifier_head = None
        self.tokenizer       = None
        if self.db_pool is not None:
            self.db_pool.close()
            self.db_pool = None


        # ─── Вспомогательные функции ─────────────────────────────────────────────────

def _resolve_device() -> torch.device:
    if DEVICE_ENV == "cpu":
        return torch.device("cpu")
    if DEVICE_ENV == "cuda":
        if not torch.cuda.is_available():
            logger.warning("DEVICE=cuda, но CUDA недоступна — используем CPU")
            return torch.device("cpu")
        return torch.device("cuda")
    chosen = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Автовыбор устройства: %s", chosen)
    return chosen


def _load_class_mapping() -> tuple[dict[int, str], dict[int, int], int]:
    if not os.path.isfile(CLASS_MAPPING):
        logger.warning(
            "class_mapping.json не найден: %s. "
            "Используем NUM_CLASSES=%d, category_db_id = model_index + 1.",
            CLASS_MAPPING, NUM_CLASSES_ENV,
        )
        n = NUM_CLASSES_ENV
        index_to_label = {i: f"Категория {i + 1}" for i in range(n)}
        index_to_db_id = {i: i + 1 for i in range(n)}
        return index_to_label, index_to_db_id, n

    with open(CLASS_MAPPING, "r", encoding="utf-8") as f:
        raw: dict = json.load(f)

    index_to_db_id: dict[int, int] = {}
    for k, v in raw.items():
        try:
            index_to_db_id[int(k)] = int(v)
        except (ValueError, TypeError):
            logger.warning("Некорректная запись в class_mapping.json: %s -> %s", k, v)

    n = len(index_to_db_id)
    index_to_label = {
        idx: f"Категория {db_id}"
        for idx, db_id in index_to_db_id.items()
    }

    logger.info(
        "Загружено %d категорий. Диапазон db_id: %d-%d",
        n,
        min(index_to_db_id.values()),
        max(index_to_db_id.values()),
    )
    return index_to_label, index_to_db_id, n

#Инициализация буфера фитбеков

DDL_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS ml_feedback_buffer (
    id                    BIGSERIAL PRIMARY KEY,
    text                  TEXT        NOT NULL,
    true_category_id      INTEGER     NOT NULL,
    predicted_category_id INTEGER,
    is_correct            BOOLEAN,
    confidence            REAL,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
    is_processed          BOOLEAN     NOT NULL DEFAULT FALSE
);
"""

DDL_FEEDBACK_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ml_feedback_unprocessed
ON ml_feedback_buffer (is_processed)
WHERE is_processed = FALSE;
"""


def _safe_dsn(dsn: str) -> str:
    """Скрывает пароль при логировании DSN."""
    return " ".join(p for p in dsn.split() if not p.startswith("password=")) + " password=***"


def init_feedback_pool() -> ConnectionPool:
    """Создаёт пул соединений с Postgres и таблицу буфера при первом запуске."""
    pool = ConnectionPool(
        conninfo=FEEDBACK_DB_DSN,
        min_size=1,
        max_size=5,
        kwargs={"autocommit": False},
        open=True,
    )
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL_FEEDBACK_TABLE)
            cur.execute(DDL_FEEDBACK_INDEX)
        conn.commit()
    logger.info("Буфер фидбэков готов (Postgres). DSN: %s", _safe_dsn(FEEDBACK_DB_DSN))
    return pool

# ─── Загрузка модели ─────────────────────────────────────────────────────────

def load_model() -> ModelState:
    state = ModelState()
    state.device = _resolve_device()

    state.id_to_category, state.index_to_db_id, state.num_classes = _load_class_mapping()

    if os.path.isfile(CATEGORY_NAMES):
        with open(CATEGORY_NAMES, "r", encoding="utf-8") as f:
            raw = json.load(f)
        state.category_names = {int(k): v for k, v in raw.items()}
        logger.info("Загружены названия категорий: %d штук", len(state.category_names))
    else:
        logger.warning("category_names.json не найден: %s.", CATEGORY_NAMES)

    if not os.path.isfile(MODEL_CHECKPOINT):
        raise FileNotFoundError(
            f"Чекпоинт не найден: '{MODEL_CHECKPOINT}'. "
            "Скопируйте best_model.pth из Google Drive в папку artifacts/."
        )

    tokenizer_path = os.path.join(_BASE, "artifacts", "tokenizer")
    if os.path.isdir(tokenizer_path):
        logger.info("Загрузка токенизатора из локальной папки: %s", tokenizer_path)
        state.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    else:
        logger.info("Загрузка токенизатора из HF Hub: %s", RUBERT_MODEL_NAME)
        state.tokenizer = AutoTokenizer.from_pretrained(RUBERT_MODEL_NAME)

    logger.info("Инициализация архитектуры BertModel (%s) ...", RUBERT_MODEL_NAME)
    try:
        bert_base = AutoModel.from_pretrained(RUBERT_MODEL_NAME)
    except OSError as exc:
        raise RuntimeError(
            f"Не удалось загрузить базовую модель '{RUBERT_MODEL_NAME}': {exc}."
        ) from exc

    hidden_size = bert_base.config.hidden_size
    bert_base.classifier = nn.Linear(hidden_size, state.num_classes)

    logger.info("Загрузка чекпоинта из %s ...", MODEL_CHECKPOINT)
    try:
        # FIX: weights_only=True — защита от вредоносного pickle
        checkpoint = torch.load(MODEL_CHECKPOINT, map_location=state.device, weights_only=True)
    except Exception as exc:
        raise RuntimeError(
            f"Не удалось прочитать чекпоинт: {exc}. "
            "Возможные причины: файл повреждён, несовместимая версия PyTorch."
        ) from exc

    if "model_state_dict" not in checkpoint:
        raise KeyError(
            "В чекпоинте нет ключа 'model_state_dict'. "
            f"Ключи в файле: {list(checkpoint.keys())}"
        )

    try:
        missing, unexpected = bert_base.load_state_dict(
            checkpoint["model_state_dict"], strict=False
        )
    except RuntimeError as exc:
        raise RuntimeError(
            f"Ошибка при загрузке весов: {exc}. "
            "Убедитесь, что NUM_CLASSES и архитектура совпадают с обучением."
        ) from exc

    if missing:
        logger.warning("Отсутствующие ключи: %s", missing)
    if unexpected:
        logger.info("Неожиданные ключи (игнорируются): %s", unexpected)

    best_acc = checkpoint.get("best_val_acc", "?")
    epoch    = checkpoint.get("epoch", "?")
    logger.info(
        "Чекпоинт загружен (эпоха %s, val_acc=%s)",
        epoch, f"{best_acc:.4f}" if isinstance(best_acc, float) else best_acc,
    )

    bert_base.to(state.device)
    bert_base.eval()

    state.bert_model      = bert_base
    state.classifier_head = bert_base.classifier

    logger.info("Сервис готов. hidden_size=%d, num_classes=%d", hidden_size, state.num_classes)
    return state


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск ML-сервиса ...")

    state = ModelState()
    try:
        state = load_model()
    except Exception as exc:
        state.load_error = str(exc)
        logger.error("Ошибка загрузки модели: %s", exc)
    try:
        state.db_pool = init_feedback_pool()
    except Exception as exc:
        logger.error("Не удалось инициализировать буфер фидбэков: %s", exc)

    app.state.model = state

    yield

    logger.info("Остановка ML-сервиса ...")
    app.state.model.release()
    logger.info("Ресурсы освобождены.")


# ─── Приложение ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Вектор — ML Service",
    description="Классификация обращений сотрудников. Архитектура: RuBERT-tiny2 + Linear head.",
    version="0.4.0",
    lifespan=lifespan,
)


# ─── Схемы ───────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    # FIX: ограничение длины входного текста
    text: str = Field(..., min_length=1, max_length=10_000)


class PredictResponse(BaseModel):
    category_id:    int
    category_db_id: int
    category_name:  str
    confidence:     float

class FeedbackRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    true_category_id: int = Field(..., ge=0)


class FeedbackResponse(BaseModel):
    status: str
    id: int

class AccuracyStatsResponse(BaseModel):
    total_samples: int
    samples_with_prediction: int
    correct_predictions: int
    accuracy: float
    avg_confidence: Optional[float]
    last_n: int


# ─── Inference (синхронная функция для run_in_executor) ───────────────────────

def _run_inference(state: ModelState, text: str) -> tuple[int, float]:
    """Выполняет inference в отдельном потоке, не блокируя event loop."""
    inputs = state.tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
        padding=True,
    )
    inputs = {k: v.to(state.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs       = state.bert_model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :]
        logits        = state.classifier_head(cls_embedding)

    probs       = torch.softmax(logits, dim=-1)
    confidence  = float(probs.max().item())
    category_id = int(torch.argmax(probs, dim=-1).item())
    return category_id, confidence


# ─── Эндпоинты ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check(request: Request):
    state: ModelState = request.app.state.model

    # FIX: возвращаем 503 если модель не загружена
    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "model_not_loaded",
                "model_loaded": False,
                "load_error": state.load_error or "см. логи запуска",
            },
        )

    return {
        "status": "ok",
        "model_loaded": True,
        "model": RUBERT_MODEL_NAME,
        "num_classes": state.num_classes,
        "device": str(state.device),
        "feedback_db_ready": state.db_pool is not None,
        "load_error": None,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest, http_request: Request):
    state: ModelState = http_request.app.state.model

    if not state.is_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Модель не загружена. Причина: {state.load_error or 'см. логи запуска'}",
        )

    text = request.text.strip()

    try:
        # FIX: inference в executor — не блокирует event loop
        # FIX: таймаут на inference
        loop = asyncio.get_running_loop()
        category_id, confidence = await asyncio.wait_for(
            loop.run_in_executor(None, _run_inference, state, text),
            timeout=INFERENCE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Inference превысил таймаут ({INFERENCE_TIMEOUT}s).",
        )
    except Exception as exc:
        logger.exception("Ошибка inference: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ошибка inference: {exc}") from exc

    category_db_id = state.index_to_db_id.get(category_id, category_id + 1)
    category_name  = state.category_names.get(category_db_id, f"Категория {category_db_id}")

    return PredictResponse(
        category_id=category_id,
        category_db_id=category_db_id,
        category_name=category_name,
        confidence=round(confidence, 4),
    )
@app.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(payload: FeedbackRequest, http_request: Request):
    """
    Принимает (text, true_category_id), прогоняет текст через текущую модель
    и сохраняет в буфер тройку (true, predicted, is_correct) для метрик.
    """
    state: ModelState = http_request.app.state.model

    if state.db_pool is None:
        raise HTTPException(status_code=503, detail="Буфер фидбэков недоступен")

    # Прогоняем модель — если она загружена.
    predicted_id: Optional[int] = None
    confidence: Optional[float] = None
    is_correct: Optional[bool] = None

    if state.is_ready:
        try:
            loop = asyncio.get_running_loop()
            category_index, conf = await asyncio.wait_for(
                loop.run_in_executor(None, _run_inference, state, payload.text),
                timeout=INFERENCE_TIMEOUT,
            )
            predicted_id = state.index_to_db_id.get(category_index, category_index + 1)
            confidence = round(conf, 4)
            is_correct = (predicted_id == payload.true_category_id)
        except Exception as exc:
            logger.warning("Не удалось получить предсказание для фидбэка: %s", exc)

    try:
        with state.db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ml_feedback_buffer
                        (text, true_category_id, predicted_category_id, is_correct, confidence)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (payload.text, payload.true_category_id, predicted_id, is_correct, confidence),
                )
                new_id = cur.fetchone()[0]
            conn.commit()
    except psycopg.Error as exc:
        logger.exception("Ошибка записи фидбэка: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save feedback") from exc

    logger.info(
        "Feedback stored: id=%s, true=%s, predicted=%s, correct=%s",
        new_id, payload.true_category_id, predicted_id, is_correct,
    )
    return FeedbackResponse(status="accepted", id=new_id)


@app.get("/stats/accuracy", response_model=AccuracyStatsResponse)
def stats_accuracy(http_request: Request, last_n: int = 100):
    """
    Возвращает метрики точности модели по последним `last_n` записям буфера.
    """
    state: ModelState = http_request.app.state.model

    if state.db_pool is None:
        raise HTTPException(status_code=503, detail="Буфер фидбэков недоступен")

    if last_n < 1:
        last_n = 100
    if last_n > 10_000:
        last_n = 10_000

    try:
        with state.db_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*)                                              AS total,
                        COUNT(predicted_category_id)                          AS with_pred,
                        COUNT(*) FILTER (WHERE is_correct IS TRUE)            AS correct,
                        AVG(confidence) FILTER (WHERE confidence IS NOT NULL) AS avg_conf
                    FROM (
                        SELECT predicted_category_id, is_correct, confidence
                        FROM ml_feedback_buffer
                        ORDER BY id DESC
                        LIMIT %s
                    ) sub
                    """,
                    (last_n,),
                )
                total, with_pred, correct, avg_conf = cur.fetchone()
    except psycopg.Error as exc:
        logger.exception("Ошибка чтения статистики: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to read stats") from exc

    accuracy = (correct / with_pred) if with_pred else 0.0

    return AccuracyStatsResponse(
        total_samples=total,
        samples_with_prediction=with_pred,
        correct_predictions=correct,
        accuracy=round(accuracy, 4),
        avg_confidence=round(float(avg_conf), 4) if avg_conf is not None else None,
        last_n=last_n,
    )

# ─── Локальный запуск ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )