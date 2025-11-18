from flask import Flask, render_template
import requests

app = Flask(__name__)

WEATHER_API_KEY = "ee3a24feb94b3d71d8948bf67643b510"  # ضع هنا مفتاح OpenWeather

# --- دالة لجلب IP حقيقي حتى على localhost ---
def get_real_ip():
    try:
        ip = requests.get("https://api.ipify.org").text
        return ip
    except:
        return "8.8.8.8"  # IP افتراضي للتجربة

# --- دالة لجلب موقع IP ---
def get_location(ip):
    try:
        url = f"https://ipapi.co/{ip}/json/"
        data = requests.get(url).json()
        if "error" in data:
            return None
        return {
            "ip": ip,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "org": data.get("org")
        }
    except:
        
        return None

# --- دالة لجلب الطقس ---
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        return {
            "temp": data["main"]["temp"],
            "desc": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"]
        }
    except:
        return None

@app.route("/")
def index():
    user_ip = get_real_ip()
    location = get_location(user_ip)
    
    if location:
        weather = get_weather(location["latitude"], location["longitude"])
    else:
        weather = None

    return render_template("dashboard.html", location=location, weather=weather)

if __name__ == "__main__":
    app.run(debug=True)
