# recommender.py — Beginner-friendly rules-based AI recommender
from database import get_db
from datetime import date

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
    """Decide if it's breakfast, lunch, dinner or snack based on time."""
    from datetime import datetime
    h = datetime.now().hour
    if 5 <= h < 11:  return "breakfast"
    if 11 <= h < 15: return "lunch"
    if 15 <= h < 18: return "snack"
    return "dinner"

def recommend(user_id):
    """Main AI recommendation function."""
    user = get_user(user_id)
    if not user:
        return None

    meals = get_today_meals(user_id)
    consumed = sum(m["calories"] for m in meals)
    remaining = max(0, user["calorie_goal"] - consumed)
    meal_type = current_meal_type()

    # Get foods for this meal type
    conn = get_db()
    foods = conn.execute(
        "SELECT * FROM foods WHERE meal_type=?", (meal_type,)
    ).fetchall()
    conn.close()
    foods = [dict(f) for f in foods]

    # Filter by user preferences (tags)
    prefs = (user["preferences"] or "").lower().split(",")
    prefs = [p.strip() for p in prefs if p.strip()]

    def matches_pref(food):
        if not prefs: return True
        tags = food["tags"].lower()
        # If user is vegan, exclude non-vegan
        if "vegan" in prefs and "vegan" not in tags: return False
        if "vegetarian" in prefs and "non-vegetarian" in tags: return False
        if "keto" in prefs and "keto" not in tags and "keto-friendly" not in tags:
            return False
        return True

    candidates = [f for f in foods if matches_pref(f)]
    if not candidates:
        candidates = foods  # fallback

    # Avoid repeating foods eaten today
    eaten_ids = {m["food_id"] for m in meals}
    candidates = [f for f in candidates if f["id"] not in eaten_ids] or candidates

    # Score each candidate
    goal = (user["fitness_goal"] or "").lower()

    def score(f):
        s = 0
        # Closer to ideal calorie share (e.g. 1/3 of remaining)
        ideal = remaining / 2 if meal_type == "dinner" else remaining / 3
        s -= abs(f["calories"] - ideal) * 0.5

        # Fitness goal weighting
        if "muscle" in goal:
            s += f["protein"] * 3
        elif "loss" in goal:
            s -= f["calories"] * 0.2
            s += f["protein"] * 1.5
        elif "keto" in goal:
            s += f["fats"] * 2 - f["carbs"] * 1.5
        else:
            s += f["protein"] * 1.2

        # Penalize if remaining calories are low
        if f["calories"] > remaining and remaining > 0:
            s -= 50
        return s

    best = max(candidates, key=score)

    # Build explanation
    last = meals[-1] if meals else None
    reason_parts = []
    if last and last["carbs"] > 50:
        reason_parts.append("your last meal was high in carbs")
    if "muscle" in goal:
        reason_parts.append("you’re building muscle, so we prioritized protein")
    elif "loss" in goal:
        reason_parts.append("you’re cutting calories, so we picked a lighter, protein-rich option")
    reason_parts.append(f"this fits within your remaining {remaining} kcal budget")

    explanation = (
        f"We recommend **{best['name']}** ({best['calories']} kcal, "
        f"{best['protein']}g protein) because "
        + ", and ".join(reason_parts) + "."
    )

    return {
        "food": best,
        "explanation": explanation,
        "meal_type": meal_type,
        "remaining": remaining,
        "consumed": consumed
    }