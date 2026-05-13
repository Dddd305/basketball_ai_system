from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Помилка: DATABASE_URL не знайдено у файлі .env або системі!")

# Двигун, який фізично виконує запити до БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Автоматично перевіряє, чи не "відвалилася" база перед запитом
    pool_recycle=300     # Примусово оновлює з'єднання кожні 5 хвилин (300 секунд)
)

# Створення фабрики сесій. Через сесію я буду додавати та читати дані
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для створення моделей (таблиць)
Base = declarative_base()