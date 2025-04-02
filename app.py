# TELEGRAM RESERVATION SYSTEM - COMPLETE VERSION
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
from datetime import datetime
import uuid  # For generating unique tokens

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql:///reservations')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    diners = db.Column(db.Integer, nullable=False)
    seating = db.Column(db.String(20), nullable=False)
    pickup = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=True)
    denial_reason = db.Column(db.String(200), nullable=True)
    token = db.Column(db.String(36), nullable=False, unique=True)  # Add token field

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['SENDER_EMAIL'] = os.getenv('SENDER_EMAIL', 'no-reply@reservations.com')

# Telegram setup
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# State management
pending_denials = {}
telegram_message_store = {}

def send_email_async(app_context, subject, recipient, body):
    def send_email():
        with app_context:
            try:
                msg = MIMEMultipart()
                msg['From'] = app.config['SENDER_EMAIL']
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))

                with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
                    if app.config['MAIL_USE_TLS']:
                        server.starttls()
                    server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                    server.send_message(msg)
                logger.info(f"Email sent to {recipient}")
            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
    Thread(target=send_email).start()

def send_telegram_async(app_context, reservation):
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
                
                if response.ok:
                    response_data = response.json()
                    telegram_message_store[reservation.id] = str(response_data['result']['message_id'])
                    logger.info(f"Telegram message stored for reservation {reservation.id}")
                else:
                    logger.error(f"Telegram API error: {response.text}")
            except Exception as e:
                logger.error(f"Telegram failed: {str(e)}")
    Thread(target=send_telegram).start()

