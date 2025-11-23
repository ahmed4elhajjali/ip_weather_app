from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import os

app = Flask(__name__)

# مفتاح الطقس (غيّره بمفتاحك من weatherapi.com لو عايز دقة أعلى)
WEATHER_API_KEY = "ee3a24feb94b3d71d8948bf67643b510"

# تحميل ملف المنتجات بأمان (الحل النهائي)
CSV_PATH = "products.csv"

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    print(f"تم تحميل {len(df)} منتج من products.csv بنجاح!")
else:
    print("تحذير: products.csv مش موجود → بيستخدم بيانات وهمية")
    df = pd.DataFrame({
        'product_id': [101, 102, 103, 104, 105, 106, 107, 108],
        'product_name_ar': ['تيشيرت قطن صيفي', 'بنطلون جينز', 'جاكيت شتوي', 'شورت بحر', 'قميص رسمي', 'فستان صيفي', 'هودي خريفي', 'ترينج رياضي'],
        'sell_price': [199.99, 449.50, 899.00, 149.75, 299.00, 399.00, 599.00, 350.00],
        'category': ['لبس صيفي', 'لبس ربيعي', 'لبس شتوي', 'لبس صيفي', 'لبس خريفي', 'لبس صيفي', 'لبس خريفي', 'لبس ربيعي']
    })

CITIES_CACHE = {}

def get_clothing_category(temp):
    if temp < 10:   return "لبس شتوي"
    elif temp < 16: return "لبس خريفي"
    elif temp < 26: return "لبس ربيعي"
    else:           return "لبس صيفي"

def get_client_ip():
    headers = ['CF-Connecting-IP', 'X-Forwarded-For', 'X-Real-IP']
    for h in headers:
        val = request.headers.get(h)
        if val:
            return val.split(',')[0].strip()
    return request.remote_addr or "127.0.0.1"

def get_user_location(ip):
    if ip.startswith(("127.", "192.168.", "10.", "::1")):
        return {"country": "EG", "country_name": "مصر", "city": "القاهرة", "lat": 30.0444, "lon": 31.2357}
    try:
        data = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8).json()
        if not data.get("error"):
            return {
                "country": data.get("country"),
                "country_name": data.get("country_name", "مصر"),
                "city": data.get("city", "القاهرة"),
                "region": data.get("region", ""),
                "lat": data.get("latitude"),
                "lon": data.get("longitude")
            }
    except: pass
    return {"country": "EG", "country_name": "مصر", "city": "القاهرة"}

def get_cities_by_country(country_code):
    if country_code in CITIES_CACHE:
        return CITIES_CACHE[country_code]
    
    fallback = {
        "EG": ["القاهرة","الإسكندرية","الجيزة","شرم الشيخ","الغردقة","الأقصر","أسوان","المنصورة","طنطا","أسيوط"],
        "SA": ["الرياض","جدة","مكة","المدينة المنورة","الدمام","الطائف","القصيم","حائل","تبوك","الأحساء"],
        "AE": ["دبي","أبوظبي","الشارقة","العين","رأس الخيمة","عجمان","الفجيرة"],
        "LB": ["بيروت","طرابلس","صيدا","جونية","زلقا"],
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
    except:
        return None

@app.route("/")
def index():
    ip = get_client_ip()
    user_loc = get_user_location(ip)
    country_code = user_loc["country"]
    cities = get_cities_by_country(country_code)
    
    weather = get_weather(lat=user_loc.get("lat"), lon=user_loc.get("lon")) or get_weather(city="القاهرة")
    selected_city = weather["city_name"] if weather else "القاهرة"
    
    category = get_clothing_category(weather["temp"])
    clothes = df[df["category"] == category].sort_values("sell_price").head(20).to_dict("records")
    
    return render_template("dashboard.html",
        user_location=user_loc,
        cities=cities,
        selected_city=selected_city,
        weather=weather,
        clothes=clothes,
        category=category.replace("لبس ", ""),
        total_clothes=len(clothes)
    )

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

# مهم جدًا لـ Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
