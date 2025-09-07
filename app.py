import os
import re
import json
import time
import datetime
import random
import requests
from difflib import get_close_matches
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ---------------- Flask App ---------------- #
app = Flask(__name__)
CORS(app)  # <- allow cross-origin requests from Electron

# ---------------- API Keys ---------------- #
# Prefer environment variables if set (safer for deployment), otherwise use the provided defaults.
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "bfff7297457b686059f8c91d5f4913e7")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "133af956c2554f76be7135217250509")
GPT_API_KEY = os.getenv("OPENAI_API_KEY", "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")

client = OpenAI(api_key=GPT_API_KEY)

# ---------------- FAQs & Details ---------------- #
faq = {
    "hi": "Hello! How can I help you today?",
    "hello": "Nice to meet you! What’s your query?",
    "hey": "Hey there! How may I assist you?",

    # Block D
    "where is block d": "Block D is located in Jagran School Of Engineering building at [location].",
    "location of block d": "You’ll find Block D inside the Jagran School of Engineering. [location].",

    # Program Leaders
    "who is program leader": "Mr. Neeraj Sharma is the Program Leader of B.Tech (Room 105, 1st floor, Block D).",
    "where is program leader": "B.Tech Program Leader Neeraj Sir sits in Room 105, 1st floor, Block D.",
    "who is bca program leader": "Vaishali Ma’am is the Program Leader of BCA (Room 203, 2nd floor, Block D).",
    "where is bca program leader": "You’ll find Vaishali Ma’am in Room 203, 2nd floor, Block D.",

    # Head & Coordinator
    "who is hod": "Dr. Dileep Kumar is the Head of Department (HOD). His office is in Room 004, Ground floor, Block D.",
    "where is hod": "HOD Dr. Dileep Kumar sits in Room 004, Ground floor, Block D.",
    "who is school coordinator": "Narendra Sir is the School Coordinator, located in Room 008, Ground floor, Block D.",
    "where is school coordinator": "You’ll find Narendra Sir (School Coordinator) in Room 008, Ground floor, Block D.",

    # Faculty Rooms
    "where is faculty staff": "Faculty offices are on 1st floor, Block D:\n- Room 104 (Data Science / AIML)\n- Room 106 (Plain B.Tech / BCA).",
    "where is btech faculty": "B.Tech Faculty Rooms:\n- DS / AIML: Room 104\n- Plain B.Tech: Room 106",
    "where is bca faculty": "BCA Faculty Rooms:\n- Room 104 and 106, 1st floor, Block D.",
    "where is ixp faculty": "IXP Faculty Rooms are on 1st floor, Block D, Room 104.",
    "where is jlu faculty": "JLU Faculty Rooms are on 1st floor, Block D, Room 107.",

    # Classrooms
    "where are bca classes": "BCA Classes are in Rooms 001, 002, 103, and 108 (Block D).",
    "where are btech classes": "B.Tech Classes are in Rooms 101, 102, 103, and 108 (Block D).",

    # Labs
    "where are labs": "Labs are in Rooms 110, 201, and 011 (Block D).",
    "where are bca labs": "BCA Labs: Rooms 110, 201, and 011.",
    "where are btech labs": "B.Tech Labs: Rooms 110, 201, and 011.",

    # Course Details
    "bca details": "📘 BCA (Bachelor of Computer Applications)\n- 3 years, 6 semesters\n- Specializations: Data Science, UX, Plain BCA\n- Program Leader: Vaishali Ma’am (Room 203, 2nd floor)\n- Classes: 001, 002, 103, 108\n- Labs: 110, 201, 011\n- Extras: Hackathons & workshops.",
    
    "btech details": "📗 B.Tech (Bachelor of Technology)\n- 4 years, 8 semesters\n- Specializations: Data Science, AIML, Plain B.Tech\n- Program Leader: Neeraj Sir (Room 105, 1st floor)\n- Classes: 101, 102, 103, 108\n- Faculty: 104 (specialization), 106 (plain)\n- Labs: 110, 201, 011\n- Extras: Hackathons & projects.",

    # Polite
    "thank you": "You’re most welcome! 😊",
    "bye": "Thank you for chatting with JLU Bot. Have a great day!"
}

# ---------------- Courses ---------------- #
btech_courses = {
    "1": "Semester 1: Mathematics-I, Physics, Basic Electrical Engineering, Programming in C, Engineering Graphics",
    "2": "Semester 2: Mathematics-II, Chemistry, Electronics Engineering, Data Structures, Communication Skills",
    "3": "Semester 3: Mathematics-III, Digital Logic, OOP (C++), Computer Organization, Environmental Science",
    "4": "Semester 4: Algorithms, DBMS, Operating Systems, Software Engineering, Probability & Statistics",
    "5": "Semester 5: Computer Networks, Compiler Design, AI, Web Tech, Elective I",
    "6": "Semester 6: Machine Learning, Cloud Computing, IoT, Cyber Security, Elective II",
    "7": "Semester 7: Deep Learning, Big Data, Blockchain, Research Methodology, Elective III",
    "8": "Semester 8: Project Work, Seminar, Internship"
}

