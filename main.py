from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from datetime import date, timedelta
from typing import List, Optional
import models
import schemas
from database import engine, SessionLocal
import tensorflow as tf
import pickle
import numpy as np
import random

# ==========================================
# 1. ІНІЦІАЛІЗАЦІЯ ТА НАЛАШТУВАННЯ
# ==========================================

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Basketball AI System API",
    description="Бекенд з авторизацією та ШІ-плануванням",
    version="1.2.1"
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

@app.get("/api/ping")
def ping_server():
    """Легкий маршрут для UptimeRobot, щоб сервер не засинав"""
    return {"status": "awake", "message": "Бекенд працює і готовий!"}        

# ==========================================
# 2. ФУНКЦІЇ БЕЗПЕКИ (КРИПТОГРАФІЯ)
# ==========================================

import jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta

SECRET_KEY = "diploma_super_secret_key_2026" # Ключ для шифрування (нікому не кажи!)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Токен живе 7 днів

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недійсний або протермінований токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# 3. МАРШРУТИ АВТОРИЗАЦІЇ ТА ПРОФІЛЮ
# ==========================================

@app.post("/api/users/register") 
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
    
    access_token = create_access_token(data={"sub": str(new_user.user_id)})
    
    return {
        "user_id": new_user.user_id,
        "name": new_user.name,
        "email": new_user.email,
        "access_token": access_token
    }

@app.post("/api/users/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невірний email або пароль")
    
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    return {
        "status": "success", 
        "user_id": user.user_id, 
        "name": user.name, 
        "access_token": access_token
    }

