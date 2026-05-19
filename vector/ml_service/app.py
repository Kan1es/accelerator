"""
ml_service/app.py — FastAPI-сервис для кастомной RuBERT-архитектуры.

Архитектура модели (из Colab-ноутбука):
    BertModel (cointegrated/rubert-tiny2, hidden_size=312)
    + model.classifier = nn.Linear(312, num_classes)
    Inference: outputs.last_hidden_state[:, 0, :] → classifier → argmax

Чекпоинт сохранён через torch.save({
    'model_state_dict': ...,
    'optimizer_state_dict': ...,
    ...
}, "best_model.pth")

Переменные окружения:
    MODEL_CHECKPOINT   — путь к best_model.pth
                         (default: artifacts/best_model.pth)
    CLASS_MAPPING      — путь к class_mapping.json
                         (default: artifacts/class_mapping.json)
    RUBERT_MODEL_NAME  — имя базовой модели HF
                         (default: cointegrated/rubert-tiny2)
    NUM_CLASSES        — число классов (используется если нет JSON)
                         (default: 14)
    DEVICE             — "cpu" | "cuda" | "auto"
                         (default: auto)
"""

import json
import logging
import os
from contextlib import asynccontextmanager

import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer

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

MAX_LENGTH = 512

# ─── Глобальное состояние ────────────────────────────────────────────────────

bert_model     = None   # BertModel
classifier_head = None  # nn.Linear
tokenizer      = None
device         = None
id_to_category: dict[int, str] = {}   # model_index → "Категория N"
index_to_db_id: dict[int, int] = {}   # model_index → db category_id (1-based)
category_names: dict[int, str] = {}   # db_id → человекочитаемое название
num_classes: int = NUM_CLASSES_ENV
load_error: str = ""    # текст последней ошибки загрузки


# ─── Загрузка ────────────────────────────────────────────────────────────────

def _resolve_device() -> torch.device:
    if DEVICE_ENV == "cpu":
        return torch.device("cpu")
    if DEVICE_ENV == "cuda":
        if not torch.cuda.is_available():
            logger.warning("DEVICE=cuda, но CUDA недоступна — используем CPU")
            return torch.device("cpu")
        return torch.device("cuda")
    # auto
    chosen = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Автовыбор устройства: %s", chosen)
    return chosen


def _load_class_mapping() -> tuple[dict[int, str], dict[int, int], int]:
    """
    Загружает class_mapping.json.

    Формат файла: { "model_index": db_category_id }
    Пример:       { "0": 1, "1": 2, ..., "13": 14 }

    Возвращает:
        index_to_label  — { model_index: "Категория N" }  для отображения
        index_to_db_id  — { model_index: db_category_id } для передачи в Django
        num_classes     — количество классов
    """
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

    # Формат: { "0": 1, "1": 2, ... }
    # ключ   — строковый индекс модели (0-based)
    # значение — id категории в таблице categories БД (1-based)
    index_to_db_id: dict[int, int] = {}
    for k, v in raw.items():
        try:
            index_to_db_id[int(k)] = int(v)
        except (ValueError, TypeError):
            logger.warning("Некорректная запись в class_mapping.json: %s → %s", k, v)

    n = len(index_to_db_id)
    index_to_label = {
        idx: f"Категория {db_id}"
        for idx, db_id in index_to_db_id.items()
    }

    logger.info(
        "Загружено %d категорий. Диапазон db_id: %d–%d",
        n,
        min(index_to_db_id.values()),
        max(index_to_db_id.values()),
    )
    return index_to_label, index_to_db_id, n


