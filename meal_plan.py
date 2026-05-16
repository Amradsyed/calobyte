# meal_plan.py — Generates a 7-day meal plan based on user profile
from database import get_db

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def calculate_water(weight, activity):
    """Calculate daily water intake in litres based on weight and activity."""
    base = weight * 0.033  # 33ml per kg
    if activity in ["active", "very active"]:
        base += 0.5
    elif activity == "moderately active":
        base += 0.3
    return round(base, 1)

def generate_meal_plan(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None

    user = dict(user)
    calorie_goal = user["calorie_goal"] or 2000
    preferences = user["preferences"] or ""
    weight = user["weight"] or 70
    activity = (user["activity"] or "sedentary").lower()

    # Calorie splits: breakfast 25%, lunch 35%, dinner 40%
    breakfast_cal = int(calorie_goal * 0.25)
    lunch_cal = int(calorie_goal * 0.35)
    dinner_cal = int(calorie_goal * 0.40)

    # Get foods from DB
    all_foods = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()

    all_foods = [dict(f) for f in all_foods]

    # Filter by preferences if available
    def filter_foods(meal_type, target_cal):
        candidates = [f for f in all_foods if f["meal_type"] == meal_type]
        if preferences:
            prefs = preferences.split(",")
            preferred = [f for f in candidates if any(p in (f["tags"] or "") for p in prefs)]
            if preferred:
                candidates = preferred
        # Sort by closest to target calories
        candidates.sort(key=lambda f: abs(f["calories"] - target_cal))
        return candidates

    breakfasts = filter_foods("breakfast", breakfast_cal)
    lunches = filter_foods("lunch", lunch_cal)
    dinners = filter_foods("dinner", dinner_cal)

    # Generate 7 days
    plan = []
    for i, day in enumerate(DAYS):
        b = breakfasts[(i * 2) % len(breakfasts)] if breakfasts else None
        l = lunches[(i * 3) % len(lunches)] if lunches else None
        d = dinners[(i * 4) % len(dinners)] if dinners else None

        total = sum(f["calories"] for f in [b, l, d] if f)
        plan.append({
            "day": day,
            "breakfast": b,
            "lunch": l,
            "dinner": d,
            "total_calories": total
        })

    water = user.get("water_goal_litres") or calculate_water(weight, activity)

    return {
        "plan": plan,
        "water_litres": water,
        "calorie_goal": calorie_goal
    }