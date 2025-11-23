from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)
WEATHER_API_KEY = "ee3a24feb94b3d71d8948bf67643b510"
df = pd.read_csv("C:/Users/asd/OneDrive/Desktop/products.csv")

# تخزين مؤقت للمدن حسب البلد (عشان ما نعملش طلبات كتير)
CITIES_CACHE = {}

def get_clothing_category(temp):
    if temp < 10:   return "لبس شتوي"
    elif temp < 16: return "لبس خريفي"
    elif temp < 26: return "لبس ربيعي"
    else:           return "لبس صيفي"

def get_client_ip():
    headers = ['CF-Connecting-IP', 'X-Forwarded-For', 'X-Real-IP']
    for h in headers:
        if request.headers.get(h):
            return request.headers.get(h).split(',')[0].strip()
    return request.remote_addr or "127.0.0.1"

def get_user_location(ip):
    if ip.startswith(("127.", "192.168.", "10.", "::1")):
        return {"country": "Egypt", "country_name": "مصر", "city": "القاهرة", "lat": 30.0444, "lon": 31.2357}
    try:
        data = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8).json()
        if data.get("error"): return None
        return {
            "country": data.get("country"),
            "country_name": data.get("country_name", "غير معروف"),
            "city": data.get("city", "غير معروف"),
            "region": data.get("region", ""),
            "lat": data.get("latitude"),
            "lon": data.get("longitude")
        }
    except:
        return None

def get_cities_by_country(country_code):
    if country_code in CITIES_CACHE:
        return CITIES_CACHE[country_code]
    
    # API مجاني يجيب مدن الدولة (مصر, السعودية, الإمارات, لبنان, الأردن...)
    url = f"https://countriesnow.space/api/v0.1/countries/cities"
    payload = {"country": country_code}
    try:
        resp = requests.post(url, json=payload, timeout=10).json()
        if resp.get("error") == False:
            cities = resp["data"]
            CITIES_CACHE[country_code] = sorted(cities)
            return sorted(cities)
    except: pass
    
    # لو فشل → قايمة يدوية لأهم الدول
    fallback = {
        "EG": ["القاهرة","الإسكندرية","الجيزة","شرم الشيخ","الغردقة","الأقصر","أسوان","طنطا","المنصورة","أسيوط"],
        "SA": ["الرياض","جدة","مكة","المدينة المنورة","الدمام","الطائف","القصيم","حائل","تبوك"],
        "AE": ["دبي","أبوظبي","الشارقة","العين","رأس الخيمة","عجمان","الفجيرة"],
        "LB": ["بيروت","طرابلس","صيدا","جونية","زلقا","جونيه"],
        "JO": ["عمان","الزرقاء","إربد","العقبة","السلط"]
    }
    cities = fallback.get(country_code, ["القاهرة"])
    CITIES_CACHE[country_code] = cities
    return cities

def get_weather(city=None, lat=None, lon=None):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"appid": WEATHER_API_KEY, "units": "metric", "lang": "ar"}
        if lat and lon:
            params.update({"lat": lat, "lon": lon})
        else:
            params["q"] = city
        data = requests.get(url, params=params, timeout=10).json()
        if data.get("cod") != 200: return None
        return {
            "temp": int(round(data["main"]["temp"])),
            "feels_like": int(round(data["main"]["feels_like"])),
            "desc": data["weather"][0]["description"].capitalize(),
            "icon": data["weather"][0]["icon"],
            "humidity": data["main"]["humidity"],
            "wind": round(data.get("wind", {}).get("speed", 0) * 3.6, 1),
            "city_name": data["name"]
        }
    except: return None

@app.route("/")
def index():
    ip = get_client_ip()
    user_loc = get_user_location(ip) or {"country": "EG", "country_name": "مصر", "city": "القاهرة"}
    
    country_code = user_loc["country"]
    cities = get_cities_by_country(country_code)
    
    # طقس المدينة اللي اكتشفناها من الـ IP
    weather = get_weather(lat=user_loc.get("lat"), lon=user_loc.get("lon")) or get_weather(city="القاهرة")
    selected_city = weather["city_name"] if weather else "القاهرة"

    category = get_clothing_category(weather["temp"])
    clothes = df[df["category"] == category].sort_values("sell_price").head(15).to_dict("records")
    category_name = category.replace("لبس ", "")

    return render_template("dashboard.html",
        user_location=user_loc,
        cities=cities,
        selected_city=selected_city,
        weather=weather,
        clothes=clothes,
        category=category_name,
        total_clothes=len(clothes)
    )

# AJAX لتحديث الطقس والملابس لما تختار مدينة جديدة
@app.route("/update", methods=["POST"])
def update():
    city = request.json.get("city")
    weather = get_weather(city=city)
    if not weather:
        return jsonify({"error": "المدينة غير موجودة"}), 404
    
    category = get_clothing_category(weather["temp"])
    clothes = df[df["category"] == category].sort_values("sell_price").head(30).to_dict("records")
    
    return jsonify({
        "city": weather["city_name"],
        "temp": weather["temp"],
        "desc": weather["desc"],
        "icon": weather["icon"],
        "feels_like": weather["feels_like"],
        "humidity": weather["humidity"],
        "wind": weather["wind"],
        "category": category.replace("لبس ", ""),
        "clothes": clothes
    })

if __name__ == "__main__":
    print("التطبيق شغال! افتح: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
