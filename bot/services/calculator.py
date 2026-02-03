from dataclasses import dataclass
from decimal import Decimal

ACTIVITY_FACTORS = {
    "sedentary": Decimal("1.2"),
    "light": Decimal("1.375"),
    "moderate": Decimal("1.55"),
    "high": Decimal("1.725"),
    "very_high": Decimal("1.9"),
}

GOAL_MULTIPLIERS = {
    "recomp": Decimal("0.93"),
    "cut": Decimal("0.85"),
    "bulk": Decimal("1.10"),
}

SPEED_ADJUSTMENTS = {
    "gentle": Decimal("0.5"),
    "standard": Decimal("1.0"),
    "aggressive": Decimal("1.5"),
}


@dataclass
class NutritionTargets:
    bmr: int
    tdee: int
    target_calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    deficit_percent: Decimal


def calculate_bmr(
    gender: str,
    weight_kg: Decimal,
    height_cm: int,
    age: int,
) -> int:
    """
    Calculate BMR using Mifflin-St Jeor formula.

    Men: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age + 5
    Women: BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age - 161
    """
    base = Decimal("10") * weight_kg + Decimal("6.25") * height_cm - 5 * age

    if gender == "male":
        bmr = base + 5
    else:
        bmr = base - 161

    return int(bmr)


def calculate_tdee(bmr: int, activity_level: str) -> int:
    """Calculate Total Daily Energy Expenditure."""
    factor = ACTIVITY_FACTORS.get(activity_level, Decimal("1.2"))
    return int(bmr * factor)


def calculate_targets(
    gender: str,
    weight_kg: Decimal,
    height_cm: int,
    age: int,
    activity_level: str,
    goal: str,
    goal_speed: str = "standard",
) -> NutritionTargets:
    """Calculate complete nutrition targets."""
    bmr = calculate_bmr(gender, weight_kg, height_cm, age)
    tdee = calculate_tdee(bmr, activity_level)

    goal_multiplier = GOAL_MULTIPLIERS.get(goal, Decimal("1.0"))
    speed_adjustment = SPEED_ADJUSTMENTS.get(goal_speed, Decimal("1.0"))

    if goal in ("recomp", "cut"):
        base_deficit = Decimal("1.0") - goal_multiplier
        adjusted_deficit = base_deficit * speed_adjustment
        effective_multiplier = Decimal("1.0") - adjusted_deficit
    else:
        base_surplus = goal_multiplier - Decimal("1.0")
        adjusted_surplus = base_surplus * speed_adjustment
        effective_multiplier = Decimal("1.0") + adjusted_surplus

    target_calories = int(tdee * effective_multiplier)
    deficit_percent = (Decimal("1.0") - effective_multiplier) * 100

    protein_g = int(Decimal("2.0") * weight_kg)
    fat_g = int(Decimal("0.9") * weight_kg)

    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9
    remaining_kcal = target_calories - protein_kcal - fat_kcal
    carbs_g = max(0, remaining_kcal // 4)

    return NutritionTargets(
        bmr=bmr,
        tdee=tdee,
        target_calories=target_calories,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        deficit_percent=deficit_percent,
    )


def calculate_e1rm(weight_kg: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1 Rep Max using Epley formula.

    e1RM = weight × (1 + reps / 30)
    """
    if reps == 1:
        return weight_kg
    return weight_kg * (Decimal("1") + Decimal(reps) / Decimal("30"))
