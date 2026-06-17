import requests

api_key = "92d01d4ca61048fa9a70a90a8252e672"

url = "https://api.spoonacular.com/recipes/findByIngredients"
params = {
    "ingredients": "eggs,tomato,cheese",
    "number": 3,
    "apiKey": api_key
}

response = requests.get(url, params=params)
data = response.json()

for recipe in data:
    print(recipe["title"])