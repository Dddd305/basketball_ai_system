from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from datetime import date
from typing import List, Optional
import models
import schemas
from database import engine, SessionLocal

# ==========================================
# 1. ІНІЦІАЛІЗАЦІЯ ТА НАЛАШТУВАННЯ
# ==========================================

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Basketball AI System API",
    description="Бекенд з авторизацією та ШІ-плануванням",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. ФУНКЦІЇ БЕЗПЕКИ (КРИПТОГРАФІЯ)
# ==========================================

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# ==========================================
# 3. МАРШРУТИ АВТОРИЗАЦІЇ ТА ПРОФІЛЮ
# ==========================================

@app.post("/api/users/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Цей Email вже зайнятий")
    
    new_user = models.User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        name=user.name,
        age=user.age,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        position=user.position
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/users/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невірний email або пароль")
    
    return {"status": "success", "user_id": user.user_id, "name": user.name}

@app.get("/api/users/{user_id}", response_model=schemas.UserWithDetails)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")
    return user

@app.put("/api/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    if user_update.name is not None: db_user.name = user_update.name
    if user_update.age is not None: db_user.age = user_update.age
    if user_update.height_cm is not None: db_user.height_cm = user_update.height_cm
    if user_update.weight_kg is not None: db_user.weight_kg = user_update.weight_kg
    if user_update.position is not None: db_user.position = user_update.position

    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/users/{user_id}/calibrate", response_model=schemas.UserWithDetails)
def calibrate_user(user_id: int, days: List[schemas.CalibrationDay], db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    # Перебираємо масив днів, який надіслав фронтенд
    for day_data in days:
        if day_data.trained:
            # Записуємо тренування
            metric = models.DailyMetric(
                user_id=user_id,
                date=day_data.date,
                sleep_hours=day_data.sleep_hours,
                duration_minutes=day_data.duration_minutes,
                rpe_score=day_data.rpe_score,
                activity_type="Баскетбол (Калібрування)"
            )
        else:
            # Записуємо день відпочинку
            metric = models.DailyMetric(
                user_id=user_id,
                date=day_data.date,
                sleep_hours=day_data.sleep_hours,
                duration_minutes=0,
                rpe_score=0,
                activity_type="Відновлення"
            )
        db.add(metric)

    # Зберігаємо всі 7 днів у базу одним комітом
    db.commit()
    db.refresh(user)
    
    return user

# ==========================================
# 4. МАРШРУТИ ЗБОРУ ДАНИХ (МЕТРИКИ ТА ІНВЕНТАР)
# ==========================================

@app.post("/api/users/{user_id}/metrics", response_model=schemas.MetricResponse)
def create_metric(user_id: int, metric: schemas.MetricCreate, db: Session = Depends(get_db)):
    new_metric = models.DailyMetric(**metric.dict(), user_id=user_id)
    db.add(new_metric)
    
    # Логіка зносу кросівок
    if metric.shoe_id and metric.activity_type != "Recovery":
        shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == metric.shoe_id).first()
        if shoe:
            shoe.current_hours_played += metric.duration_minutes / 60.0

    db.commit()
    db.refresh(new_metric)
    return new_metric

@app.post("/api/users/{user_id}/shoes", response_model=schemas.ShoeResponse)
def add_shoe(user_id: int, shoe: schemas.ShoeCreate, db: Session = Depends(get_db)):
    # Знаходимо користувача, щоб взяти його вагу
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    # 1. Базовий ресурс
    base_hours = 80.0

    # 2. Коефіцієнт ваги (беремо з профілю гравця!)
    weight_coeff = 1.0
    if user.weight_kg < 80:
        weight_coeff = 1.1
    elif user.weight_kg > 95:
        weight_coeff = 0.85

    # 3. Коефіцієнт покриття
    surface_coeff = 1.0
    if shoe.surface_type == "Асфальт":
        surface_coeff = 0.5
    elif shoe.surface_type == "Гібрид (Мікс)":
        surface_coeff = 0.75
    elif shoe.surface_type == "Гума/Тартан":
        surface_coeff = 0.8

    # 4. Коефіцієнт типу взуття
    type_coeff = 1.0
    if shoe.shoe_type != "Баскетбольні":
        type_coeff = 0.7

    # --- МАТЕМАТИКА ШІ-КАЛЬКУЛЯТОРА ---
    calculated_max_lifespan = base_hours * weight_coeff * surface_coeff * type_coeff
    
    # Вираховуємо, скільки годин вже "відіграно", якщо користувач вказав б/в кросівки
    calculated_current_wear = calculated_max_lifespan * (shoe.initial_wear_percentage / 100.0)

    # Створюємо запис у базі
    new_shoe = models.ShoeInventory(
        user_id=user_id,
        brand_model=shoe.brand_model,
        # Зберігаємо інформацію про тип і покриття замість cushion_type
        cushion_type=f"{shoe.shoe_type} | {shoe.surface_type}", 
        max_lifespan_hours=calculated_max_lifespan,
        current_hours_played=calculated_current_wear
    )
    
    db.add(new_shoe)
    db.commit()
    db.refresh(new_shoe)
    return new_shoe

@app.delete("/api/shoes/{shoe_id}")
def delete_shoe(shoe_id: int, db: Session = Depends(get_db)):
    shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == shoe_id).first()
    if not shoe:
        raise HTTPException(status_code=404, detail="Кросівки не знайдено")
    db.delete(shoe)
    db.commit()
    return {"status": "success"}

