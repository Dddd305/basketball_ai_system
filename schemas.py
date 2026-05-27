from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
import datetime as dt
from enum import Enum

# ==========================================
# ДОМЕННІ ПЕРЕЛІКИ (ENUMS) ДЛЯ ВАЛІДАЦІЇ
# ==========================================
class CourtPosition(str, Enum):
    """Баскетбольні ігрові позиції за стандартною класифікацією."""
    PG = "PG"
    SG = "SG"
    SF = "SF"
    PF = "PF"
    C = "C"

class ActivityCategory(str, Enum):
    """Категорії щоденних фізичних активностей."""
    TRAINING = "Training"
    GAME = "Game"
    RECOVERY = "Recovery"

# ==========================================
# СХЕМИ КОРИСТУВАЧА
# ==========================================
class UserBase(BaseModel):
    email: str = Field(..., example="player@gmail.com")
    name: str = Field(..., example="Dmytro")
    age: int = Field(..., gt=0, example=21)
    height_cm: float = Field(..., gt=100, example=188)
    weight_kg: float = Field(..., gt=30, example=80.0)
    position: CourtPosition = Field(..., description="Ігрове амплуа: PG, SG, SF, PF або C", example="PG")

class UserCreate(UserBase):
    password: str = Field(..., example="securepassword123")

class UserLogin(BaseModel):
    email: str
    password: str
    
class CalibrationDay(BaseModel):
    date: dt.date = Field(..., description="Дата тренування/відпочинку")
    activity_type: ActivityCategory = Field(..., description="Тип активності: Training, Game або Recovery")
    duration_minutes: int = Field(0, ge=0, description="Тривалість у хвилинах")
    rpe_score: int = Field(0, ge=0, le=10, description="Інтенсивність RPE (1-10)")
    sleep_hours: float = Field(..., ge=0, le=24, description="Сон цієї ночі")
    
    @model_validator(mode='after')
    def validate_recovery_consistency(self) -> 'CalibrationDay':
        """Гарантує нульове навантаження для відновлювальних сесій."""
        if self.activity_type == ActivityCategory.RECOVERY:
            if self.duration_minutes > 0 or self.rpe_score > 0:
                raise ValueError("Сесія типу 'Recovery' повинна мати duration_minutes=0 та rpe_score=0.")
        return self

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Dmytro")
    age: Optional[int] = Field(None, gt=0, example=21)
    height_cm: Optional[float] = Field(None, gt=100, example=188.0)
    weight_kg: Optional[float] = Field(None, gt=30, example=85.0)
    position: Optional[CourtPosition] = Field(None, description="PG, SG, SF, PF, C", example="SG")

class PasswordChange(BaseModel):
    old_password: str = Field(..., description="Поточний пароль")
    new_password: str = Field(..., description="Новий пароль")

class EmailChange(BaseModel):
    new_email: str = Field(..., description="Нова електронна адреса")

class UserResponse(UserBase):
    user_id: int

    class Config:
        from_attributes = True

# ==========================================
# СХЕМИ ІНВЕНТАРЮ (КРОСІВКИ)
# ==========================================
class ShoeCreate(BaseModel):
    brand_model: str = Field(..., example="Nike KD 17")
    shoe_type: Literal["Баскетбольні", "Інші"] = Field(
        ..., description="Баскетбольні або Інші"
    )
    surface_type: Literal["Паркет", "Гума/Тартан", "Гібрид (Мікс)", "Асфальт"] = Field(
        ..., description="Паркет, Гума/Тартан або Асфальт"
    )
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

# ==========================================
# СХЕМИ МЕТРИК (ТРЕНУВАННЯ)
# ==========================================
class MetricCreate(BaseModel):
    date: dt.date = Field(..., description="Дата тренування")
    sleep_hours: float = Field(..., ge=0, le=24, description="Години сну")
    duration_minutes: int = Field(..., ge=0, description="Тривалість тренування (хвилини)")
    rpe_score: int = Field(..., ge=0, le=10, description="Оцінка RPE (1-10)")
    activity_type: ActivityCategory = Field(..., description="Тип активності")
    shoe_id: Optional[int] = Field(None, description="ID кросівок, якщо використовувались")
    hrv_value: Optional[float] = Field(
        None, 
        ge=1.0, 
        le=300.0, 
        description="Варіабельність серцевого ритму rMSSD (1-300 мс)"
    )

    @model_validator(mode='after')
    def validate_recovery_consistency(self) -> 'MetricCreate':
        """Гарантує нульове навантаження для відновлювальних сесій."""
        if self.activity_type == ActivityCategory.RECOVERY:
            if self.duration_minutes > 0 or self.rpe_score > 0:
                raise ValueError("Сесія типу 'Recovery' повинна мати duration_minutes=0 та rpe_score=0.")
        return self

class MetricResponse(MetricCreate):
    metric_id: int
    user_id: int

    class Config:
        from_attributes = True

# ==========================================
# СХЕМИ ШІ-ПЛАНІВ
# ==========================================
class PlanResponse(BaseModel):
    plan_id: int
    date: dt.date
    fatigue_risk: str
    plan_focus: str
    plan_content: str

    class Config:
        from_attributes = True                     

# ==========================================
# КОМПЛЕКСНА СХЕМА (DASHBOARD)
# ==========================================
class UserWithDetails(UserBase):
    user_id: int
    metrics: List[MetricResponse] = []
    shoes: List[ShoeResponse] = []
    plans: List[PlanResponse] = []
    
    # Розрахункові поля, які додає бекенд
    readiness_score: int = 100
    fatigue_risk: str = "Калібрування"
    acwr_ratio: str = "0.00"
    acwr_status: str = "Немає даних"
    days_in_system: int = 0

    class Config:
        from_attributes = True