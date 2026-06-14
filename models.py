from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON, Text, Index
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

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, name='{self.name}', position='{self.position}')>"

# Таблиця 2: Щоденні метрики (навантаження)
class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    __table_args__ = (
        # Складений індекс для найпоширенішого запиту (фільтрація по юзеру та даті)
        Index('ix_daily_metrics_user_date', 'user_id', 'date'),
    )

    metric_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    shoe_id = Column(Integer, ForeignKey("shoes_inventory.shoe_id", ondelete="SET NULL"), nullable=True)

    date = Column(Date, nullable=False)
    duration_minutes = Column(Integer)
    activity_type = Column(String)
    rpe_score = Column(Integer)
    hrv_value = Column(Float)
    sleep_hours = Column(Float)

    owner = relationship("User", back_populates="metrics")
    shoe = relationship("ShoeInventory", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<DailyMetric(metric_id={self.metric_id}, date={self.date}, type='{self.activity_type}')>"

# Таблиця 3: Моніторинг кросівок
class ShoeInventory(Base):
    __tablename__ = "shoes_inventory"

    shoe_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    brand_model = Column(String)
    cushion_type = Column(String)
    current_hours_played = Column(Float, default=0.0)
    max_lifespan_hours = Column(Float)

    owner = relationship("User", back_populates="shoes")
    metrics = relationship("DailyMetric", back_populates="shoe")

    def __repr__(self) -> str:
        return f"<ShoeInventory(shoe_id={self.shoe_id}, model='{self.brand_model}', wear={self.current_hours_played}/{self.max_lifespan_hours})>"

# Таблиця 4: Згенеровані ШІ тренувальні плани
class GeneratedPlan(Base):
    __tablename__ = "generated_plans"
    __table_args__ = (
        Index('ix_generated_plans_user_date', 'user_id', 'date'),
    )

    plan_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    date = Column(Date, nullable=False)
    fatigue_risk = Column(String)
    plan_focus = Column(String)
    plan_content = Column(Text, nullable=False) 

    owner = relationship("User", back_populates="plans")

    def __repr__(self) -> str:
        return f"<GeneratedPlan(plan_id={self.plan_id}, date={self.date}, risk='{self.fatigue_risk}')>"