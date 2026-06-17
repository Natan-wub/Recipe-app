import requests #for making API requests
import sqlite3 #for database connection
from flask import Flask, render_template, request#for creating the web application and handling requests
#from dotenv import load_dotenv #for loading environment variables
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

SPOONACULAR_KEY = os.environ.get("SPOONACULAR_KEY")

def suggest_drink(temperature):
    if temperature >= 28:
        return {"name": "a tall glass of iced lemonade", "emoji": "🍋"}
    elif temperature >= 18:
        return {"name": "an iced coffee or a fruit smoothie", "emoji": "🥤"}
    elif temperature >= 10:
        return {"name": "a warm cup of tea", "emoji": "🍵"}
    else:
        return {"name": "a hot chocolate", "emoji": "☕"}

@app.route("/")
def home():
    return render_template("index.html")

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
        "drink": drink["name"],
        "emoji": drink["emoji"]
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