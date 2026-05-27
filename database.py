"""
Модуль ініціалізації рівня зберігання даних.

Конфігурація з'єднання з PostgreSQL для Basketball AI Injury Prevention System (BAIPS).
Використовується синхронний рушій SQLAlchemy Core з наступними оптимізаціями:

- pool_pre_ping: автоматично відкидає розірвані з'єднання перед виконанням запиту,
  що є критичним для Render.com (хмарна платформа засипляє контейнери після простою).
- pool_recycle=300: примусово оновлює з'єднання кожні 5 хвилин, запобігаючи
  помилці "server closed the connection unexpectedly" після тривалої бездіяльності.
- pool_size / max_overflow: керування чергою пулу з'єднань під навантаженням.
- echo=False: SQL-лог вимкнено в production для безпеки.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# ==========================================
# 1. ВАЛІДАЦІЯ ПІДКЛЮЧЕННЯ
# ==========================================
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError(
        "[BAIS Database] КРИТИЧНА ПОМИЛКА: Змінна середовища "
        "'SQLALCHEMY_DATABASE_URL' не знайдена. "
        "Переконайтеся, що файл .env завантажено коректно."
    )

_EXPECTED_PREFIX = ("postgresql://", "postgresql+psycopg2://")
if not SQLALCHEMY_DATABASE_URL.startswith(_EXPECTED_PREFIX):
    raise ValueError(
        f"[BAIS Database] Невалідний формат DSN. "
        f"Очікується: postgresql:// або postgresql+psycopg2://"
    )

# ==========================================
# 2. ІНІЦІАЛІЗАЦІЯ ДВИГУНА
# ==========================================
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,         # перевірка живості з'єднання перед використанням
    pool_recycle=300,           # оновлення з'єднань кожні 5 хв
    pool_size=5,                # базовий розмір пулу з'єднань
    max_overflow=10,            # максимальне перевищення пулу під навантаженням
    pool_timeout=30,            # максимальний час очікування вільного з'єднання (сек)
    echo=False                  # вимкнути SQL-лог у production
)

# Створення фабрики сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для створення моделей
Base = declarative_base()