# database.py — Sets up SQLite database and helper functions
import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "calobyte.db"

def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            height REAL,
            weight REAL,
            gender TEXT,
            activity TEXT,
            calorie_goal INTEGER,
            fitness_goal TEXT,
            preferences TEXT
        )
    """)

    # Foods table
    c.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            meal_type TEXT,
            calories INTEGER,
            protein REAL,
            carbs REAL,
            fats REAL,
            portion TEXT,
            tags TEXT
        )
    """)

    # Meals eaten by users
    c.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_id INTEGER,
            meal_type TEXT,
            calories INTEGER,
            protein REAL,
            carbs REAL,
            fats REAL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Water tracker
    c.execute("""
        CREATE TABLE IF NOT EXISTS water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            glasses INTEGER DEFAULT 0,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized.")