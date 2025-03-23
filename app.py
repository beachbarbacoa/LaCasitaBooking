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
CORS(app)  # Allow requests from all origins

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Use PostgreSQL URL from Render
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
    denial_reason = db.Column(db.String(200))  # New field for denial reason

# Create the database and tables
with app.app_context():
    db.create_all()

# Email configuration for SendGrid
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587  # Use port 587 for TLS (or 2525 if 587 is blocked)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Should be 'apikey'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your SendGrid API key

# Telegram setup
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')  # Replace with your bot token
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')  # Replace with your chat ID

# Global variable to track pending denials
pending_denial = None

# Helper function to send Telegram message with inline buttons
def send_telegram_message_with_buttons(reservation):
    try:
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

        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
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
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.debug("Telegram message with buttons sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message with buttons: {e}")
        return False

# Helper function to send email using SendGrid SMTP Relay
def send_email(subject, recipient, body):
    try:
        sender_email = os.getenv('MAIL_USERNAME')
        sender_password = os.getenv('MAIL_PASSWORD')
        smtp_server = app.config['MAIL_SERVER']
        smtp_port = app.config['MAIL_PORT']
        from_email = os.getenv('SENDER_EMAIL')

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(from_email, recipient, msg.as_string())
        logger.debug("Email sent successfully!")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return False

# Route to handle Telegram callback queries
@app.route("/telegram-callback", methods=["POST"])
def telegram_callback():
    try:
        data = request.json
        callback_query = data.get("callback_query")
        if not callback_query:
            abort(400, "No callback query found")

        callback_data = callback_query.get("data")
        reservation_id = int(callback_data.split("_")[1])
        reservation = Reservation.query.get(reservation_id)

        if not reservation:
            abort(404, "Reservation not found")

        if callback_data.startswith("accept"):
            # Handle acceptance
            reservation.status = "Confirmed"
            db.session.commit()

            # Send confirmation email
            send_email(
                subject="Reservation Confirmed",
                recipient=reservation.email,
                body=f"""
                Your reservation has been confirmed, {reservation.name}!
                Date: {reservation.date}
                Time: {reservation.time}
                Diners: {reservation.diners}
                Seating: {reservation.seating}
                Pickup: {reservation.pickup}

                We look forward to seeing you!
                """
            )
            return jsonify({"message": "Reservation confirmed and email sent"})

        elif callback_data.startswith("deny"):
            # Handle denial
            reservation.status = "Denied"
            db.session.commit()

            # Prompt the operator for a reason
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": telegram_chat_id,
                "text": "Please provide a reason for denying this reservation:",
                "reply_markup": {
                    "force_reply": True  # Force the operator to reply
                }
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()

            # Store the reservation ID in the operator's session
            global pending_denial
            pending_denial = reservation_id

            return jsonify({"message": "Prompted operator for denial reason"})

        else:
            abort(400, "Invalid callback data")

    except Exception as e:
        logger.error(f"Error in telegram_callback: {e}")
        abort(500, "Internal server error")

# Route to handle operator's reply with denial reason
@app.route("/telegram-reply", methods=["POST"])
def telegram_reply():
    try:
        logger.debug("Received reply data: %s", request.json)  # Log the incoming request
        data = request.json
        message = data.get("message")
        if not message:
            logger.error("No message found in request")
            abort(400, "No message found")

        # Check if this is a reply to a denial prompt
        global pending_denial
        if not pending_denial:
            logger.error("No pending denial found")
            abort(400, "No pending denial found")

        # Get the reservation
        reservation = Reservation.query.get(pending_denial)
        if not reservation:
            logger.error("Reservation not found for ID: %s", pending_denial)
            abort(404, "Reservation not found")

        # Update the reservation with the denial reason
        reservation.denial_reason = message.get("text")
        db.session.commit()
        logger.debug("Denial reason updated for reservation ID: %s", pending_denial)

        # Send denial email to the guest
        email_sent = send_email(
            subject="Reservation Denied",
            recipient=reservation.email,
            body=f"""
            We regret to inform you that your reservation has been denied.
            Reason: {reservation.denial_reason}

            Date: {reservation.date}
            Time: {reservation.time}
            Diners: {reservation.diners}
            Seating: {reservation.seating}
            Pickup: {reservation.pickup}

            Please try booking a different time.
            """
        )
        if email_sent:
            logger.debug("Denial email sent successfully")
        else:
            logger.error("Failed to send denial email")

        # Clear the pending denial
        pending_denial = None

        return jsonify({"message": "Denial reason received and email sent"})

    except Exception as e:
        logger.error(f"Error in telegram_reply: {e}")
        abort(500, "Internal server error")

# Routes
@app.route("/")
def home():
    return "Welcome to the Reservation System!"

@app.route("/reservations", methods=["POST"])
def create_reservation():
    try:
        data = request.json
        required_fields = ["name", "email", "phone", "time", "date", "diners", "seating", "pickup"]
        if not all(field in data for field in required_fields):
            abort(400, "Missing required fields")

        reservation = Reservation(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            time=data["time"],
            date=data["date"],
            diners=data["diners"],
            seating=data["seating"],
            pickup=data["pickup"],
            status="Pending"
        )

        db.session.add(reservation)
        db.session.commit()

        if send_telegram_message_with_buttons(reservation):
            email_sent = send_email(
                subject="Reservation Request Received",
                recipient=reservation.email,
                body=f"""
                Thank you for your reservation request, {reservation.name}!
                Date: {reservation.date}
                Time: {reservation.time}
                Diners: {reservation.diners}
                Seating: {reservation.seating}
                Pickup: {reservation.pickup}

                We will notify you once your reservation is confirmed.
                """
            )
            if email_sent:
                return jsonify({"message": "Reservation created and confirmation email sent", "reservation": {
                    "id": reservation.id,
                    "name": reservation.name,
                    "email": reservation.email,
                    "phone": reservation.phone,
                    "time": reservation.time,
                    "date": reservation.date,
                    "diners": reservation.diners,
                    "seating": reservation.seating,
                    "pickup": reservation.pickup,
                    "status": reservation.status
                }})
            else:
                return jsonify({"message": "Reservation created but failed to send email", "reservation": {
                    "id": reservation.id,
                    "name": reservation.name,
                    "email": reservation.email,
                    "phone": reservation.phone,
                    "time": reservation.time,
                    "date": reservation.date,
                    "diners": reservation.diners,
                    "seating": reservation.seating,
                    "pickup": reservation.pickup,
                    "status": reservation.status
                }})
        else:
            return jsonify({"message": "Reservation created but failed to send Telegram message", "reservation": {
                "id": reservation.id,
                "name": reservation.name,
                "email": reservation.email,
                "phone": reservation.phone,
                "time": reservation.time,
                "date": reservation.date,
                "diners": reservation.diners,
                "seating": reservation.seating,
                "pickup": reservation.pickup,
                "status": reservation.status
            }})
    except Exception as e:
        logger.error(f"Error in create_reservation: {e}")
        abort(500, "Internal server error")

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)