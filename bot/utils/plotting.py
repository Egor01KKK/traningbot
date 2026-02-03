import io
from datetime import date
from decimal import Decimal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from bot.services.analytics import WeightTrend, ExerciseProgress


def create_weight_chart(trend: WeightTrend) -> bytes:
    """Create weight trend chart as PNG bytes."""
    fig, ax = plt.subplots(figsize=(10, 5))

    dates = [d for d in trend.dates]
    weights = [float(w) for w in trend.weights]
    moving_avg = [float(w) for w in trend.moving_avg]

    ax.plot(dates, weights, "o-", color="#4CAF50", label="Вес", alpha=0.7, markersize=6)
    ax.plot(dates, moving_avg, "-", color="#2196F3", label="Скользящее среднее (7 дней)", linewidth=2)

    ax.set_xlabel("Дата", fontsize=10)
    ax.set_ylabel("Вес (кг)", fontsize=10)
    ax.set_title("Динамика веса", fontsize=12, fontweight="bold")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    if weights:
        y_min = min(weights) - 1
        y_max = max(weights) + 1
        ax.set_ylim(y_min, y_max)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_exercise_progress_chart(progress: ExerciseProgress) -> bytes:
    """Create exercise progress chart as PNG bytes."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    dates = [d for d in progress.dates]
    weights = [float(w) for w in progress.weights]
    e1rms = [float(e) for e in progress.e1rms]

    ax1.plot(dates, weights, "o-", color="#FF5722", label="Рабочий вес", linewidth=2, markersize=8)
    ax1.set_ylabel("Вес (кг)", fontsize=10)
    ax1.set_title(f"Прогресс: {progress.exercise_name}", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2.plot(dates, e1rms, "s-", color="#9C27B0", label="e1RM", linewidth=2, markersize=8)
    ax2.set_xlabel("Дата", fontsize=10)
    ax2.set_ylabel("e1RM (кг)", fontsize=10)
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()
