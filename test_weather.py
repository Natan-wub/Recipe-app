import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 9.03,
    "longitude": 38.74,
    "current": "temperature_2m"
}

response = requests.get(url, params=params)
data = response.json()

temperature = data["current"]["temperature_2m"]
print(f"The current temperature in Addis Ababa is {temperature}°C")