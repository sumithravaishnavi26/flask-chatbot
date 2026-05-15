from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from markdown import markdown  # ✅ for pretty text formatting
import traceback

# -----------------------------
# Flask Setup
# -----------------------------
app = Flask(__name__)
app.secret_key = "my_super_secret_dev_key"
CORS(app, supports_credentials=True)

# -----------------------------
# Gemini Setup
# -----------------------------
# ✅ Paste your valid Gemini API key
GEMINI_API_KEY = "AIzaSyAKJOv4MVoH262-yL_h7ld_rBTH3oV3HW4"

if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY not provided! Please set it here in the code.")

genai.configure(api_key=GEMINI_API_KEY)

# ✅ Use a valid model (from your list)
model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# In-memory storage
# -----------------------------
users = {}          # {username: hashed_password}
chat_history = {}   # {username: [{"user": msg, "bot": reply}]}

# -----------------------------
# Error handler
# -----------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    print("Unhandled Exception:")
    traceback.print_exc()
    return jsonify({"error": "Server error occurred"}), 500

# -----------------------------
# Gemini chat query
# -----------------------------
def query_gemini(username, user_input):
    history_text = ""
    for turn in chat_history.get(username, []):
        history_text += f"User: {turn['user']}\nBot: {turn['bot']}\n"
    full_prompt = history_text + f"User: {user_input}\nBot:"

    try:
        response = model.generate_content(full_prompt)
        if response and hasattr(response, "text"):
            markdown_text = response.text
            reply = markdown(markdown_text)  # ✅ Converts markdown → HTML
        else:
            reply = "Sorry, I didn’t get that."
    except Exception as e:
        print("Gemini API error:", e)
        traceback.print_exc()
        reply = "⚠ Gemini API error. Try again later."
    return reply

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html", username=session.get("username"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            return "Username and password required", 400
        if username in users:
            return "User already exists", 400
        users[username] = generate_password_hash(password)
        chat_history[username] = []
        session["username"] = username
        return redirect(url_for("chat_page"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username not in users or not check_password_hash(users[username], password):
            return "Invalid credentials", 401
        session["username"] = username
        return redirect(url_for("chat_page"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/chat")
def chat_page():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])

@app.route("/chat", methods=["POST"])
def chat_api():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 403
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        user_input = (data.get("message") or "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400

        username = session["username"]
        bot_reply = query_gemini(username, user_input)

        chat_history.setdefault(username, []).append({"user": user_input, "bot": bot_reply})
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("Unexpected Chat API error:", e)
        traceback.print_exc()
        return jsonify({"error": "Server error occurred"}), 500

@app.route("/history", methods=["GET"])
def history():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 403
    return jsonify(chat_history.get(session["username"], []))

@app.route("/ping")
def ping():
    return "pong"

# -----------------------------
# Run the app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
