# seed_foods.py — Loads foods.csv into the SQLite foods table
import pandas as pd
from database import get_db, init_db

def seed():
    init_db()
    df = pd.read_csv("foods.csv")
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM foods")  # clear existing
    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO foods (id, name, category, meal_type, calories, protein, carbs, fats, portion, tags)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            int(row["id"]), row["name"], row["category"], row["meal_type"],
            int(row["calories"]), float(row["protein"]), float(row["carbs"]),
            float(row["fats"]), row["portion"], row["tags"]
        ))
    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(df)} foods.")

if __name__ == "__main__":
    seed()