def load_model():
    global bert_model, classifier_head, tokenizer, device
    global id_to_category, index_to_db_id, category_names, num_classes, load_error

    load_error = ""

    # 1. Устройство
    device = _resolve_device()

    # 2. Маппинг категорий
    id_to_category, index_to_db_id, num_classes = _load_class_mapping()

    # 3. Названия категорий из category_names.json
    if os.path.isfile(CATEGORY_NAMES):
        with open(CATEGORY_NAMES, "r", encoding="utf-8") as f:
            raw = json.load(f)
        category_names = {int(k): v for k, v in raw.items()}
        logger.info("Загружены названия категорий: %d штук", len(category_names))
    else:
        logger.warning("category_names.json не найден: %s. Будет использоваться 'Категория N'.", CATEGORY_NAMES)
        category_names = {}

    # 4. Проверка чекпоинта
    if not os.path.isfile(MODEL_CHECKPOINT):
        raise FileNotFoundError(
            f"Чекпоинт не найден: '{MODEL_CHECKPOINT}'. "
            "Скопируйте best_model.pth из Google Drive в папку artifacts/."
        )

    # 4. Токенизатор — сначала из локальной папки, потом из HF Hub
    tokenizer_path = os.path.join(os.path.dirname(MODEL_CHECKPOINT), "tokenizer")
    if os.path.isdir(tokenizer_path):
        logger.info("Загрузка токенизатора из локальной папки: %s", tokenizer_path)
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
    else:
        logger.info("Загрузка токенизатора из HF Hub: %s", RUBERT_MODEL_NAME)
        tokenizer = AutoTokenizer.from_pretrained(RUBERT_MODEL_NAME)

    # 5. Базовая BERT-модель (архитектура без весов чекпоинта — загружаем отдельно)
    logger.info("Инициализация архитектуры BertModel (%s) …", RUBERT_MODEL_NAME)
    try:
        bert_base = AutoModel.from_pretrained(RUBERT_MODEL_NAME)
    except OSError as exc:
        raise RuntimeError(
            f"Не удалось загрузить базовую модель '{RUBERT_MODEL_NAME}': {exc}. "
            "Проверьте интернет-соединение или разместите модель локально."
        ) from exc

    # 6. Навешиваем классификационную голову (точно как в Colab)
    hidden_size = bert_base.config.hidden_size   # 312 для rubert-tiny2
    head = nn.Linear(hidden_size, num_classes)
    bert_base.classifier = head

    # 7. Загружаем веса чекпоинта
    logger.info("Загрузка чекпоинта из %s …", MODEL_CHECKPOINT)
    try:
        checkpoint = torch.load(
            MODEL_CHECKPOINT,
            map_location=device,
            weights_only=False,   # нужно для совместимости с PyTorch < 2.4
        )
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
            "Убедитесь, что NUM_CLASSES и архитектура совпадают с теми, "
            "что использовались при обучении."
        ) from exc

    if missing:
        logger.warning("Отсутствующие ключи в чекпоинте: %s", missing)
    if unexpected:
        logger.info("Неожиданные ключи (игнорируются): %s", unexpected)

    best_acc = checkpoint.get("best_val_acc", "неизвестно")
    epoch    = checkpoint.get("epoch", "?")
    logger.info(
        "Чекпоинт загружен ✔  (эпоха %s, val_acc=%s)",
        epoch, f"{best_acc:.4f}" if isinstance(best_acc, float) else best_acc,
    )

    # 8. Переносим на устройство и переводим в eval-режим
    bert_base.to(device)
    bert_base.eval()

    bert_model      = bert_base
    classifier_head = bert_base.classifier
    logger.info("Сервис готов. hidden_size=%d, num_classes=%d", hidden_size, num_classes)


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global load_error

    logger.info("🚀 Запуск ML-сервиса …")
    try:
        load_model()
    except Exception as exc:
        load_error = str(exc)
        logger.error("❌ Ошибка загрузки модели: %s", exc)

    yield

    logger.info("🛑 Остановка ML-сервиса …")
    bert_model = None
    classifier_head = None
    tokenizer = None
    logger.info("Ресурсы освобождены.")


# ─── FastAPI ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Вектор — ML Service",
    description=(
        "Классификация обращений сотрудников. "
        "Архитектура: RuBERT-tiny2 + Linear head. "
        "Возвращает category_id, category_name и confidence."
    ),
    version="0.3.0",
    lifespan=lifespan,
)


# ─── Схемы ───────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    category_id: int      # индекс модели (0-based), для отладки
    category_db_id: int   # id в таблице categories БД (1-based) — используйте это
    category_name: str
    confidence: float


# ─── Эндпоинты ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "ok" if bert_model is not None else "model_not_loaded",
        "model_loaded": bert_model is not None,
        "model": RUBERT_MODEL_NAME,
        "num_classes": num_classes,
        "device": str(device) if device else "unknown",
        "load_error": load_error or None,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if bert_model is None:
        raise HTTPException(
            status_code=503,
            detail=f"Модель не загружена. Причина: {load_error or 'см. логи запуска'}",
        )

    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Поле text не может быть пустым.")

    try:
        # Токенизация
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_LENGTH,
            padding=True,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Forward pass (точно как в Colab)
        with torch.no_grad():
            outputs = bert_model(**inputs)
            cls_embedding = outputs.last_hidden_state[:, 0, :]   # [1, 312]
            logits = classifier_head(cls_embedding)               # [1, num_classes]

        # Softmax → уверенность
        probs = torch.softmax(logits, dim=-1)
        confidence = float(probs.max().item())
        category_id = int(torch.argmax(probs, dim=-1).item())

    except Exception as exc:
        logger.exception("Ошибка inference: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ошибка inference: {exc}") from exc

    category_db_id = index_to_db_id.get(category_id, category_id + 1)
    category_name  = category_names.get(category_db_id, f"Категория {category_db_id}")

    return PredictResponse(
        category_id=category_id,
        category_db_id=category_db_id,
        category_name=category_name,
        confidence=round(confidence, 4),
    )


# ─── Локальный запуск ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,   # reload=True конфликтует с CUDA-контекстом
        log_level="info",
    )
