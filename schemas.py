from pydantic import BaseModel, Field
from typing import Optional, List
import datetime as dt

# Базова схема користувача (без пароля)
class UserBase(BaseModel):
    email: str = Field(..., example="player@gmail.com")
    name: str = Field(..., example="Dmytro")
    age: int = Field(..., gt=0, example=21)
    height_cm: float = Field(..., gt=100, example=188)
    weight_kg: float = Field(..., gt=30, example=80.0)
    position: str = Field(..., description="Ігрове амплуа: PG, SG, SF, PF або C", example="PG")

# Схема для реєстрації (додається пароль)
class UserCreate(UserBase):
    password: str = Field(..., example="securepassword123")

# Схема для авторизації
class UserLogin(BaseModel):
    email: str
    password: str
    
class CalibrationDay(BaseModel):
    date: dt.date = Field(..., description="Дата тренування/відпочинку")
    activity_type: str = Field(..., description="Тип активності: Training, Game або Recovery")
    duration_minutes: int = Field(0, description="Тривалість у хвилинах")
    rpe_score: int = Field(0, description="Інтенсивність RPE (1-10)")
    sleep_hours: float = Field(..., description="Сон цієї ночі")
    
# Схема для оновлення даних
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Dmytro")
    age: Optional[int] = Field(None, gt=0, example=21)
    height_cm: Optional[float] = Field(None, gt=100, example=188.0)
    weight_kg: Optional[float] = Field(None, gt=30, example=85.0)
    position: Optional[str] = Field(None, description="PG, SG, SF, PF, C", example="SG")

# Схеми для налаштувань
class PasswordChange(BaseModel):
    old_password: str = Field(..., description="Поточний пароль")
    new_password: str = Field(..., description="Новий пароль")

class EmailChange(BaseModel):
    new_email: str = Field(..., description="Нова електронна адреса")

# Схема для того, що сервер віддасть назад (додасться ID, АЛЕ БЕЗ ПАРОЛЯ)
class UserResponse(UserBase):
    user_id: int

    class Config:
        from_attributes = True

# Схеми для кросівок
class ShoeCreate(BaseModel):
    brand_model: str = Field(..., example="Nike KD 17")
    shoe_type: str = Field(..., description="Баскетбольні або Інші")
    surface_type: str = Field(..., description="Паркет, Гума/Тартан або Асфальт")
    initial_wear_percentage: int = Field(0, ge=0, le=100, description="Відсоток зносу на момент додавання")

class ShoeResponse(BaseModel):
    shoe_id: int
    user_id: int
    brand_model: str
    cushion_type: str
    current_hours_played: float
    max_lifespan_hours: float

    class Config:
        from_attributes = True  

# Схеми щоденних метрик(тренувань)
class MetricCreate(BaseModel):
    date: dt.date = Field(..., description="Дата тренування")
    sleep_hours: float = Field(..., ge=0, le=24, description="Години сну")
    duration_minutes: int = Field(..., ge=0, description="Тривалість тренування (хвилини)")
    rpe_score: int = Field(..., ge=0, le=10, description="Оцінка RPE (1-10)")
    activity_type: str = Field(..., description="Тип активності")
    shoe_id: Optional[int] = Field(None, description="ID кросівок, якщо використовувались")

class MetricResponse(MetricCreate):
    metric_id: int
    user_id: int

    class Config:
        from_attributes = True

# Схеми для згенерованих планів
class PlanResponse(BaseModel):
    plan_id: int
    date: dt.date
    fatigue_risk: str
    plan_focus: str
    plan_content: str

    class Config:
        from_attributes = True             

# Комплексна схема(має завжди бути знизу коду)
class UserWithDetails(UserBase):
    user_id: int
    metrics: List['MetricResponse'] = []
    shoes: List['ShoeResponse'] = []
    plans: List['PlanResponse'] = []
    
    readiness_score: int = 100
    acwr_ratio: str = "0.00"
    acwr_status: str = "Немає даних"
    days_in_system: int = 0

    class Config:
        from_attributes = True