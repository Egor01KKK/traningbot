"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=10), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("current_weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("activity_level", sa.String(length=20), nullable=True),
        sa.Column("goal", sa.String(length=20), nullable=True),
        sa.Column("goal_speed", sa.String(length=20), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "computed_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("bmr", sa.Integer(), nullable=True),
        sa.Column("tdee", sa.Integer(), nullable=True),
        sa.Column("target_calories", sa.Integer(), nullable=True),
        sa.Column("protein_g", sa.Integer(), nullable=True),
        sa.Column("fat_g", sa.Integer(), nullable=True),
        sa.Column("carbs_g", sa.Integer(), nullable=True),
        sa.Column("deficit_percent", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("calculated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("calories_consumed", sa.Integer(), nullable=True),
        sa.Column("water_ml", sa.Integer(), nullable=True),
        sa.Column("sleep_hours", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_daily_logs_user_date"),
    )
    op.create_index(
        "idx_daily_logs_user_date", "daily_logs", ["user_id", "log_date"]
    )

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("workout_date", sa.Date(), nullable=False),
        sa.Column("workout_type", sa.String(length=20), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("calories_burned", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workouts_user_date", "workouts", ["user_id", "workout_date"])

    op.create_table(
        "strength_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("exercise_name", sa.String(length=100), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("e1rm", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_strength_logs_user_exercise",
        "strength_logs",
        ["user_id", "exercise_name", "log_date"],
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("weigh_day", sa.String(length=10), nullable=True),
        sa.Column("weigh_time", sa.Time(), nullable=True),
        sa.Column("daily_reminder_time", sa.Time(), nullable=True),
        sa.Column("weekly_report_time", sa.Time(), nullable=True),
        sa.Column("alert_weight_loss_pct", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("alert_low_calories_pct", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("use_ai_coach", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_index("idx_strength_logs_user_exercise", table_name="strength_logs")
    op.drop_table("strength_logs")
    op.drop_index("idx_workouts_user_date", table_name="workouts")
    op.drop_table("workouts")
    op.drop_index("idx_daily_logs_user_date", table_name="daily_logs")
    op.drop_table("daily_logs")
    op.drop_table("computed_targets")
    op.drop_table("profiles")
    op.drop_table("users")
