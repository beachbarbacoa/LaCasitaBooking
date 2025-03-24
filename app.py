from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Reservation model
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

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Telegram setup
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Dictionary to track pending denials {chat_id: reservation_id}
denial_requests = {}

# Helper function to send email
def send_email(subject, recipient, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        logger.debug("Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

# Send Telegram message with buttons
def send_telegram_message(reservation):
    message = (
        f"New Reservation:\n"
        f"Name: {reservation.name}\n"
        f"Email: {reservation.email}\n"
        f"Phone: {reservation.phone}\n"
        f"Date: {reservation.date}\n"
        f"Time: {reservation.time}\n"
        f"Diners: {reservation.diners}\n"
        f"Seating: {reservation.seating}\n"
        f"Pickup: {reservation.pickup}"
    )
    
    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "Accept", "callback_data": f"accept_{reservation.id}"},
                    {"text": "Deny", "callback_data": f"deny_{reservation.id}"}
                ]
            ]
        }
    }
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
            json=payload
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram message failed: {e}")
        return False

# Handle Telegram callbacks
@app.route("/telegram-callback", methods=["POST"])
def telegram_callback():
    try:
        data = request.json
        logger.debug(f"Received callback: {data}")
        
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback["data"]
            reservation_id = int(callback_data.split("_")[1])
            chat_id = str(callback["message"]["chat"]["id"])
            
            if callback_data.startswith("accept"):
                reservation = Reservation.query.get(reservation_id)
                if reservation:
                    reservation.status = "Confirmed"
                    db.session.commit()
                    send_email(
                        "Reservation Confirmed",
                        reservation.email,
                        f"Your reservation for {reservation.date} at {reservation.time} has been confirmed!"
                    )
                    return jsonify({"status": "success"})
            
            elif callback_data.startswith("deny"):
                reservation = Reservation.query.get(reservation_id)
                if reservation:
                    reservation.status = "Denied"
                    db.session.commit()
                    denial_requests[chat_id] = reservation_id
                    
                    requests.post(
                        f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": "Please provide a reason for denial:",
                            "reply_to_message_id": callback["message"]["message_id"],
                            "reply_markup": {"force_reply": True}
                        }
                    )
                    return jsonify({"status": "awaiting_reason"})
        
        elif "message" in data and "reply_to_message" in data["message"]:
            message = data["message"]
            chat_id = str(message["chat"]["id"])
            
            if chat_id in denial_requests:
                reservation = Reservation.query.get(denial_requests[chat_id])
                if reservation:
                    reason = message.get("text", "No reason provided")
                    reservation.denial_reason = reason
                    db.session.commit()
                    
                    send_email(
                        "Reservation Denied",
                        reservation.email,
                        f"Your reservation was denied. Reason: {reason}\n\n"
                        f"Details:\nDate: {reservation.date}\nTime: {reservation.time}"
                    )
                    
                    del denial_requests[chat_id]
                    return jsonify({"status": "success"})
        
        return jsonify({"status": "ignored"}), 200
    
    except Exception as e:
        logger.error(f"Callback error: {e}")
        abort(500, "Internal server error")

# Create new reservation
@app.route("/reservations", methods=["POST"])
def create_reservation():
    try:
        data = request.json
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
        
        # Initialize webhook on first request
        if not hasattr(app, 'webhook_initialized'):
            try:
                webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/telegram-callback"
                requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/setWebhook",
                    json={"url": webhook_url}
                )
                app.webhook_initialized = True
                logger.debug("Telegram webhook initialized")
            except Exception as e:
                logger.error(f"Webhook setup failed: {e}")

        telegram_sent = send_telegram_message(reservation)
        email_sent = send_email(
            "Reservation Request Received",
            reservation.email,
            f"Your reservation request for {reservation.date} at {reservation.time} has been received."
        )
        
        return jsonify({
            "id": reservation.id,
            "telegram_sent": telegram_sent,
            "email_sent": email_sent
        })
    
    except Exception as e:
        logger.error(f"Reservation error: {e}")
        abort(400, "Invalid reservation data")

# Create tables and initialize
with app.app_context():
    db.create_all()
    try:
        webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/telegram-callback"
        requests.post(
            f"https://api.telegram.org/bot{telegram_bot_token}/setWebhook",
            json={"url": webhook_url}
        )
        logger.debug("Initial webhook setup attempted")
    except Exception as e:
        logger.error(f"Initial webhook setup failed: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)