# ==========================================
# 5. ШІ ТА АНАЛІТИКА
# ==========================================

@app.post("/api/ai/generate_plan/{user_id}", response_model=schemas.PlanResponse)
def generate_plan(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    # ЗАХИСТ ВІД "ХОЛОДНОГО СТАРТУ"
    if not user.metrics or len(user.metrics) == 0:
        fallback_plan = models.GeneratedPlan(
            user_id=user_id,
            date=date.today(),
            fatigue_risk="Optimal",
            plan_focus="Калібрування (Ввідне тренування)",
            plan_content="Система ще не має історії ваших навантажень.\n\nСьогодні виконайте легке тренування (30-40 хв, RPE 4-5) та збережіть його в 'Активність'. Це дозволить алгоритмам почати розрахунок вашого ACWR."
        )
        db.add(fallback_plan)
        db.commit()
        db.refresh(fallback_plan)
        return fallback_plan

    # АНАЛІЗ ДАНИХ (Якщо метрики вже існують)
    last_metric = sorted(user.metrics, key=lambda x: x.date)[-1]
    
    # Логіка визначення втоми
    fatigue_status = "Optimal"
    if last_metric.sleep_hours < 6 or last_metric.rpe_score >= 8:
        fatigue_status = "High Danger"
    elif last_metric.rpe_score >= 6:
        fatigue_status = "Moderate Risk"

    # Логіка генерації контенту на основі амплуа
    focus = ""
    content = ""

    if "Danger" in fatigue_status:
        focus = "Відновлення (Recovery)"
        content = "Виявлено високий рівень втоми.\n1. МТФ (масажним ролом) - 15 хв.\n2. Статична розтяжка.\n3. Повноцінний сон сьогодні вночі."
    else:
        if user.position in ["PG", "SG"]:
            focus = "Швидкість та гра на периметрі"
            content = "1. Динамічна розминка - 10 хв.\n2. Дриблінг на максимальній швидкості - 15 хв.\n3. Кидки після заслону - 100 влучань."
        elif user.position == "SF":
            focus = "Універсальність (Wing Skills)"
            content = "1. Динамічна розминка - 10 хв.\n2. Проходи під кільце з опором - 15 хв.\n3. Кидки Catch and Shoot - 100 влучань."
        else:
            focus = "Гра під кільцем (Post Skills)"
            content = "1. Динамічна розминка - 10 хв.\n2. Робота на вусах (Post moves) - 20 хв.\n3. Підбирання та добивання - 50 разів."

    new_plan = models.GeneratedPlan(
        user_id=user_id,
        date=date.today(),
        fatigue_risk=fatigue_status,
        plan_focus=focus,
        plan_content=content
    )
    
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan