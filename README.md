# CaloByte

CaloByte is an AI-powered nutrition and fitness web app built with Flask. It helps users create weekly meal plans, track calories, macros, water intake, and receive personalized AI fitness tips.

## Features

- User signup and login
- Personalized onboarding with height, weight, calorie goal, water goal, and fitness goal
- 7-day meal plan generation
- Daily nutrition dashboard
- Calories, macros, BMI, and water tracking
- Smart meal recommendations
- AI Fitness Coach using NVIDIA's Gemma model

## Tech Stack

- Python
- Flask
- SQLite
- HTML/CSS/Jinja
- JavaScript
- NVIDIA AI API

## Run Locally in VS Code

1. Clone the repo:
```bash
git clone YOUR_GITHUB_REPO_URL
cd calobyte


2. Create a virtual environment:
python -m venv venv

3. Activate it:
Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

4. Install dependencies:
pip install -r requirements.txt

5. Create a .env file:
NVIDIA_API_KEY=your_api_key_here

6. Run the app:
python app.py

7. Open in browser:
http://127.0.0.1:5000

