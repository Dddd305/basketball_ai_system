from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
import datetime as dt

# === БАЗОВІ ТИПИ (СУВОРІ) ===
CourtPosition = Literal["PG", "SG", "SF", "PF", "C"]
ActivityCategory = Literal["Training", "Game", "Recovery"]

# === ПРОФІЛЬ ГРАВЦЯ ===
class UserBase(BaseModel):
    email: str
    name: str
    age: int
    height_cm: float
    weight_kg: float
    position: str

class UserCreate(BaseModel):
    email: str = Field(..., example="player@gmail.com")
    name: str = Field(..., example="Dmytro")
    age: int = Field(..., gt=0)
    height_cm: float = Field(..., gt=100)
    weight_kg: float = Field(..., gt=30)
    position: CourtPosition
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=100)
    weight_kg: Optional[float] = Field(None, gt=30)
    position: Optional[CourtPosition] = None

class UserResponse(UserBase):
    user_id: int
    class Config: from_attributes = True
        
class UserLogin(BaseModel):
    email: str
    password: str
        
class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class EmailChange(BaseModel):
    new_email: str

# === ІНВЕНТАР ===
class ShoeCreate(BaseModel):
    brand_model: str
    shoe_type: Literal["Баскетбольні", "Інші"]
    surface_type: Literal["Паркет", "Гума/Тартан", "Гібрид (Мікс)", "Асфальт"]
    initial_wear_percentage: int = Field(0, ge=0, le=100)

class ShoeResponse(BaseModel):
    shoe_id: int
    user_id: int
    brand_model: str
    cushion_type: str
    current_hours_played: float
    max_lifespan_hours: float
    class Config: from_attributes = True  

# === МЕТРИКИ ТА КАЛІБРУВАННЯ ===
class CalibrationDay(BaseModel):
    date: dt.date
    activity_type: ActivityCategory
    duration_minutes: int = Field(0, ge=0)
    rpe_score: int = Field(0, ge=0, le=10)
    sleep_hours: float = Field(..., ge=0, le=24)
    
    @model_validator(mode='after')
    def validate_recovery(self) -> 'CalibrationDay':
        if self.activity_type == "Recovery":
            self.duration_minutes = 0
            self.rpe_score = 0
        return self

class MetricCreate(BaseModel):
    date: dt.date
    sleep_hours: float = Field(..., ge=0, le=24)
    duration_minutes: int = Field(..., ge=0)
    rpe_score: int = Field(..., ge=0, le=10)
    activity_type: ActivityCategory
    shoe_id: Optional[int] = None
    hrv_value: Optional[float] = Field(None, ge=0.0)

    @model_validator(mode='after')
    def validate_recovery(self) -> 'MetricCreate':
        if self.activity_type == "Recovery":
            self.duration_minutes = 0
            self.rpe_score = 0
            self.shoe_id = None
        return self

class MetricResponse(BaseModel):
    metric_id: int
    user_id: int
    date: dt.date
    sleep_hours: float
    duration_minutes: int
    rpe_score: int
    activity_type: str 
    shoe_id: Optional[int]
    hrv_value: Optional[float]
    class Config: from_attributes = True

# === ШІ ПЛАНИ ===
class PlanResponse(BaseModel):
    plan_id: int
    date: dt.date
    fatigue_risk: str
    plan_focus: str
    plan_content: str
    class Config: from_attributes = True                     

# === DASHBOARD (КОМПЛЕКСНА СХЕМА) ===
class UserWithDetails(UserResponse):
    metrics: List[MetricResponse] = []
    shoes: List[ShoeResponse] = []
    plans: List[PlanResponse] = []
    
    readiness_score: int = 100
    fatigue_risk: str = "Калібрування"
    acwr_ratio: str = "0.00"
    acwr_status: str = "Немає даних"
    days_in_system: int = 0
    class Config: from_attributes = True