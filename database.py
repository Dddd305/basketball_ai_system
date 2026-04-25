from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Рядок підключення. Формат: postgresql://користувач:пароль@хост:порт/назва_бази
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_h0C9rlEwQFvn@ep-young-lake-alqfuwz1.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Двигун, який фізично виконує запити до БД
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Створення фабрики сесій. Через сесію я буду додавати та читати дані
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для створення моделей (таблиць)
Base = declarative_base()