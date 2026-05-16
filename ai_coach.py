import os
import json
import urllib.request
import urllib.error
from pathlib import Path


def load_local_env():
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def get_ai_coach_advice(user, consumed, remaining, protein, carbs, fats, water, recommendation):
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        return {
            "summary": "AI coach is not connected yet.",
            "meal_tip": "Add your NVIDIA API key to the .env file.",
            "fitness_tip": "Once connected, you will get personalized fitness tips here.",
            "water_tip": "Your water advice will appear here."
        }

    recommended_food = "No food recommendation available"
    if recommendation and recommendation.get("food"):
        recommended_food = recommendation["food"]["name"]

    prompt = f"""
You are CaloByte's AI fitness and meal coach.
Do not give medical advice. Keep answers practical and short.

User profile:
Name: {user.get("name")}
Age: {user.get("age")}
Height: {user.get("height")} cm
Weight: {user.get("weight")} kg
Fitness goal: {user.get("fitness_goal")}
Food preferences: {user.get("preferences")}
Daily calorie goal: {user.get("calorie_goal")}
Daily water goal in litres: {user.get("water_goal_litres")}

Today's progress:
Calories consumed: {consumed}
Calories remaining: {remaining}
Protein: {protein}g
Carbs: {carbs}g
Fats: {fats}g
Water glasses logged: {water}
Recommended food from app: {recommended_food}

Return exactly this format:
Summary: ...
Meal Tip: ...
Fitness Tip: ...
Water Tip: ...
"""

    payload = {
        "model": "google/gemma-2-2b-it",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 300,
        "stream": False
    }

    request = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        text = data["choices"][0]["message"]["content"].strip()

        advice = {
            "summary": "",
            "meal_tip": "",
            "fitness_tip": "",
            "water_tip": ""
        }

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Summary:"):
                advice["summary"] = line.replace("Summary:", "").strip()
            elif line.startswith("Meal Tip:"):
                advice["meal_tip"] = line.replace("Meal Tip:", "").strip()
            elif line.startswith("Fitness Tip:"):
                advice["fitness_tip"] = line.replace("Fitness Tip:", "").strip()
            elif line.startswith("Water Tip:"):
                advice["water_tip"] = line.replace("Water Tip:", "").strip()

        if not advice["summary"]:
            advice["summary"] = text
        if not advice["meal_tip"]:
            advice["meal_tip"] = "Choose a meal that fits your remaining calories and protein needs."
        if not advice["fitness_tip"]:
            advice["fitness_tip"] = "Add light movement today based on your energy level."
        if not advice["water_tip"]:
            advice["water_tip"] = "Keep sipping water steadily toward your daily goal."

        return advice

    except urllib.error.HTTPError as e:
        print("AI Coach HTTP error:", e.code, e.read().decode("utf-8"))
    except Exception as e:
        print("AI Coach error:", repr(e))

    return {
        "summary": "AI coach could not load right now.",
        "meal_tip": "Check the terminal or PythonAnywhere error log for the AI Coach error message.",
        "fitness_tip": "Keep moving today, even a short walk helps.",
        "water_tip": "Stay consistent with your water goal."
    }
