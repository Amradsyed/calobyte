import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


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

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    prompt = f"""
You are CaloByte's AI fitness and meal coach.

Use the user's profile and today's progress to give practical food, fitness, and hydration advice.

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

Return exactly this format. Keep each line short:

Summary: ...
Meal Tip: ...
Fitness Tip: ...
Water Tip: ...
"""

    try:
        completion = client.chat.completions.create(
            model="google/gemma-2-2b-it",
            messages=[
                {
                    "role": "user",
                    "content": "You are a concise nutrition and fitness coach. Do not give medical advice. Keep answers practical and short."
                }, 
            ],
            temperature=0.2,
            top_p=0.7,
            max_tokens=300
        )

        text = completion.choices[0].message.content.strip()

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

    except Exception as e:
        print("AI Coach error:", repr(e))
        return {
            "summary": "AI coach could not load right now.",
            "meal_tip": "Check the terminal for the AI Coach error message.",
            "fitness_tip": "Keep moving today, even a short walk helps.",
            "water_tip": "Stay consistent with your water goal."
        }