def update_telegram_message(reservation_id, new_text, new_markup=None):
    try:
        message_id = telegram_message_store.get(reservation_id)
        if not message_id:
            logger.error(f"No message ID found for reservation {reservation_id}")
            return

        payload = {
            "chat_id": telegram_chat_id,
            "message_id": message_id,
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
        logger.info(f"Telegram message updated for reservation {reservation_id}")
    except Exception as e:
        logger.error(f"Failed to update Telegram message: {str(e)}")

@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    try:
        if not request.is_json:
            abort(400, "Request must be JSON")

        data = request.get_json()
        logger.info(f"New reservation data: {data}")

        required_fields = ["name", "email", "phone", "time", "date", "diners", "seating", "pickup"]
        if missing := [f for f in required_fields if f not in data]:
            abort(400, f"Missing fields: {', '.join(missing)}")

        try:
            datetime.strptime(data["date"], "%Y-%m-%d")
        except ValueError:
            abort(400, "Invalid date format. Use YYYY-MM-DD")

        # Generate a unique token for the reservation
        reservation = Reservation(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            time=data["time"],
            date=data["date"],
            diners=int(data["diners"]),
            seating=data["seating"],
            pickup=data["pickup"],
            token=str(uuid.uuid4())  # Generate unique token
        )

        db.session.add(reservation)
        db.session.commit()

        app_context = app.app_context()
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
            "message": "Reservation created",
            "reservation_id": reservation.id
        }), 201

    except Exception as e:
        logger.error(f"Reservation creation failed: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route("/telegram-callback", methods=["POST"])
def telegram_callback():
    logger.info("Received Telegram callback")
    try:
        data = request.json
        logger.debug(f"Callback data: {data}")
        if not data:
            logger.error("Empty Telegram callback received")
            return jsonify({"status": "error", "message": "Empty data"}), 400

        # Handle callback queries (button presses)
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback["data"]
            
            try:
                action, reservation_id = callback_data.split("_")
                reservation_id = int(reservation_id)
            except (ValueError, IndexError):
                logger.error(f"Invalid callback data: {callback_data}")
                return jsonify({"status": "error", "message": "Invalid callback data"}), 400
            
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                logger.error(f"Reservation not found: {reservation_id}")
                abort(404, "Reservation not found")

            original_text = callback["message"]["text"]

            # Immediately answer the callback to prevent timeout
            requests.post(
                f"https://api.telegram.org/bot{telegram_bot_token}/answerCallbackQuery",
                json={
                    "callback_query_id": callback["id"],
                    "text": "Processing your request..."
                }
            )

            if action == "accept":
                reservation.status = "Confirmed"
                db.session.commit()
                
                update_telegram_message(
                    reservation_id,
                    f"✅ Accepted\n{original_text}",
                    {
                        "inline_keyboard": [
                            [
                                {"text": "Accepted", "callback_data": f"done_{reservation_id}"},
                                {"text": "Deny", "callback_data": f"done_{reservation_id}"}
                            ]
                        ]
                    }
                )
                
                with app.app_context():
                    send_email_async(
                        app.app_context(),
                        "Reservation Confirmed",
                        reservation.email,
                        f"Hello {reservation.name},<br><br>" +
                        f"Your reservation has been confirmed. We look forward to seeing you at {reservation.time} on {reservation.date}.<br><br>"
                    )
                
                return jsonify({"status": "confirmed"}), 200

            elif action == "deny":
                pending_denials[str(callback["message"]["chat"]["id"])] = reservation_id
                
                update_telegram_message(
                    reservation_id,
                    f"🔄 Processing Denial\n{original_text}",
                    {
                        "inline_keyboard": [
                            [
                                {"text": "Accept", "callback_data": "already_processing", "disabled": True},
                                {"text": "Processing...", "callback_data": "already_processing", "disabled": True}
                            ]
                        ]
                    }
                )
                
                requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": callback["message"]["chat"]["id"],
                        "text": "Please provide a reason for denial:",
                        "reply_to_message_id": callback["message"]["message_id"],
                        "reply_markup": {"force_reply": True}
                    }
                )
                
                return jsonify({"status": "awaiting_reason"}), 200

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
                    
                    original_text = data["message"]["reply_to_message"]["text"].replace("🔄 Processing Denial\n", "")
                    
                    update_telegram_message(
                        reservation.id,
                        f"❌ Denied\n{original_text}\nReason: {reason}",
                        {
                            "inline_keyboard": [
                                [
                                    {"text": "Accept", "callback_data": f"done_{reservation.id}"},
                                    {"text": "Denied", "callback_data": f"done_{reservation.id}"}
                                ]
                            ]
                        }
                    )
                    
                    # Update booking URL to include token
                    booking_url = f"https://snack.expo.dev/@beachbar/la-casita-booking?reservation_id={reservation.id}&token={reservation.token}"
                    with app.app_context():
                        send_email_async(
                            app.app_context(),
                            "Reservation Denied",
                            reservation.email,
                            f"""Hello {reservation.name},<br><br>
                            Sorry, we cannot take your reservation request for {reservation.date} at {reservation.time}.<br><br>
                            Reason: {reason}<br><br>
                            Click the button below to book a new time with your previous details:<br><br>
                            <a href="{booking_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Book A New Time</a><br><br>
                            Please contact us if you have any questions."""
                        )
                    
                    del pending_denials[chat_id]
                    return jsonify({"status": "denied"}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        logger.error(f"Callback error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route("/api/reservations/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id):
    try:
        # Get token from query parameter
        token = request.args.get('token')
        if not token:
            abort(401, "Token is required")

        reservation = Reservation.query.get_or_404(reservation_id)
        if reservation.token != token:
            abort(403, "Invalid token")

        return jsonify({
            "status": "success",
            "data": {
                "name": reservation.name,
                "email": reservation.email,
                "phone": reservation.phone,
                "date": reservation.date,
                "time": reservation.time,
                "diners": reservation.diners,
                "seating": reservation.seating,
                "pickup": reservation.pickup,
                "status": reservation.status,
                "denial_reason": reservation.denial_reason
            }
        })
    except Exception as e:
        logger.error(f"Failed to get reservation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Reservation not found or invalid token"
        }), 404

@app.route("/api/reservations", methods=["GET"])
def list_reservations():
    try:
        reservations = Reservation.query.order_by(Reservation.date, Reservation.time).all()
        return jsonify({
            "status": "success",
            "count": len(reservations),
            "data": [{
                "id": r.id,
                "name": r.name,
                "date": r.date,
                "time": r.time,
                "diners": r.diners,
                "status": r.status
            } for r in reservations]
        })
    except Exception as e:
        logger.error(f"Failed to list reservations: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "valid_endpoints": [
            "/api/reservations",
            "/api/reservations/<id>",
            "/telegram-callback",
            "/test"
        ]
    }), 404

@app.route("/test", methods=["GET"])
def test_endpoint():
    try:
        db.session.execute("SELECT 1")
        return jsonify({
            "status": "running",
            "service": "Reservation System",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        })
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return jsonify({
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)