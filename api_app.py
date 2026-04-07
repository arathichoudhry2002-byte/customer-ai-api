from flask import Flask, request, jsonify
import mysql.connector
from flask_mail import Mail, Message
import os

app = Flask(__name__)
print("✅ API APP FILE IS RUNNING")

# ---------------- MAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# 🔥 DIRECT VALUE (WORKING)
app.config['MAIL_USERNAME'] = "arathi.1ki23ai006@gmail.com"
app.config['MAIL_PASSWORD'] = "czcbnzrolvxzemgq"  # remove spaces

mail = Mail(app)
# ---------------- DB CONNECT (🔥 FIXED) ----------------
try:
    db = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", "your_local_password"),
    database=os.environ.get("DB_NAME", "customer_ai"),
    port=int(os.environ.get("DB_PORT", 3306))
)
    print("✅ MySQL Connected Successfully")

except Exception as e:
    print("❌ MySQL Connection Error:", e)
    exit()

# buffered=True avoids unread result errors
cursor = db.cursor(dictionary=True, buffered=True)


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


# ---------------- API KEY CHECK ----------------
def validate_api_key(req):
    api_key = req.headers.get("x-api-key")

    if not api_key:
        return False, "API key missing"

    cursor.execute(
        "SELECT * FROM api_clients WHERE api_key=%s AND status='active'",
        (api_key,)
    )
    client = cursor.fetchone()

    if not client:
        return False, "Invalid API key"

    return True, client["client_name"]

@app.route("/")
def home():
    return "🚀 Customer AI API is running!"


# ---------------- HEALTH ----------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "API is running"
    })


# ---------------- TRACK VIEW ----------------
@app.route("/api/track-view", methods=["POST"])
def track_view():
    valid, result = validate_api_key(request)
    if not valid:
        return jsonify({"status": "error", "message": result}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON body"}), 400

    email = data.get("email")
    product_id = data.get("product_id")

    if not email or product_id is None:
        return jsonify({
            "status": "error",
            "message": "email and product_id required"
        }), 400

    cursor.execute(
        "SELECT * FROM user_behavior WHERE email=%s AND product_id=%s",
        (email, product_id)
    )
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE user_behavior
            SET clicks = clicks + 1,
                last_action = CURRENT_TIMESTAMP
            WHERE email=%s AND product_id=%s
        """, (email, product_id))
    else:
        cursor.execute("""
            INSERT INTO user_behavior (email, product_id, clicks, added_to_cart)
            VALUES (%s, %s, 1, FALSE)
        """, (email, product_id))

    db.commit()

    return jsonify({
        "status": "success",
        "message": "Product view tracked",
        "client": result
    })


# ---------------- ADD TO CART ----------------
@app.route("/api/add-to-cart", methods=["POST"])
def add_to_cart():
    valid, result = validate_api_key(request)
    if not valid:
        return jsonify({"status": "error", "message": result}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON body"}), 400

    email = data.get("email")
    product_id = data.get("product_id")

    if not email or product_id is None:
        return jsonify({
            "status": "error",
            "message": "email and product_id required"
        }), 400

    cursor.execute(
        "SELECT * FROM user_behavior WHERE email=%s AND product_id=%s",
        (email, product_id)
    )
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE user_behavior
            SET added_to_cart = TRUE,
                last_action = CURRENT_TIMESTAMP
            WHERE email=%s AND product_id=%s
        """, (email, product_id))
    else:
        cursor.execute("""
            INSERT INTO user_behavior (email, product_id, clicks, added_to_cart)
            VALUES (%s, %s, 0, TRUE)
        """, (email, product_id))

    db.commit()

    return jsonify({
        "status": "success",
        "message": "Added to cart",
        "client": result
    })


# ---------------- ANALYZE ----------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    valid, result = validate_api_key(request)
    if not valid:
        return jsonify({"status": "error", "message": result}), 401

    data = request.get_json(silent=True)
    email = data.get("email")

    if not email:
        return jsonify({"status": "error", "message": "email required"}), 400

    cursor.execute("SELECT * FROM user_behavior WHERE email=%s", (email,))
    rows = cursor.fetchall()

    if not rows:
        return jsonify({
            "status": "success",
            "decision": "no_action"
        })

    for row in rows:
        if row["added_to_cart"]:
            send_email(email, "Discount 🎉", "Get 10% OFF!")
            return jsonify({"decision": "discount_sent"})

        if row["clicks"] >= 2:
            return jsonify({"decision": "interested_user"})

    return jsonify({"decision": "no_action"})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)