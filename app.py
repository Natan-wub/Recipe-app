from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

import requests #for making API requests
#import sqlite3 #for database connection#
import psycopg2 #FFOR connecting to PostgreSQL database
from flask import Flask, render_template, request#for creating the web application and handling requests
#from dotenv import load_dotenv #for loading environment variables
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_recipes (
            user_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            title TEXT,
            image TEXT,
            PRIMARY KEY (user_id, recipe_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

SPOONACULAR_KEY = os.environ.get("SPOONACULAR_KEY")

def suggest_drink(temperature):
    if temperature >= 28:
        return {
            "name": "Iced lemonade",
            "emoji": "🍋",
            "ingredients": ["1 cup cold water", "Juice of 1 lemon", "2 tbsp sugar", "A handful of ice"],
            "steps": [
                "Stir the lemon juice and sugar together until the sugar dissolves.",
                "Add the cold water and mix well.",
                "Drop in the ice and serve."
            ]
        }
    elif temperature >= 18:
        return {
            "name": "Iced coffee",
            "emoji": "🥤",
            "ingredients": ["1 cup brewed coffee, cooled", "1/2 cup milk", "1 tsp sugar (optional)", "A handful of ice"],
            "steps": [
                "Brew a cup of coffee and let it cool.",
                "Fill a glass with ice.",
                "Pour the coffee over the ice, add milk and sugar, and stir."
            ]
        }
    elif temperature >= 10:
        return {
            "name": "Hot tea",
            "emoji": "🍵",
            "ingredients": ["1 cup hot water", "1 tea bag", "Honey or sugar to taste"],
            "steps": [
                "Boil the water and pour it over the tea bag in a mug.",
                "Let it steep for 3 to 5 minutes, then remove the tea bag.",
                "Sweeten with honey or sugar if you like."
            ]
        }
    else:
        return {
            "name": "Hot chocolate",
            "emoji": "☕",
            "ingredients": ["1 cup milk", "2 tbsp cocoa powder", "2 tbsp sugar", "A pinch of salt"],
            "steps": [
                "Warm the milk in a small pot over medium heat — don't let it boil.",
                "Whisk in the cocoa, sugar, and salt until smooth.",
                "Pour into a mug and enjoy."
            ]
        }

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return {"error": "Username and password are required."}, 400

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return {"error": "That username is already taken."}, 400

    password_hash = generate_password_hash(password)
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (username, password_hash)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    session["user_id"] = user_id
    return {"username": username}

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row and check_password_hash(row[1], password):
        session["user_id"] = row[0]
        return {"username": username}
    else:
        return {"error": "Wrong username or password."}, 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return {"status": "logged out"}

@app.route("/api/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return {"user": None}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return {"user": row[0] if row else None}


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/saved", methods=["POST"])
def save_recipe():
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Please log in to save recipes."}, 401

    recipe = request.get_json()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO saved_recipes (user_id, recipe_id, title, image) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, recipe_id) DO NOTHING",
        (user_id, recipe["id"], recipe["title"], recipe["image"])
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "saved"}

@app.route("/api/saved", methods=["GET"])
def list_saved():
    user_id = session.get("user_id")
    if not user_id:
        return {"recipes": []}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT recipe_id, title, image FROM saved_recipes WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    saved = []
    for row in rows:
        saved.append({"id": row[0], "title": row[1], "image": row[2]})
    return {"recipes": saved}

@app.route("/api/saved/<int:recipe_id>", methods=["DELETE"])
def delete_saved(recipe_id):
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Please log in."}, 401

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_recipes WHERE user_id = %s AND recipe_id = %s", (user_id, recipe_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "deleted"}
def weather():
    latitude = request.args.get("lat", 9.03)
    longitude = request.args.get("lon", 38.74)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m"
    }

    response = requests.get(url, params=params)
    data = response.json()
    temperature = data["current"]["temperature_2m"]

    drink = suggest_drink(temperature)

    return {
        "temperature": temperature,
        "name": drink["name"],
        "emoji": drink["emoji"],
        "ingredients": drink["ingredients"],
        "steps": drink["steps"]
    }
@app.route("/api/recipes")
@app.route("/api/recipes")
def recipes():
    ingredients = request.args.get("ingredients")
    max_calories = request.args.get("maxCalories")

    if max_calories:
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "includeIngredients": ingredients,
            "maxCalories": max_calories,
            "number": 6,
            "addRecipeNutrition": "true",
            "sort": "min-missing-ingredients",
            "apiKey": SPOONACULAR_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "results" not in data:
            return {"recipes": [], "error": data.get("message", "Recipe service error")}

        recipes_list = []
        for recipe in data["results"]:
            calories = None
            for nutrient in recipe.get("nutrition", {}).get("nutrients", []):
                if nutrient["name"] == "Calories":
                    calories = round(nutrient["amount"])
                    break
            recipes_list.append({
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe.get("image", ""),
                "calories": calories
            })

        return {"recipes": recipes_list}

    else:
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ingredients,
            "number": 6,
            "ranking": 1,
            "ignorePantry": "true",
            "apiKey": SPOONACULAR_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()

        if not isinstance(data, list):
            return {"recipes": [], "error": data.get("message", "Recipe service error")}

        recipes_list = []
        for recipe in data:
            recipes_list.append({
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe["image"],
                "used": recipe["usedIngredientCount"],
                "missed": recipe["missedIngredientCount"],
                "calories": None
            })

        return {"recipes": recipes_list}
    
@app.route("/api/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_KEY}

    response = requests.get(url, params=params)
    data = response.json()

    ingredients = []
    for item in data.get("extendedIngredients", []):
        ingredients.append(item["original"])

    steps = []
    instructions = data.get("analyzedInstructions", [])
    if instructions:
        for step in instructions[0]["steps"]:
            steps.append(step["step"])

    return {
        "title": data.get("title", "Recipe"),
        "image": data.get("image", ""),
        "readyInMinutes": data.get("readyInMinutes", "?"),
        "servings": data.get("servings", "?"),
        "ingredients": ingredients,
        "steps": steps
    }

if __name__ == "__main__":
    app.run(debug=True)