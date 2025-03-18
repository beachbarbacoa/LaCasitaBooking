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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
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

# Helper function to send Telegram message
def send_telegram_message(message):
    try:
        logger.debug("Sending Telegram message...")  # Log when sending a message
        logger.debug(f"Message content: {message}")  # Log the message content

        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": message
        }
        response = requests.post(url, json=payload)  # Fixed missing parenthesis
        response.raise_for_status()  # Raise an error for bad status codes
        logger.debug("Message sent successfully!")  # Log success
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")  # Log any exceptions
        return False

# Helper function to send email using SendGrid SMTP Relay
def send_email(subject, recipient, body):
    try:
        # Email configuration
        sender_email = os.getenv('MAIL_USERNAME')  # This should still be 'apikey'
        sender_password = os.getenv('MAIL_PASSWORD')  # Your SendGrid API key
        smtp_server = app.config['MAIL_SERVER']
        smtp_port = app.config['MAIL_PORT']
        from_email = os.getenv('SENDER_EMAIL')  # Get the sender email from environment variables

        logger.debug(f"Attempting to send email to {recipient} using SendGrid SMTP...")
        logger.debug(f"SMTP Server: {smtp_server}, Port: {smtp_port}")
        logger.debug(f"Sender Email: {from_email}")

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = from_email  # Use the environment variable
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logger.debug("Starting TLS...")
            server.starttls()
            logger.debug("Logging into SMTP server...")
            server.login(sender_email, sender_password)
            logger.debug("Sending email...")
            server.sendmail(from_email, recipient, msg.as_string())  # Use the environment variable
        logger.debug("Email sent successfully!")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return False

# Routes
@app.route("/")
def home():
    return "Welcome to the Reservation System!"

@app.route("/test-email")
def test_email():
    try:
        send_email(
            subject="Test Email",
            recipient="colincorreia@me.com",  # Replace with your email
            body="This is a test email."
        )
        return "Test email sent successfully!"
    except Exception as e:
        return f"Failed to send test email: {e}"

@app.route("/reservations", methods=["POST"])
def create_reservation():
    try:
        logger.debug("Request received at /reservations")  # Log when the endpoint is hit
        data = request.json
        logger.debug(f"Received data: {data}")  # Log the received data

        required_fields = ["name", "email", "phone", "time", "date", "diners", "seating", "pickup"]
        if not all(field in data for field in required_fields):
            abort(400, "Missing required fields")

        # Create a new reservation
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

        # Add the reservation to the database
        db.session.add(reservation)
        db.session.commit()

        # Send Telegram message
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

        if send_telegram_message(message):
            # Send initial email confirmation
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
        logger.error(f"Error in create_reservation: {e}")  # Log any exceptions
        abort(500, "Internal server error")

@app.route("/confirm-reservation", methods=["POST"])
def confirm_reservation():
    try:
        data = request.json
        reservation_id = data.get("reservation_id")

        # Find the reservation
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            abort(404, "Reservation not found")

        # Update reservation status
        reservation.status = "Confirmed"
        db.session.commit()

        # Send confirmation email
        email_sent = send_email(
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
        if email_sent:
            return jsonify({"message": "Reservation confirmed and email sent", "reservation": {
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
            return jsonify({"message": "Reservation confirmed but failed to send email", "reservation": {
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
        logger.error(f"Error in confirm_reservation: {e}")
        abort(500, "Internal server error")

@app.route("/reservations", methods=["GET"])
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify({"reservations": [
        {
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
        }
        for reservation in reservations
    ]})

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)