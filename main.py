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
import warnings
import math

warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# 1. ІНІЦІАЛІЗАЦІЯ ТА НАЛАШТУВАННЯ
# ==========================================

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BAIPS API",
    description="Бекенд з авторизацією та ШІ-плануванням",
    version="1.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://basketball-ai-system.vercel.app"
    ],
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
import os
from dotenv import load_dotenv 

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Помилка: SECRET_KEY не знайдено!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

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
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
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
    
# Маршрут для зміни пароля
@app.put("/api/users/me/change-password")
def change_password(
    pass_data: schemas.PasswordChange, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    if not verify_password(pass_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Старий пароль невірний")
    
    current_user.password_hash = get_password_hash(pass_data.new_password)
    db.commit()
    return {"message": "Пароль успішно змінено"}  

# Маршрут для зміни Email
@app.put("/api/users/me/change-email")
def change_email(
    email_data: schemas.EmailChange, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    user_check = db.query(models.User).filter(models.User.email == email_data.new_email).first()
    if user_check:
        raise HTTPException(status_code=400, detail="Цей Email вже використовується")
    
    current_user.email = email_data.new_email
    db.commit()
    return {"message": "Email змінено"}

# Маршрут для видалення акаунта 
@app.delete("/api/users/me")
def delete_account(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()
    return {"message": "Акаунт видалено назавжди"}

@app.get("/api/users/{user_id}", response_model=schemas.UserWithDetails)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Розрахунок Readiness Score
    sorted_metrics = sorted(user.metrics, key=lambda x: x.date)
    if not sorted_metrics:
        setattr(user, 'readiness_score', 100)
        setattr(user, 'fatigue_risk', "Немає даних")
        return user
        
    last_metric = sorted_metrics[-1]
    sleep_points = min((last_metric.sleep_hours / 8.0) * 60, 60)
    fatigue_points = ((10 - last_metric.rpe_score) / 10.0) * 40
    base_readiness = sleep_points + fatigue_points

    # Плавний HRV модифікатор
    if last_metric.hrv_value and last_metric.hrv_value > 0:
        raw_hrv_mod = 1.0 + (last_metric.hrv_value - 55) * 0.005
        base_readiness *= max(0.80, min(1.20, raw_hrv_mod))

    setattr(user, 'readiness_score', min(100, round(base_readiness)))

    # Живий розрахунок Fatigue Risk
    if len(sorted_metrics) >= 7:
        last_7 = sorted_metrics[-7:]
        input_features = []
        for m in last_7:
            mult = 1.25 if m.activity_type == "Game" else 1.0
            input_features.append([m.sleep_hours, min(10.0, m.rpe_score * mult), m.duration_minutes * mult])
        
        try:
            scaled_input = scaler.transform(np.array(input_features))
            final_input = scaled_input.reshape(1, 7, 3)
            prediction = model.predict(final_input)
            risk_score = float(prediction[0][0])

            # Плавний HRV модифікатор для ризику
            latest_hrv = next((m.hrv_value for m in reversed(last_7) if m.hrv_value and m.hrv_value > 0), None)
            if latest_hrv:
                raw_risk_mod = 1.0 - (latest_hrv - 55) * 0.008
                risk_score *= max(0.75, min(1.25, raw_risk_mod))

            if risk_score > 0.75: fatigue_label = "High Danger"
            elif risk_score > 0.4: fatigue_label = "Moderate Risk"
            else: fatigue_label = "Optimal"
            
            setattr(user, 'fatigue_risk', fatigue_label)
        except:
            setattr(user, 'fatigue_risk', "Помилка ШІ")
    else:
        setattr(user, 'fatigue_risk', "Калібрування")

    # Розрахунок ACWR
    now = date.today()
    oldest_date = sorted_metrics[0].date
    days_in_system = (now - oldest_date).days + 1
    
    setattr(user, 'days_in_system', days_in_system)
    
    acute_days = [m for m in sorted_metrics if (now - m.date).days <= 6]   # 7-денне вікно (включно з сьогодні)
    chronic_days = [m for m in sorted_metrics if (now - m.date).days <= 27] # 28-денне вікно
    
    def calculate_load(metrics_list):
            return sum(
                m.duration_minutes * m.rpe_score * (1.25 if m.activity_type == "Game" else 1.0)
                for m in metrics_list
            )

    acute_load_total = calculate_load(acute_days)
    chronic_load_total = calculate_load(chronic_days)
    
    weeks_in_system = min(4, max(1, math.ceil(days_in_system / 7.0)))
    chronic_load_avg = chronic_load_total / weeks_in_system if weeks_in_system else 0
    
    if chronic_load_avg == 0:
        ratio = "2.00" if acute_load_total > 0 else "0.00"
    else:
        ratio = f"{(acute_load_total / chronic_load_avg):.2f}"
        
    setattr(user, 'acwr_ratio', ratio)
    
    val = float(ratio)
    if val == 0: acwr_label = "Немає даних"
    elif val < 0.8: acwr_label = "Недотренованість"
    elif val <= 1.3: acwr_label = "Оптимальна зона"
    elif val <= 1.5: acwr_label = "Зона ризику"
    else: acwr_label = "Небезпека травми"
    
    setattr(user, 'acwr_status', acwr_label)

    return user

@app.put("/api/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int, 
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:                               
        raise HTTPException(status_code=403, detail="Доступ заборонено")

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
def calibrate_user(
    user_id: int, 
    days: List[schemas.CalibrationDay], 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено") 

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")
    
    dates_to_calibrate = [day.date for day in days]
    
    old_metrics = db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user_id,
        models.DailyMetric.date.in_(dates_to_calibrate)
    ).all()

    for old_m in old_metrics:
        if old_m.shoe_id and old_m.activity_type != "Recovery":
            shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == old_m.shoe_id).first()
            if shoe:
                shoe.current_hours_played = max(0.0, shoe.current_hours_played - (old_m.duration_minutes / 60.0))

    db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user_id,
        models.DailyMetric.date.in_(dates_to_calibrate)
    ).delete(synchronize_session=False)
    
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
def create_metric(
    user_id: int, 
    metric: schemas.MetricCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  
):
    if current_user.user_id != user_id:                     
        raise HTTPException(status_code=403, detail="Доступ заборонено")
        
    existing_metrics = db.query(models.DailyMetric).filter(
        models.DailyMetric.user_id == user_id,
        models.DailyMetric.date == metric.date
    ).all()

    for ex_metric in existing_metrics:
        if ex_metric.shoe_id and ex_metric.activity_type != "Recovery":
            old_shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == ex_metric.shoe_id).first()
            if old_shoe:
                old_shoe.current_hours_played -= ex_metric.duration_minutes / 60.0
                old_shoe.current_hours_played = max(0.0, old_shoe.current_hours_played) # Захист від мінусів
        
        db.delete(ex_metric)
        
    db.commit()

    new_metric = models.DailyMetric(**metric.dict(), user_id=user_id)
    db.add(new_metric)
    if metric.shoe_id and metric.activity_type != "Recovery":
        shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == metric.shoe_id).first()
        if shoe:
            shoe.current_hours_played += metric.duration_minutes / 60.0

    db.commit()
    db.refresh(new_metric)
    return new_metric

@app.delete("/api/users/{user_id}/metrics/{metric_id}")
def delete_metric(
    user_id: int, 
    metric_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")

    metric = db.query(models.DailyMetric).filter(
        models.DailyMetric.metric_id == metric_id,
        models.DailyMetric.user_id == user_id
    ).first()

    if not metric:
        raise HTTPException(status_code=404, detail="Метрику не знайдено")

    if metric.shoe_id and metric.activity_type != "Recovery":
        shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == metric.shoe_id).first()
        if shoe:
            shoe.current_hours_played = max(0.0, shoe.current_hours_played - (metric.duration_minutes / 60.0))

    db.delete(metric)
    db.commit()
    return {"status": "success", "message": "Тренування успішно видалено"}

@app.post("/api/users/{user_id}/shoes", response_model=schemas.ShoeResponse)
def add_shoe(
    user_id: int, 
    shoe: schemas.ShoeCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    base_hours = 80.0
    raw_weight_coeff = 1.0 - (user.weight_kg - 85) * 0.01
    weight_coeff = max(0.75, min(1.25, raw_weight_coeff))

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
def delete_shoe(
    shoe_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    shoe = db.query(models.ShoeInventory).filter(models.ShoeInventory.shoe_id == shoe_id).first()
    if not shoe:
        raise HTTPException(status_code=404, detail="Кросівки не знайдено")
        
    if shoe.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")
        
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
    scaler = None

@app.post("/api/ai/generate_plan/{user_id}", response_model=schemas.PlanResponse)
def generate_plan(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ заборонено")

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Гравця не знайдено")

    today = date.today()
    existing_plan = db.query(models.GeneratedPlan).filter(
        models.GeneratedPlan.user_id == user_id,
        models.GeneratedPlan.date == today
    ).first()

    metrics = sorted(user.metrics, key=lambda x: x.date)
    
    if len(metrics) < 7:
        return schemas.PlanResponse(
            plan_id=0,
            date=today,
            fatigue_risk="Optimal",
            plan_focus="Збір даних (Калібрування)",
            plan_content=f"Для роботи нейромережі LSTM потрібно 7 днів історії. Зараз у вас {len(metrics)}/7 днів.\nПродовжуйте вносити дані!"
        )

    # Підготовка даних для LSTM
    last_date = metrics[-1].date
    metrics_dict = {m.date: m for m in metrics}
    last_7_days = []
    
    for i in range(6, -1, -1):
        target_date = last_date - timedelta(days=i)
        if target_date in metrics_dict:
            last_7_days.append(metrics_dict[target_date])
        else:
            empty_metric = models.DailyMetric(sleep_hours=8.0, rpe_score=0, duration_minutes=0, activity_type="Recovery")
            last_7_days.append(empty_metric)

    input_features = []
    for m in last_7_days:
        game_multiplier = 1.25 if m.activity_type == "Game" else 1.0
        effective_rpe = min(10.0, m.rpe_score * game_multiplier)
        effective_duration = m.duration_minutes * game_multiplier
        input_features.append([m.sleep_hours, effective_rpe, effective_duration])
    
    input_array = np.array(input_features)

    if model is not None and scaler is not None:
        scaled_input = scaler.transform(input_array)
        final_input = scaled_input.reshape(1, 7, 3)
        prediction = model.predict(final_input, verbose=0)
        risk_score = float(prediction[0][0])
    else:   
        risk_score = 0.5 

    # Гібридний алгоритм (плавний HRV)
    latest_hrv = next((m.hrv_value for m in reversed(last_7_days) if m.hrv_value is not None and m.hrv_value > 0), None)
    if latest_hrv:
        raw_risk_mod = 1.0 - (latest_hrv - 55) * 0.008
        risk_modifier = max(0.75, min(1.25, raw_risk_mod))
        risk_score *= risk_modifier
         
    risk_score = max(0.0, min(risk_score, 1.0))

    # Класифікація рівня ризику за трипороговою шкалою
    if risk_score > 0.75:
        fatigue_status = "High Danger"
    elif risk_score > 0.40:
        fatigue_status = "Moderate Risk"
    else:
        fatigue_status = "Optimal"

    # Бібліотека знань ШІ-Тренера
    RECOVERY_TOOLKIT = [
        "Контрастний душ (3х45 сек)", 
        "Міофасціальний реліз (МФР) квадрицепсів",
        "Йога для баскетболістів (15 хв)", 
        "Суглобова гімнастика Бубновського",
        "Дихальна техніка 4-7-8", 
        "Прогулянка на свіжому повітрі (20 хв)",
        "Масажний пістолет (м'язи гомілки)"
    ]

    LOW_IMPACT_DRILLS = [
        "Штрафні кидки (5 серій по 10)",
        "Дриблінг на місці (слабка рука, 10 хв)",
        "Form shooting (кидки однією рукою з-під кільця)",
        "Робота ніг без м'яча на низькій швидкості",
        "Аналіз відео (вивчення плейбуку або розбір ігор)",
        "Кидки з місця без стрибків (Catch and shoot)"
    ]

    POSITION_DRILL_MATRIX = {
        "PG": {"primary": ["Speed dribbling з конусами", "Floater mechanics", "Pick-and-roll read"], 
               "secondary": ["Court vision drills", "Double crossover"]},
        "SG": {"primary": ["Catch-and-shoot off screens", "ISO mid-range", "One-dribble pull-up"],
               "secondary": ["Transition 3s", "Corner 3pt precision"]},
        "SF": {"primary": ["Wing slash-and-kick", "Fadeaway mid-range", "Wing 1-on-1 attacks"],
               "secondary": ["Defensive close-out slides", "Rebound-and-outlet"]},
        "PF": {"primary": ["Post-up power moves", "Pick-and-pop spacing", "Face-up drives"],
               "secondary": ["Box-out battle drills", "Offensive put-backs"]},
        "C":  {"primary": ["Mikan drill (обидві руки)", "Drop-step hook", "Rim protection positioning"],
               "secondary": ["High-post two-man game", "Vertical jump timing"]}
    }
    
    warmups = ["Скакалка (3х3 хв)", "Робота з тенісним м'ячем", "Динамічна розминка", "Координаційна драбина"]

    risk_percent = int(risk_score * 100)

    # Генерація унікального контенту
    if fatigue_status == "High Danger":
        focus = "Повне відновлення ЦНС"
        selected = random.sample(RECOVERY_TOOLKIT, 3)
        content = (
            f"ШІ зафіксував критичний ризик втоми ({risk_percent}%).\n"
            f"Будь-яке навантаження сьогодні підвищує ризик травми.\n\n"
            f"Ваш протокол відновлення:\n"
            f"1. {selected[0]}\n"
            f"2. {selected[1]}\n"
            f"3. {selected[2]}\n\n"
            f"Обов'язковий мінімум сну цієї ночі: 8.5 годин."
        )
        
    elif fatigue_status == "Moderate Risk":
        focus = "Техніка (Low Impact)"
        selected = random.sample(LOW_IMPACT_DRILLS, 3)
        content = (
            f"Ризик втоми підвищений ({risk_percent}%).\n"
            f"Тіло потребує відпочинку від ударних навантажень. Жодних стрибків чи спринтів.\n\n"
            f"План на сьогодні:\n"
            f"1. Суглобова розминка (10 хв)\n"
            f"2. {selected[0]}\n"
            f"3. {selected[1]}\n"
            f"4. {selected[2]}"
        )
        
    else:
        position = user.position if user.position in POSITION_DRILL_MATRIX else "PG"
        pos_data = POSITION_DRILL_MATRIX[position]
        # 2 первинні та 1 вторинна навички для різноманітності
        primary_drills = random.sample(pos_data["primary"], 2)
        secondary_drill = random.sample(pos_data["secondary"], 1)
        selected_drills = primary_drills + secondary_drill
        
        todays_warmup = random.choice(warmups)
        
        focus = f"Інтенсивний розвиток ({position})"
        content = (
            f"Організм повністю відновлений (Ризик: {risk_percent}%).\n"
            f"Час для інтенсивної роботи на майданчику:\n\n"
            f"1. {todays_warmup}\n"
            f"2. {selected_drills[0]}\n"
            f"3. {selected_drills[1]}\n"
            f"4. {selected_drills[2]}\n"
            f"5. Заминка (5 хв легкий біг + розтяжка)"
        )


    # Логіка збереження/оновлення
    if existing_plan:
        existing_plan.fatigue_risk = fatigue_status
        existing_plan.plan_focus = focus
        existing_plan.plan_content = content
        db.commit()
        db.refresh(existing_plan)
        return existing_plan
    else:
        new_plan = models.GeneratedPlan(
            user_id=user_id,
            date=today,
            fatigue_risk=fatigue_status,
            plan_focus=focus,
            plan_content=content
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return new_plan