bca_courses = {
    "1": "Semester 1: Fundamentals of Computers, Programming in C, Mathematics-I, Business Communication, Digital Logic",
    "2": "Semester 2: Data Structures, DBMS-I, Mathematics-II, Operating Systems, Environmental Studies",
    "3": "Semester 3: OOP in C++, DBMS-II, Computer Networks, Software Engineering, Probability & Statistics",
    "4": "Semester 4: Java Programming, Web Technologies, Computer Organization, Numerical Methods, Elective I",
    "5": "Semester 5: Python Programming, Data Science Basics, Cyber Security, Elective II, Mini Project",
    "6": "Semester 6: Machine Learning, Cloud Computing, Mobile App Development, Major Project, Internship"
}

# ---------------- Fun ---------------- #
jokes = [
    "Why don’t programmers like nature? Because it has too many bugs! 🐞",
    "Why do Java developers wear glasses? Because they don’t see sharp! 🤓",
    "Why was the computer cold? Because it left its Windows open! 🪟😂",
    "How do you comfort a JavaScript bug? You console it. 💻"
]

quotes = [
    "Believe you can and you're halfway there. 💪",
    "The best way to get started is to quit talking and begin doing. 🚀",
    "Success is not in what you have, but who you are. 🌟",
    "Dream it. Wish it. Do it. 🔥"
]

# ---------------- Small Helpers ---------------- #
def normalize_input(text: str) -> str:
    return (text or "").lower().strip()

def help_text() -> str:
    return (
        "💡 You can ask me:\n"
        "• weather in bhopal / bhopal weather / what's temperature in delhi\n"
        "• news india / news technology\n"
        "• math: 12+5*3, (10-2)/4, 2**10\n"
        "• btech courses / bca courses (then send semester number)\n"
        "• who is hod / where is block d / who is program leader\n"
        "• joke, quote, time, date\n"
    )

# ---------------- Safe Math Evaluator ---------------- #
import ast
import operator as op

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def _eval_ast(node):
    if isinstance(node, ast.Num):  # Py<3.8
        return node.n
    if isinstance(node, ast.Constant):  # Py>=3.8
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.operand))
    if isinstance(node, ast.Expr):
        return _eval_ast(node.value)
    raise ValueError("Unsupported expression")

def solve_math(expr: str):
    # allow digits, ops, dot, spaces, parentheses
    if not re.fullmatch(r"[0-9\.\s\+\-\*\/\%\(\)]{1,200}", expr.replace("**", "**")):
        return None
    try:
        node = ast.parse(expr, mode="eval")
        result = _eval_ast(node.body)
        return f"🧮 The answer is {result}"
    except Exception:
        return None

# ---------------- Caching (to be gentle on APIs) ---------------- #
_cache = {}  # key -> (timestamp, value)
CACHE_TTL = 60  # seconds

def get_cached(key):
    item = _cache.get(key)
    if not item:
        return None
    ts, val = item
    if time.time() - ts > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return val

def set_cached(key, val):
    _cache[key] = (time.time(), val)

# ---------------- News / Weather ---------------- #
def get_news(query="india"):
    cache_key = f"news::{query.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    try:
        url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=5&apikey={NEWS_API_KEY}"
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])[:5]
        if not articles:
            msg = "❌ No news found for that topic."
            set_cached(cache_key, msg)
            return msg
        parts = []
        for a in articles:
            title = a.get("title", "No Title")
            desc = a.get("description", "") or ""
            url = a.get("url", "")
            source = a.get("source", {}).get("name", "Unknown Source")
            if desc and len(desc) > 150:
                desc = desc[:147] + "..."
            parts.append(f"📰 {title}\n   📌 {source}\n   {desc}\n   🔗 {url}")
        result = "\n\n".join(parts)
        set_cached(cache_key, result)
        return result
    except Exception:
        return "⚠️ Couldn’t fetch news right now."

def get_live_weather(city="bhopal"):
    city = city.strip()
    cache_key = f"weather::{city.lower()}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        data = requests.get(url, timeout=6).json()
        if "error" in data:
            return "❌ Sorry, couldn’t fetch weather for that location."
        cond = data["current"]["condition"]["text"]
        temp = data["current"]["temp_c"]
        msg = f"🌡️ Weather in {city.title()}: {cond}, {temp}°C"
        set_cached(cache_key, msg)
        return msg
    except Exception:
        return "⚠️ Couldn’t fetch weather right now."

