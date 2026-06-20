# app.py — CaloByte Main Flask App
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from database import init_db, get_db
from recommender import recommend, get_today_meals
from ai_coach import get_ai_coach_advice
from meal_plan import generate_meal_plan

app = Flask(__name__)
app.secret_key = "calobyte-secret-2025"

init_db()

# ---------- Helpers ----------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(u) if u else None

def profile_complete(user):
    """Check if user has filled in their profile after signup."""
    if not user:
        return False
    return bool(user.get("name") and user.get("calorie_goal") and user.get("water_goal_litres"))

@app.context_processor
def inject_user():
    return {"user": current_user()}


# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = generate_password_hash(request.form["password"])
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (email, password) VALUES (?,?)", (email, password))
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            session["user_id"] = user["id"]
            conn.close()
            flash("Account created! Please complete your profile.", "success")
            return redirect(url_for("onboarding"))
        except Exception:
            flash("That email is already registered. Please log in.", "error")
            conn.close()
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        u = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if u and check_password_hash(u["password"], password):
            session["user_id"] = u["id"]
            user = dict(u)
            # Always send to onboarding if profile not complete
            if not profile_complete(user):
                flash("Please complete your profile first.", "success")
                return redirect(url_for("onboarding"))
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        prefs = ",".join(request.form.getlist("preferences"))
        conn = get_db()
        conn.execute("""
            UPDATE users SET name=?, age=?, height=?, weight=?, gender=?,
            activity=?, calorie_goal=?, water_goal_litres=?, fitness_goal=?, preferences=?
            WHERE id=?
        """, (
            request.form["name"],
            int(request.form["age"]),
            float(request.form["height"]),
            float(request.form["weight"]),
            request.form["gender"],
            request.form["activity"],
            int(request.form["calorie_goal"]),
            float(request.form["water_goal_litres"]),
            request.form["fitness_goal"],
            prefs,
            session["user_id"]
        ))
        conn.commit()
        conn.close()
        flash("Profile saved! Your AI meal plan is being generated.", "success")
        return redirect(url_for("meal_plan"))
    user = current_user()
    return render_template("onboarding.html", user=user)

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    # Guard: send to onboarding if profile incomplete
    if not profile_complete(user):
        flash("Please complete your profile to access the dashboard.", "success")
        return redirect(url_for("onboarding"))

    meals = get_today_meals(user["id"])
    consumed = sum(m["calories"] for m in meals)
    protein  = sum(m["protein"]  for m in meals)
    carbs    = sum(m["carbs"]    for m in meals)
    fats     = sum(m["fats"]     for m in meals)
    calorie_goal = user["calorie_goal"] or 2000
    remaining = max(0, calorie_goal - consumed)

    conn = get_db()
    w = conn.execute(
        "SELECT * FROM water WHERE user_id=? AND date=?",
        (user["id"], str(date.today()))
    ).fetchone()
    glasses = w["glasses"] if w else 0

    meal_rows = []
    for m in meals:
        f = conn.execute("SELECT name FROM foods WHERE id=?", (m["food_id"],)).fetchone()
        meal_rows.append({**m, "name": f["name"] if f else "Custom"})
    conn.close()

    rec = recommend(user["id"])

    ai_coach = get_ai_coach_advice(
        user=user, consumed=consumed, remaining=remaining,
        protein=protein, carbs=carbs, fats=fats,
        water=glasses, recommendation=rec
    )

    score = 100
    if consumed > calorie_goal:      score -= 20
    if protein < 50:                 score -= 10
    if glasses < 6:                  score -= 10

    return render_template("dashboard.html",
        user=user, meals=meal_rows,
        consumed=consumed, remaining=remaining,
        protein=protein, carbs=carbs, fats=fats,
        water=glasses, recommendation=rec,
        health_score=max(0, score),
        ai_coach=ai_coach,
        calorie_goal=calorie_goal
    )

@app.route("/log_meal", methods=["POST"])
def log_meal():
    if "user_id" not in session:
        return redirect(url_for("login"))
    food_id = int(request.form["food_id"])
    conn = get_db()
    f = conn.execute("SELECT * FROM foods WHERE id=?", (food_id,)).fetchone()
    if f:
        conn.execute("""
            INSERT INTO meals (user_id, food_id, meal_type, calories, protein, carbs, fats, date)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            session["user_id"], food_id, f["meal_type"],
            f["calories"], f["protein"], f["carbs"], f["fats"],
            str(date.today())
        ))
        conn.commit()
    conn.close()
    flash(f"Logged: {f['name']} ({f['calories']} kcal)", "success")
    return redirect(url_for("meal_plan"))

@app.route("/water", methods=["POST"])
def water():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    w = conn.execute(
        "SELECT * FROM water WHERE user_id=? AND date=?",
        (session["user_id"], str(date.today()))
    ).fetchone()
    if w:
        conn.execute("UPDATE water SET glasses=glasses+1 WHERE id=?", (w["id"],))
    else:
        conn.execute(
            "INSERT INTO water (user_id, glasses, date) VALUES (?,?,?)",
            (session["user_id"], 1, str(date.today()))
        )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/api/foods")
def api_foods():
    conn = get_db()
    foods = conn.execute("SELECT * FROM foods").fetchall()
    conn.close()
    return jsonify([dict(f) for f in foods])

@app.route("/meal_plan")
def meal_plan():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if not profile_complete(user):
        flash("Please complete your profile first.", "success")
        return redirect(url_for("onboarding"))
    plan = generate_meal_plan(user["id"])
    return render_template("meal_plan.html", user=user, plan=plan)

if __name__ == "__main__":
    app.run(debug=True)