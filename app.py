from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# جلب مفتاح OpenWeather من Environment Variable
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

# --- دالة لجلب IP المستخدم الحقيقي ---
def get_real_ip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not ip:
        ip = "127.0.0.1"  # IP افتراضي للتطوير المحلي
    return ip

# --- دالة لجلب موقع IP ---
def get_location(ip):
    # لو localhost، استخدم موقع افتراضي للتطوير المحلي
    if ip.startswith("127.") or ip == "localhost":
        return {
            "ip": ip,
            "city": "Cairo",
            "region": "Cairo Governorate",
            "country": "Egypt",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "org": "Localhost"
        }
    # لو IP خارجي
    try:
        url = f"https://ipapi.co/{ip}/json/"
        data = requests.get(url, timeout=5).json()
        if data.get("error"):
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
    except Exception as e:
        print("Location error:", e)
        return None

# --- دالة لجلب الطقس ---
def get_weather(lat, lon):
    if not WEATHER_API_KEY:
        return {"temp": "--", "desc": "No API Key", "humidity": "--", "wind": "--"}
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url, timeout=5).json()
        return {
            "temp": data["main"]["temp"],
            "desc": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"]
        }
    except Exception as e:
        print("Weather error:", e)
        return {"temp": "--", "desc": "Unknown", "humidity": "--", "wind": "--"}

@app.route("/")
def index():
    user_ip = get_real_ip()
    location = get_location(user_ip)
    
    if location and location["latitude"] and location["longitude"]:
        weather = get_weather(location["latitude"], location["longitude"])
    else:
        weather = {"temp": "--", "desc": "Unknown", "humidity": "--", "wind": "--"}

    return render_template("dashboard.html", location=location, weather=weather)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