# ---------------- NLP-ish Routing ---------------- #
def extract_weather_city(text: str):
    # handles: "weather in bhopal", "bhopal weather", "what is the weather of mumbai", "temperature in delhi"
    patterns = [
        r"weather\s+(in|at|of)\s+([a-zA-Z\s]+)$",
        r"(?:what'?s|what is|how is)?\s*the?\s*weather\s+(?:in|at|of)?\s*([a-zA-Z\s]+)$",
        r"([a-zA-Z\s]+)\s+weather$",
        r"(?:temp|temperature)\s+(?:in|at|of)?\s*([a-zA-Z\s]+)$",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            # group with city
            city = m.group(m.lastindex) if m.lastindex else None
            if city:
                return city.strip()
    return None

def is_news_query(text: str):
    return any(w in text for w in ["news", "headline", "headlines", "khabar"])

def news_topic(text: str):
    # "news india", "news technology", etc.
    parts = text.split()
    if len(parts) >= 2 and parts[0] == "news":
        return " ".join(parts[1:])
    return None

# ---------------- Main Brain ---------------- #
# ---------------- Main Brain with Safe GPT Fallback ---------------- #
def find_answer(user_input: str):
    text = normalize_input(user_input)

    if not text:
        return "Please type something. " + help_text()

    # Help
    if text in ("help", "menu", "options"):
        return help_text()

    # FAQs
    if text in faq:
        return faq[text]

    # Courses prompt flows
    if text in ("btech courses", "show btech courses"):
        return "Please enter semester number (1–8)."
    if text in btech_courses:
        return btech_courses[text]

    if text in ("bca courses", "show bca courses"):
        return "Please enter semester number (1–6)."
    if text in bca_courses:
        return bca_courses[text]

    # Fun
    if "joke" in text:
        return random.choice(jokes)
    if "quote" in text or "motivate" in text:
        return random.choice(quotes)
    if "time" in text:
        return f"⏰ Current time: {datetime.datetime.now().strftime('%H:%M:%S')}"
    if "date" in text:
        return f"📅 Today’s date: {datetime.date.today().strftime('%d %B %Y')}"

    # Weather first (never depend on GPT)
    if "weather" in text or "temperature" in text or "mausam" in text:
        city = extract_weather_city(text)
        if city:
            return get_live_weather(city)
        m = re.search(r"weather\s+([a-zA-Z\s]+)$", text)
        if m:
            return get_live_weather(m.group(1))
        return get_live_weather("bhopal")

    # News (never depend on GPT)
    if is_news_query(text):
        topic = news_topic(text)
        return get_news(topic or "india")

    # Math
    math_answer = solve_math(text)
    if math_answer:
        return math_answer

    # Fuzzy match from FAQ keys
    match = get_close_matches(text, list(faq.keys()), n=1, cutoff=0.6)
    if match:
        return faq.get(match[0])

    # GPT fallback with error handling
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}],
            max_tokens=200,
            temperature=0.6,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        err = str(e).lower()
        # Common GPT errors
        if "invalid_api_key" in err:
            fallback_msg = ("🤖 GPT API key error detected! "
                            "I can still answer FAQs, news, weather, math, jokes, and quotes.")
        elif "insufficient_quota" in err or "429" in err:
            fallback_msg = ("🤖 GPT API quota exceeded or temporarily unavailable. "
                            "I can still help with FAQs, news, weather, math, jokes, and quotes!")
        elif "network" in err or "timeout" in err:
            fallback_msg = ("⚠️ Network issue while contacting GPT. "
                            "I can still help with FAQs, news, weather, math, jokes, and quotes!")
        else:
            fallback_msg = ("🤖 GPT error occurred. "
                            "I can still answer FAQs, news, weather, math, jokes, and quotes!")

        # Optional: attempt a fuzzy FAQ match as last resort
        match = get_close_matches(text, list(faq.keys()), n=1, cutoff=0.5)
        if match:
            fallback_msg += f"\n\nDid you mean: {faq[match[0]]}"

        return fallback_msg

# ---------------- Routes ---------------- #
@app.route("/")
def home():
    return render_template("index.html")  # your HTML file

@app.route("/get", methods=["POST"])
def get_bot_response():
    # Accept form or JSON body
    user_msg = request.form.get("msg") if request.form else None
    if user_msg is None:
        data = request.get_json(silent=True) or {}
        user_msg = data.get("msg", "")
    user_msg = normalize_input(user_msg)

    # Fast paths for courses
    if user_msg in ("btech courses", "show btech courses"):
        return jsonify("Please enter semester number (1–8).")
    if user_msg in btech_courses:
        return jsonify(btech_courses[user_msg])

    if user_msg in ("bca courses", "show bca courses"):
        return jsonify("Please enter semester number (1–6).")
    if user_msg in bca_courses:
        return jsonify(bca_courses[user_msg])

    # Delegate to core with safe fallback
    reply = find_answer(user_msg)
    return jsonify(reply)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": time.time()})

# ---------------- Main ---------------- #
if __name__ == "__main__":
     app.run(host="0.0.0.0", port=5000, debug=True)
