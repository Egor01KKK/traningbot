from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
    computed_targets: Mapped["ComputedTargets"] = relationship(
        back_populates="user", uselist=False
    )
    daily_logs: Mapped[List["DailyLog"]] = relationship(back_populates="user")
    workouts: Mapped[List["Workout"]] = relationship(back_populates="user")
    strength_logs: Mapped[List["StrengthLog"]] = relationship(back_populates="user")
    calorie_entries: Mapped[List["CalorieEntry"]] = relationship(back_populates="user")
    settings: Mapped["Settings"] = relationship(back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    height_cm: Mapped[Optional[int]] = mapped_column(Integer)
    current_weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    activity_level: Mapped[Optional[str]] = mapped_column(String(20))
    goal: Mapped[Optional[str]] = mapped_column(String(20))
    goal_speed: Mapped[Optional[str]] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class ComputedTargets(Base):
    __tablename__ = "computed_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bmr: Mapped[Optional[int]] = mapped_column(Integer)
    tdee: Mapped[Optional[int]] = mapped_column(Integer)
    target_calories: Mapped[Optional[int]] = mapped_column(Integer)
    protein_g: Mapped[Optional[int]] = mapped_column(Integer)
    fat_g: Mapped[Optional[int]] = mapped_column(Integer)
    carbs_g: Mapped[Optional[int]] = mapped_column(Integer)
    deficit_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="computed_targets")


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_daily_logs_user_date"),
        Index("idx_daily_logs_user_date", "user_id", "log_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    calories_consumed: Mapped[Optional[int]] = mapped_column(Integer)
    water_ml: Mapped[Optional[int]] = mapped_column(Integer)
    sleep_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="daily_logs")


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (Index("idx_workouts_user_date", "user_id", "workout_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    workout_date: Mapped[date] = mapped_column(Date, nullable=False)
    workout_type: Mapped[Optional[str]] = mapped_column(String(20))
    duration_min: Mapped[Optional[int]] = mapped_column(Integer)
    calories_burned: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="workouts")


class StrengthLog(Base):
    __tablename__ = "strength_logs"
    __table_args__ = (
        Index("idx_strength_logs_user_exercise", "user_id", "exercise_name", "log_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    reps: Mapped[Optional[int]] = mapped_column(Integer)
    sets: Mapped[Optional[int]] = mapped_column(Integer)
    e1rm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="strength_logs")


class CalorieEntry(Base):
    __tablename__ = "calorie_entries"
    __table_args__ = (Index("idx_calorie_entries_user_date", "user_id", "entry_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="calorie_entries")


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Yerevan")
    weigh_day: Mapped[str] = mapped_column(String(10), default="sunday")
    weigh_time: Mapped[time] = mapped_column(Time, default=time(10, 0))
    daily_reminder_time: Mapped[time] = mapped_column(Time, default=time(21, 30))
    weekly_report_time: Mapped[time] = mapped_column(Time, default=time(19, 0))
    alert_weight_loss_pct: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("1.0")
    )
    alert_low_calories_pct: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("0.7")
    )
    use_ai_coach: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="settings")
