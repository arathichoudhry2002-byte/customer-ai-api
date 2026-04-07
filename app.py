from flask import Flask, request, jsonify
import joblib
from flask_mail import Mail, Message
import mysql.connector

app = Flask(__name__)

print("🚀 Customer AI API Running...")

# ---------------- MAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'arathi.1ki23ai006@gmail.com'
app.config['MAIL_PASSWORD'] = 'czcbnzrolvxzemgq'  # 🔥 FIXED

mail = Mail(app)

# ---------------- DB CONNECT ----------------
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Arathi....2002",
    database="customer_ai"
)

cursor = db.cursor(dictionary=True, buffered=True)

# ---------------- LOAD MODELS ----------------
model = joblib.load("models/model.pkl")
purchase_model = joblib.load("models/purchase_model.pkl")

# ---------------- EMAIL FUNCTION ----------------
def send_email(to, subject, body):
    try:
        msg = Message(subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[to])
        msg.body = body
        mail.send(msg)
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print("❌ Email error:", e)
        return False

# ---------------- API KEY ----------------
def validate_api_key(req):
    api_key = req.headers.get("x-api-key")

    if api_key != "test123":
        return False

    return True

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "🚀 Customer AI API LIVE"

# ---------------- TRACK VIEW ----------------
@app.route("/api/track-view", methods=["POST"])
def track_view():
    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    email = data["email"]
    product_id = data["product_id"]

    cursor.execute(
        "SELECT * FROM user_behavior WHERE email=%s AND product_id=%s",
        (email, product_id)
    )
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE user_behavior
            SET clicks = clicks + 1
            WHERE email=%s AND product_id=%s
        """, (email, product_id))
    else:
        cursor.execute("""
            INSERT INTO user_behavior (email, product_id, clicks, added_to_cart)
            VALUES (%s, %s, 1, FALSE)
        """, (email, product_id))

    db.commit()

    return jsonify({"message": "view tracked"})

# ---------------- ADD TO CART ----------------
@app.route("/api/add-to-cart", methods=["POST"])
def add_to_cart():
    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    email = data["email"]
    product_id = data["product_id"]

    cursor.execute("""
        UPDATE user_behavior
        SET added_to_cart = TRUE
        WHERE email=%s AND product_id=%s
    """, (email, product_id))

    db.commit()

    decision = check_behavior(email)

    return jsonify({"decision": decision})

# ---------------- ANALYZE ----------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    email = data["email"]

    decision = check_behavior(email)

    return jsonify({"decision": decision})

# ---------------- BEHAVIOR LOGIC ----------------
def check_behavior(email):
    cursor.execute("SELECT * FROM user_behavior WHERE email=%s", (email,))
    rows = cursor.fetchall()

    for row in rows:
        if row["added_to_cart"]:
            send_email(email, "Discount 🎉", "Get 10% OFF now!")
            return "💸 discount_sent"

        if row["clicks"] >= 2:
            return "👀 interested_user"

    return "no_action"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)