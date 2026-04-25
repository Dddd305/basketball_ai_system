from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Рядок підключення. Формат: postgresql://користувач:пароль@хост:порт/назва_бази
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:qwerty12345@localhost:5432/basketball_db"

# Двигун, який фізично виконує запити до БД
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Створення фабрики сесій. Через сесію я буду додавати та читати дані
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для створення моделей (таблиць)
Base = declarative_base()