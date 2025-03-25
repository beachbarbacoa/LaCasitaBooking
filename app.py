from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    diners = db.Column(db.Integer, nullable=False)
    seating = db.Column(db.String(20), nullable=False)
    pickup = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    denial_reason = db.Column(db.String(200))
    telegram_message_id = db.Column(db.String(50))  # New field to track Telegram message ID

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Telegram setup
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# State management
pending_denials = {}

def send_email_async(app_context, subject, recipient, body):
    """Non-blocking email sender with app context"""
    def send_email():
        with app_context:
            try:
                msg = MIMEMultipart()
                msg['From'] = os.getenv('SENDER_EMAIL')
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))

                with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
                    server.starttls()
                    server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                    server.send_message(msg)
                logger.debug(f"Email sent to {recipient}")
            except Exception as e:
                logger.error(f"Email failed: {e}")
    Thread(target=send_email).start()

def send_telegram_async(app_context, reservation):
    """Non-blocking Telegram sender with app context"""
    def send_telegram():
        with app_context:
            try:
                message = f"""New Reservation Request:
Name: {reservation.name}
Email: {reservation.email}
Phone: {reservation.phone}
Date: {reservation.date}
Time: {reservation.time}
Diners: {reservation.diners}
Seating: {reservation.seating}
Pickup: {reservation.pickup}"""

                response = requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": telegram_chat_id,
                        "text": message,
                        "reply_markup": {
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Accept", "callback_data": f"accept_{reservation.id}"},
                                    {"text": "❌ Deny", "callback_data": f"deny_{reservation.id}"}
                                ]
                            ]
                        }
                    },
                    timeout=10
                )
                response_data = response.json()
                if response.ok:
                    reservation.telegram_message_id = str(response_data['result']['message_id'])
                    db.session.commit()
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Telegram failed: {e}")
    Thread(target=send_telegram).start()

def update_telegram_message(reservation_id, new_text, new_markup=None):
    """Update the original Telegram message to show status"""
    try:
        reservation = Reservation.query.get(reservation_id)
        if not reservation or not reservation.telegram_message_id:
            return

        payload = {
            "chat_id": telegram_chat_id,
            "message_id": reservation.telegram_message_id,
            "text": new_text
        }
        
        if new_markup:
            payload["reply_markup"] = new_markup

        response = requests.post(
            f"https://api.telegram.org/bot{telegram_bot_token}/editMessageText",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to update Telegram message: {e}")

@app.route("/reservations", methods=["POST"])
def create_reservation():
    """Create reservation endpoint with async notifications"""
    try:
        data = request.json
        logger.debug(f"New reservation: {data}")

        # Validate input
        required_fields = ["name", "email", "phone", "time", "date", "diners", "seating", "pickup"]
        if not all(field in data for field in required_fields):
            abort(400, "Missing required fields")

        # Create reservation
        reservation = Reservation(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            time=data["time"],
            date=data["date"],
            diners=data["diners"],
            seating=data["seating"],
            pickup=data["pickup"]
        )
        
        db.session.add(reservation)
        db.session.commit()

        # Create application context for background tasks
        app_context = app.app_context()

        # Start async notifications with proper context
        send_telegram_async(app_context, reservation)
        send_email_async(
            app_context,
            "Reservation Request Received",
            reservation.email,
            f"""Hello {reservation.name},<br><br>
            We've received your reservation request for {reservation.date} at {reservation.time}.<br><br>
            You will receive an email soon with your reservation confirmation."""
        )

        return jsonify({
            "status": "success",
            "message": "Reservation created successfully",
            "reservation_id": reservation.id
        }), 200

    except Exception as e:
        logger.error(f"Reservation failed: {e}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/reservations/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id):
    """Get reservation details"""
    try:
        reservation = Reservation.query.get_or_404(reservation_id)
        return jsonify({
            "name": reservation.name,
            "email": reservation.email,
            "phone": reservation.phone,
            "date": reservation.date,
            "time": reservation.time,
            "diners": reservation.diners,
            "seating": reservation.seating,
            "pickup": reservation.pickup,
            "status": reservation.status
        })
    except Exception as e:
        logger.error(f"Failed to get reservation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/telegram-callback", methods=["POST"])
def telegram_callback():
    """Handle Telegram interactions"""
    try:
        data = request.json
        logger.debug(f"Telegram callback: {data}")

        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback["data"]
            reservation_id = int(callback_data.split("_")[1])
            message_id = callback["message"]["message_id"]
            
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                abort(404, "Reservation not found")

            if callback_data.startswith("accept"):
                reservation.status = "Confirmed"
                db.session.commit()
                
                # Update original message
                original_text = callback["message"]["text"]
                update_telegram_message(
                    reservation_id,
                    f"✅ ACCEPTED\n{original_text}",
                    {"inline_keyboard": [[{"text": "✓ Accepted", "callback_data": "already_processed"}]]}
                )
                
                app_context = app.app_context()
                send_email_async(
                    app_context,
                    "Reservation Confirmed",
                    reservation.email,
                    f"Your reservation for {reservation.date} at {reservation.time} is confirmed!"
                )
                
                return jsonify({"status": "confirmed"})

            elif callback_data.startswith("deny"):
                pending_denials[str(callback["message"]["chat"]["id"])] = reservation_id
                
                # Update original message
                original_text = callback["message"]["text"]
                update_telegram_message(
                    reservation_id,
                    f"🔄 PROCESSING DENIAL\n{original_text}",
                    {"inline_keyboard": [[{"text": "Processing...", "callback_data": "already_processing"}]]}
                )
                
                requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": callback["message"]["chat"]["id"],
                        "text": "Please provide a reason for denial:",
                        "reply_markup": {"force_reply": True}
                    },
                    timeout=3
                )
                return jsonify({"status": "awaiting_reason"})

        elif "message" in data and "reply_to_message" in data["message"]:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            
            if chat_id in pending_denials:
                reservation = Reservation.query.get(pending_denials[chat_id])
                if reservation:
                    reason = message.get("text", "No reason provided")
                    reservation.denial_reason = reason
                    reservation.status = "Denied"
                    db.session.commit()
                    
                    # Update original message
                    original_text = data["message"]["reply_to_message"]["text"].replace("🔄 PROCESSING DENIAL\n", "")
                    update_telegram_message(
                        reservation.id,
                        f"❌ DENIED\n{original_text}\nReason: {reason}",
                        {"inline_keyboard": [[{"text": "✗ Denied", "callback_data": "already_processed"}]]}
                    )
                    
                    frontend_url = os.getenv('FRONTEND_URL', f"exp://127.0.0.1:19000/--/reservation?reservation_id={reservation.id}")
                    app_context = app.app_context()
                    send_email_async(
                        app_context,
                        "Reservation Update",
                        reservation.email,
                        f"""Your reservation for {reservation.date} at {reservation.time} was denied.<br>
Reason: {reason}<br><br>
<a href='{frontend_url}'>Click here to book a new time</a><br><br>
Or copy this link to your phone: {frontend_url}"""
                    )
                    
                    del pending_denials[chat_id]
                    return jsonify({"status": "denied"})

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        logger.error(f"Callback error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/test", methods=["GET"])
def test_endpoint():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "service": "Reservation System"
    })

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)