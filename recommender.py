# recommender.py — Rules-based meal recommender (safe, no crashes)
from database import get_db
from datetime import date, datetime


def get_today_meals(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM meals WHERE user_id=? AND date=?",
        (user_id, str(date.today()))
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user(user_id):
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(u) if u else None


def current_meal_type():
    h = datetime.now().hour
    if 5  <= h < 11: return "breakfast"
    if 11 <= h < 15: return "lunch"
    if 15 <= h < 18: return "snack"
    return "dinner"


def recommend(user_id):
    user = get_user(user_id)
    if not user:
        return None

    # Safe defaults — never crash on None
    calorie_goal = user.get("calorie_goal") or 2000
    goal         = (user.get("fitness_goal") or "").lower()
    preferences  = (user.get("preferences")  or "").lower()

    meals     = get_today_meals(user_id)
    consumed  = sum(m["calories"] for m in meals)
    remaining = max(0, calorie_goal - consumed)
    meal_type = current_meal_type()

    conn = get_db()
    foods = conn.execute(
        "SELECT * FROM foods WHERE meal_type=?", (meal_type,)
    ).fetchall()
    conn.close()
    foods = [dict(f) for f in foods]

    if not foods:
        return None

    # Filter by preferences
    prefs = [p.strip() for p in preferences.split(",") if p.strip()]

    def matches_pref(food):
        if not prefs:
            return True
        tags = (food.get("tags") or "").lower()
        if "vegan"        in prefs and "vegan"          not in tags: return False
        if "vegetarian"   in prefs and "non-vegetarian" in tags:     return False
        if "keto"         in prefs and "keto"           not in tags: return False
        return True

    candidates = [f for f in foods if matches_pref(f)] or foods

    # Exclude already-eaten today
    eaten_ids  = {m["food_id"] for m in meals}
    candidates = [f for f in candidates if f["id"] not in eaten_ids] or candidates

    # Score
    def score(f):
        s = 0
        ideal = remaining / 2 if meal_type == "dinner" else remaining / 3
        s -= abs(f["calories"] - ideal) * 0.5
        if "muscle" in goal:
            s += f["protein"] * 3
        elif "loss" in goal:
            s -= f["calories"] * 0.2
            s += f["protein"] * 1.5
        elif "keto" in goal:
            s += f["fats"] * 2 - f["carbs"] * 1.5
        else:
            s += f["protein"] * 1.2
        if remaining > 0 and f["calories"] > remaining:
            s -= 50
        return s

    best = max(candidates, key=score)

    reason_parts = []
    last = meals[-1] if meals else None
    if last and last.get("carbs", 0) > 50:
        reason_parts.append("your last meal was high in carbs")
    if "muscle" in goal:
        reason_parts.append("you're building muscle so we prioritised protein")
    elif "loss" in goal:
        reason_parts.append("you're cutting calories so we chose a lighter option")
    reason_parts.append(f"it fits your remaining {remaining} kcal budget")

    explanation = (
        f"We recommend {best['name']} ({best['calories']} kcal, "
        f"{best['protein']}g protein) because "
        + ", and ".join(reason_parts) + "."
    )

    return {
        "food":        best,
        "explanation": explanation,
        "meal_type":   meal_type,
        "remaining":   remaining,
        "consumed":    consumed
    }