@app.get("/api/users/{user_id}", response_model=schemas.UserWithDetails)
def get_user(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Відмовлено в доступі. Це не ваші дані!")
        
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    
    import datetime as dt
    
    # Розрахунок Readiness Score
    sorted_metrics = sorted(user.metrics, key=lambda x: x.date)
    if not sorted_metrics:
        setattr(user, 'readiness_score', 100)
        setattr(user, 'acwr_ratio', "0.00")
        setattr(user, 'acwr_status', "Немає даних")
        return user
        
    last_metric = sorted_metrics[-1]
    sleep_points = min((last_metric.sleep_hours / 8.0) * 60, 60)
    fatigue_points = ((10 - last_metric.rpe_score) / 10.0) * 40
    setattr(user, 'readiness_score', round(sleep_points + fatigue_points))

    # Розрахунок ACWR
    now = dt.date.today()
    oldest_date = sorted_metrics[0].date
    days_in_system = (now - oldest_date).days + 1
    
    setattr(user, 'days_in_system', days_in_system)
    
    acute_load = 0
    chronic_load_total = 0
    
    for m in sorted_metrics:
        diff_days = (now - m.date).days
        daily_load = m.duration_minutes * m.rpe_score
        
        if diff_days <= 7:
            acute_load += daily_load
        if diff_days <= 28:
            chronic_load_total += daily_load
            
    import math
    weeks_in_system = min(4, max(1, math.ceil(days_in_system / 7.0)))
    chronic_load = chronic_load_total / weeks_in_system
    
    if chronic_load == 0:
        ratio = "2.00" if acute_load > 0 else "0.00"
    else:
        ratio = f"{(acute_load / chronic_load):.2f}"
        
    setattr(user, 'acwr_ratio', ratio)
    
    val = float(ratio)
    if val == 0: status_text = "Немає даних"
    elif val < 0.8: status_text = "Недотренованість"
    elif val <= 1.3: status_text = "Оптимальна зона"
    elif val <= 1.5: status_text = "Зона ризику"
    else: status_text = "Небезпека травми"
    
    setattr(user, 'acwr_status', status_text)

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

    for day_data in days:
        if day_data.activity_type != "Recovery":
            metric = models.DailyMetric(
                user_id=user_id,
                date=day_data.date,
                sleep_hours=day_data.sleep_hours,
                duration_minutes=day_data.duration_minutes,
                rpe_score=day_data.rpe_score,
                activity_type=day_data.activity_type
            )
        else:
            metric = models.DailyMetric(
                user_id=user_id,
                date=day_data.date,
                sleep_hours=day_data.sleep_hours,
                duration_minutes=0,
                rpe_score=0,
                activity_type="Recovery"
            )
        db.add(metric)

    db.commit()
    db.refresh(user)
    
    return user

# ==========================================
# 4. МАРШРУТИ ЗБОРУ ДАНИХ (МЕТРИКИ ТА ІНВЕНТАР)
# ==========================================

@app.post("/api/users/{user_id}/metrics", response_model=schemas.MetricResponse)
def create_metric(user_id: int, metric: schemas.MetricCreate, db: Session = Depends(get_db)):
    # Перевірка на дублікати: якщо запис за цю дату вже є, видаляємо старий
    existing_metric = db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user_id,
        models.DailyMetric.date == metric.date
    ).first()

    if existing_metric:
        db.delete(existing_metric)
        db.commit()

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
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    base_hours = 80.0

    weight_coeff = 1.0
    if user.weight_kg < 80:
        weight_coeff = 1.1
    elif user.weight_kg > 95:
        weight_coeff = 0.85

    surface_coeff = 1.0
    if shoe.surface_type == "Асфальт":
        surface_coeff = 0.5
    elif shoe.surface_type == "Гібрид (Мікс)":
        surface_coeff = 0.75
    elif shoe.surface_type == "Гума/Тартан":
        surface_coeff = 0.8

    type_coeff = 1.0
    if shoe.shoe_type != "Баскетбольні":
        type_coeff = 0.7

    calculated_max_lifespan = base_hours * weight_coeff * surface_coeff * type_coeff
    calculated_current_wear = calculated_max_lifespan * (shoe.initial_wear_percentage / 100.0)

    new_shoe = models.ShoeInventory(
        user_id=user_id,
        brand_model=shoe.brand_model,
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

try:
    model = tf.keras.models.load_model('basketball_lstm.keras')
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("ШІ-модель LSTM та Scaler успішно завантажені")
except Exception as e:
    print(f"Помилка завантаження моделі: {e}")
    model = None

@app.post("/api/ai/generate_plan/{user_id}", response_model=schemas.PlanResponse)
def generate_plan(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    metrics = sorted(user.metrics, key=lambda x: x.date)
    
    if len(metrics) < 7:
        return models.GeneratedPlan(
            user_id=user_id,
            date=date.today(),
            fatigue_risk="Optimal",
            plan_focus="Збір даних (Калібрування)",
            plan_content=f"Для роботи нейромережі LSTM потрібно 7 днів історії. Зараз у вас {len(metrics)}/7 днів.\nПродовжуйте вносити дані!"
        )

    # Підготовка часового ряду (захист від розривів у днях)
    last_date = metrics[-1].date
    metrics_dict = {m.date: m for m in metrics}
    last_7_days = []
    
    for i in range(6, -1, -1):
        target_date = last_date - timedelta(days=i)
        if target_date in metrics_dict:
            last_7_days.append(metrics_dict[target_date])
        else:
            # Пропущений день вважається днем відновлення
            empty_metric = models.DailyMetric(sleep_hours=8.0, rpe_score=0, duration_minutes=0, activity_type="Recovery")
            last_7_days.append(empty_metric)

    input_features = []
    for m in last_7_days:
        # Коефіцієнт змагального стресу: +25% до навантаження, якщо це Гра
        game_multiplier = 1.25 if m.activity_type == "Game" else 1.0
        
        effective_rpe = min(10.0, m.rpe_score * game_multiplier)
        effective_duration = m.duration_minutes * game_multiplier
        
        input_features.append([m.sleep_hours, effective_rpe, effective_duration])
    
    input_array = np.array(input_features)
    scaled_input = scaler.transform(input_array)
    final_input = scaled_input.reshape(1, 7, 3)

    if model:
        prediction = model.predict(final_input)
        risk_score = float(prediction[0][0])
    else:
        risk_score = 0.5 

    fatigue_status = "Optimal"
    if risk_score > 0.75:
        fatigue_status = "High Danger"
    elif risk_score > 0.4:
        fatigue_status = "Moderate Risk"

    focus = ""
    content = ""

    if fatigue_status == "High Danger":
        focus = "Повне відновлення"
        content = (
            f"ШІ зафіксував критичну втому ({int(risk_score*100)}%).\n"
            "Сьогодні робота тільки над відновленням:\n"
            "1. Контрастний душ або кріо-процедури.\n"
            "2. МТФ (масажний рол) - фокус на поперек та ікри.\n"
            "3. Повноцінний сон (9+ годин) та гідратація."
        )
    elif fatigue_status == "Moderate Risk":
        focus = "Технічна підготовка (Low Intensity)"
        content = (
            f"Ризик втоми помірний ({int(risk_score*100)}%). Уникаємо стрибків.\n"
            "1. Суглобова розминка - 15 хв.\n"
            "2. Штрафні кидки - 100 спроб.\n"
            "3. Робота над слабкою рукою (дриблінг на місці) - 15 хв.\n"
            "4. Розтяжка всього тіла."
        )
    else:
        warmups = ["Скакалка (3х3 хв)", "Робота з тенісним м'ячем (реакція)", "Динамічна розминка NBA-style"]
        
        drills_library = {
            "PG": ["Pick-and-roll passing", "Deep range shooting", "Speed dribbling", "Double crossover drills"],
            "SG": ["Catch and shoot (3pts)", "Coming off screens", "Floater development", "ISO moves"],
            "SF": ["Slash and kick", "Mid-range fadeaways", "Defensive sliding", "Fast break finishing"],
            "PF": ["Post-fade moves", "Pick and pop shooting", "Box-out drills", "Face-up drives"],
            "C": ["Rim protection positioning", "Mikan drill (finishing)", "Drop step moves", "Hook shots"]
        }

        position_drills = drills_library.get(user.position, ["Загальний дриблінг", "Кидки з дистанції", "Захисна стійка"])
        todays_warmup = random.choice(warmups)
        selected_drills = random.sample(position_drills, min(len(position_drills), 3))
        
        focus = f"Інтенсивний розвиток ({user.position})"
        content = (
            f"Прогноз стану: Оптимальний. Рівень ризику: {int(risk_score*100)}%.\n"
            f"1. {todays_warmup}\n"
            f"2. {selected_drills[0]}\n"
            f"3. {selected_drills[1]}\n"
            f"4. {selected_drills[2]}\n"
            "5. Високоінтенсивне інтервальне біг (5 хв)."
        )

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