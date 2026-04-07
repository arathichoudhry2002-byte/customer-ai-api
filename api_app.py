from flask import Flask, request, jsonify
import mysql.connector
from flask_mail import Mail, Message

app = Flask(__name__)
print("🚀 Customer AI API Running...")

# ---------------- MAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = 'arathi.1ki23ai006@gmail.com'
app.config['MAIL_PASSWORD'] = 'czcbnzrolvxzemgq'

mail = Mail(app)

# ---------------- DB CONNECT ----------------
db = None
cursor = None

try:
    db = mysql.connector.connect(
        host="interchange.proxy.rlwy.net",
        user="root",
        password="nHZZvmjfVoaRTzdPgQhQyGLYZnrLXAbr",
        database="railway",
        port=25755,
        ssl_disabled=False,
        ssl_verify_cert=False
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


# ---------------- API KEY (🔥 FIXED) ----------------
def validate_api_key(req):
    try:
        api_key = req.headers.get("x-api-key")

        if not api_key:
            return False

        cursor.execute(
            "SELECT * FROM api_clients WHERE api_key=%s AND status='active'",
            (api_key,)
        )
        client = cursor.fetchone()

        if not client:
            return False

        return True

    except Exception as e:
        print("❌ API KEY ERROR:", e)
        return False


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
    try:
        if not db or not cursor:
            return jsonify({"error": "Database not connected"}), 500

        if not validate_api_key(request):
            return jsonify({"error": "Invalid API key"}), 401

        data = request.get_json(force=True)

        email = data.get("email")
        product_id = data.get("product_id")

        if not email or not product_id:
            return jsonify({"error": "Missing email or product_id"}), 400

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

    except Exception as e:
        print("❌ TRACK ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- ADD TO CART ----------------
@app.route("/api/add-to-cart", methods=["POST"])
def add_to_cart():
    try:
        if not db or not cursor:
            return jsonify({"error": "Database not connected"}), 500

        if not validate_api_key(request):
            return jsonify({"error": "Invalid API key"}), 401

        data = request.get_json(force=True)

        email = data.get("email")
        product_id = data.get("product_id")

        if not email or not product_id:
            return jsonify({"error": "Missing email or product_id"}), 400

        cursor.execute(
            "SELECT * FROM user_behavior WHERE email=%s AND product_id=%s",
            (email, product_id)
        )
        row = cursor.fetchone()

        if row:
            cursor.execute("""
                UPDATE user_behavior
                SET added_to_cart = TRUE
                WHERE email=%s AND product_id=%s
            """, (email, product_id))
        else:
            cursor.execute("""
                INSERT INTO user_behavior (email, product_id, clicks, added_to_cart)
                VALUES (%s, %s, 1, TRUE)
            """, (email, product_id))

        db.commit()

        decision = check_behavior(email)
        return jsonify({"decision": decision})

    except Exception as e:
        print("❌ ADD TO CART ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- ANALYZE ----------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        if not db or not cursor:
            return jsonify({"error": "Database not connected"}), 500

        if not validate_api_key(request):
            return jsonify({"error": "Invalid API key"}), 401

        data = request.get_json(force=True)
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email missing"}), 400

        decision = check_behavior(email)
        return jsonify({"decision": decision})

    except Exception as e:
        print("❌ ANALYZE ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- BEHAVIOR LOGIC ----------------
def check_behavior(email):
    cursor.execute("SELECT * FROM user_behavior WHERE email=%s", (email,))
    rows = cursor.fetchall()

    if not rows:
        return "no_data"

    for row in rows:
        if row.get("added_to_cart"):
            send_email(email, "Discount 🎉", "Get 10% OFF now!")
            return "💸 discount_sent"

        if row.get("clicks", 0) >= 2:
            return "👀 interested_user"

    return "no_action"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)