from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

# Таблиця 1: Профіль гравця
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String, index=True)
    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    position = Column(String)  # Ігрове амплуа (PG, SG, SF, PF, C)

    # Вказуються зв'язки (один гравець має багато метрик, кросівок і планів)
    metrics = relationship("DailyMetric", back_populates="owner", lazy="selectin", cascade="all, delete-orphan")
    shoes = relationship("ShoeInventory", back_populates="owner", lazy="selectin", cascade="all, delete-orphan")
    plans = relationship("GeneratedPlan", back_populates="owner", lazy="selectin", cascade="all, delete-orphan")

# Таблиця 2: Щоденні метрики (навантаження)
class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    metric_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    
    shoe_id = Column(Integer, ForeignKey("shoes_inventory.shoe_id", ondelete="SET NULL"), nullable=True)

    date = Column(Date)
    duration_minutes = Column(Integer)
    activity_type = Column(String)
    rpe_score = Column(Integer)
    hrv_value = Column(Float)
    sleep_hours = Column(Float)

    owner = relationship("User", back_populates="metrics")
    shoe = relationship("ShoeInventory", back_populates="metrics")


# Таблиця 3: Моніторинг кросівок (наша фішка)
class ShoeInventory(Base):
    __tablename__ = "shoes_inventory"

    shoe_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    brand_model = Column(String)
    cushion_type = Column(String)
    current_hours_played = Column(Float, default=0.0)
    max_lifespan_hours = Column(Float)

    owner = relationship("User", back_populates="shoes")
    metrics = relationship("DailyMetric", back_populates="shoe")

# Таблиця 4: Згенеровані ШІ тренувальні плани
class GeneratedPlan(Base):
    __tablename__ = "generated_plans"

    plan_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    
    date = Column(Date)
    fatigue_risk = Column(String)
    plan_focus = Column(String)
    plan_content = Column(String)

    owner = relationship("User", back_populates="plans")