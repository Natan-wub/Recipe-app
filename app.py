import requests #for making API requests
import sqlite3 #for database connection
from flask import Flask, render_template, request#for creating the web application and handling requests
#from dotenv import load_dotenv #for loading environment variables
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

DB_NAME = "recipes.db"

def init_db():#function to initialize the database and create the saved_recipes table if it doesn't exist
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_recipes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            image TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()#initialize the database when the application starts

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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/saved", methods=["POST"])
def save_recipe():
    recipe = request.get_json()

    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT OR REPLACE INTO saved_recipes (id, title, image) VALUES (?, ?, ?)",
        (recipe["id"], recipe["title"], recipe["image"])
    )
    conn.commit()
    conn.close()

    return {"status": "saved"}

@app.route("/api/saved", methods=["GET"])
def list_saved():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT id, title, image FROM saved_recipes").fetchall()
    conn.close()

    saved = []
    for row in rows:
        saved.append({"id": row[0], "title": row[1], "image": row[2]})

    return {"recipes": saved}

@app.route("/api/saved/<int:recipe_id>", methods=["DELETE"])
def delete_saved(recipe_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM saved_recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    return {"status": "deleted"}

@app.route("/api/weather")
@app.route("/api/weather")
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
def recipes():
    ingredients = request.args.get("ingredients")

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
            "missed": recipe["missedIngredientCount"]
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