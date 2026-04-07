from flask import Flask, request, jsonify
import mysql.connector
from flask_mail import Mail, Message
import os

app = Flask(__name__)
print("🚀 Customer AI API Running...")

# ---------------- MAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

# ---------------- DB CONNECT ----------------
db = None
cursor = None

try:
    db = mysql.connector.connect(
        host=os.environ.get("HOST"),
        user=os.environ.get("USER"),
        password=os.environ.get("PASSWORD"),
        database=os.environ.get("DATABASE"),
        port=int(os.environ.get("DB_PORT"))
    )
    cursor = db.cursor(dictionary=True, buffered=True)
    print("✅ MySQL Connected Successfully")

except Exception as e:
    print("❌ MySQL Connection Error:", e)


# ---------------- EMAIL FUNCTION ----------------
def send_email(to, subject, body):
    try:
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[to]
        )
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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "message": "API is running"})


# ---------------- TRACK VIEW ----------------
@app.route("/api/track-view", methods=["POST"])
def track_view():
    if not db or not cursor:
        return jsonify({"error": "Database not connected"}), 500

    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    email = data.get("email")
    product_id = data.get("product_id")

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
    if not db or not cursor:
        return jsonify({"error": "Database not connected"}), 500

    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    data = request.get_json()
    email = data.get("email")
    product_id = data.get("product_id")

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
    if not db or not cursor:
        return jsonify({"error": "Database not connected"}), 500

    if not validate_api_key(request):
        return jsonify({"error": "Invalid API key"}), 401

    email = request.json.get("email")

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)