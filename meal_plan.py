# meal_plan.py — AI-powered 7-day meal plan via NVIDIA Kimi K2
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from database import get_db

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_local_env():
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()

load_local_env()


def calculate_water(weight, activity):
    base = (weight or 70) * 0.033
    if activity in ["active", "very active"]:
        base += 0.5
    elif activity in ["moderate", "moderately active"]:
        base += 0.3
    return round(base, 1)


def _fallback_plan(user, all_foods):
    """Rules-based fallback if AI is unavailable."""
    calorie_goal = user["calorie_goal"] or 2000
    preferences  = user["preferences"] or ""
    weight       = user["weight"] or 70
    activity     = (user["activity"] or "sedentary").lower()

    breakfast_cal = int(calorie_goal * 0.25)
    lunch_cal     = int(calorie_goal * 0.35)
    dinner_cal    = int(calorie_goal * 0.40)

    def filter_foods(meal_type, target_cal):
        candidates = [f for f in all_foods if f["meal_type"] == meal_type]
        if preferences:
            prefs = [p.strip() for p in preferences.split(",")]
            preferred = [f for f in candidates if any(p in (f["tags"] or "") for p in prefs)]
            if preferred:
                candidates = preferred
        candidates.sort(key=lambda f: abs(f["calories"] - target_cal))
        return candidates

    breakfasts = filter_foods("breakfast", breakfast_cal)
    lunches    = filter_foods("lunch",     lunch_cal)
    dinners    = filter_foods("dinner",    dinner_cal)

    plan = []
    for i, day in enumerate(DAYS):
        b = breakfasts[(i * 2) % len(breakfasts)] if breakfasts else None
        l = lunches  [(i * 3) % len(lunches)]     if lunches    else None
        d = dinners  [(i * 4) % len(dinners)]     if dinners    else None
        total = sum(f["calories"] for f in [b, l, d] if f)
        plan.append({"day": day, "breakfast": b, "lunch": l, "dinner": d, "total_calories": total})

    water = user.get("water_goal_litres") or calculate_water(weight, activity)
    return {"plan": plan, "water_litres": water, "calorie_goal": calorie_goal, "ai_generated": False}


def _build_ai_plan(user, all_foods, api_key):
    """Call Kimi K2 to generate a 7-day meal plan from the foods DB."""
    calorie_goal = user["calorie_goal"] or 2000
    water        = user.get("water_goal_litres") or calculate_water(user.get("weight", 70), user.get("activity", "sedentary"))

    # Give the AI the food catalogue so it picks real items from the DB
    food_catalogue = []
    for f in all_foods:
        food_catalogue.append({
            "id":        f["id"],
            "name":      f["name"],
            "meal_type": f["meal_type"],
            "calories":  f["calories"],
            "protein":   f["protein"],
            "carbs":     f["carbs"],
            "fats":      f["fats"],
            "portion":   f["portion"],
            "tags":      f["tags"]
        })

    prompt = f"""You are CaloByte's AI nutrition engine powered by Kimi K2.

USER PROFILE:
- Name: {user.get('name')}
- Age: {user.get('age')}, Gender: {user.get('gender')}
- Height: {user.get('height')} cm, Weight: {user.get('weight')} kg
- Activity level: {user.get('activity')}
- Fitness goal: {user.get('fitness_goal')}
- Food preferences: {user.get('preferences')}
- Daily calorie goal: {calorie_goal} kcal
- Daily water goal: {water} litres

FOOD CATALOGUE (you MUST only use items from this list by their exact id):
{json.dumps(food_catalogue, indent=2)}

TASK:
Create a 7-day meal plan (Monday through Sunday).
Each day must have exactly: breakfast, lunch, dinner.
Pick items from the catalogue that best match the user's calorie goal and fitness goal.
Breakfast ≈ {int(calorie_goal*0.25)} kcal, Lunch ≈ {int(calorie_goal*0.35)} kcal, Dinner ≈ {int(calorie_goal*0.40)} kcal.
Respect food preferences. Vary meals across days — do not repeat the same meal on consecutive days.

Return ONLY valid JSON, no markdown, no explanation. Exactly this structure:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast_id": <food id integer>,
      "lunch_id": <food id integer>,
      "dinner_id": <food id integer>,
      "ai_note": "<one sentence explaining why this day suits the user>"
    }},
    ... (all 7 days)
  ]
}}"""

    payload = {
        "model": "moonshotai/kimi-k2.6",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 2000,
        "stream": False
    }

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8"))

    raw = data["choices"][0]["message"]["content"].strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    ai_response = json.loads(raw)

    # Build a lookup map for foods
    food_map = {f["id"]: f for f in all_foods}

    plan = []
    for day_data in ai_response["days"]:
        b = food_map.get(day_data.get("breakfast_id"))
        l = food_map.get(day_data.get("lunch_id"))
        d = food_map.get(day_data.get("dinner_id"))
        total = sum(f["calories"] for f in [b, l, d] if f)
        plan.append({
            "day":            day_data["day"],
            "breakfast":      b,
            "lunch":          l,
            "dinner":         d,
            "total_calories": total,
            "ai_note":        day_data.get("ai_note", "")
        })

    return {
        "plan":          plan,
        "water_litres":  water,
        "calorie_goal":  calorie_goal,
        "ai_generated":  True,
        "ai_model": "Kimi K2.6 (moonshotai/kimi-k2.6)"
    }


def generate_meal_plan(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return None
    user = dict(user)

    all_foods = [dict(f) for f in conn.execute("SELECT * FROM foods").fetchall()]
    conn.close()

    api_key = os.getenv("NVIDIA_API_KEY")

    if api_key and all_foods:
        try:
            print(f"[CaloByte] Calling Kimi K2 to generate meal plan for {user.get('name')}...")
            result = _build_ai_plan(user, all_foods, api_key)
            print(f"[CaloByte] ✅ Kimi K2 meal plan generated successfully.")
            return result
        except Exception as e:
            print(f"[CaloByte] ⚠️  Kimi K2 failed ({e}), falling back to rules-based plan.")

    return _fallback_plan(user, all_foods)