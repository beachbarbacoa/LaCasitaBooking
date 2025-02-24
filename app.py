from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_mail import Mail, Message  # Corrected import
import os
import requests
import logging

app = Flask(__name__)
CORS(app)  # Allow requests from all origins

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email provider's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your email address
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')  # Default sender

mail = Mail(app)

# In-memory "database" (using a list)
reservations = []

# Telegram setup
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '7619634541:AAHoWrA378nyG8--LAE7LMwtlKcsozRyFTI')  # Replace with your bot token
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '6864600775')  # Replace with your chat ID

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

# Routes
@app.route("/")
def home():
    return "Welcome to the Reservation System!"

@app.route("/reservations", methods=["POST"])
def create_reservation():
    try:
        logger.debug("Request received at /reservations")  # Log when the endpoint is hit
        data = request.json
        logger.debug(f"Received data: {data}")  # Log the received data

        required_fields = ["name", "email", "phone", "time", "date", "diners", "seating", "pickup"]
        if not all(field in data for field in required_fields):
            abort(400, "Missing required fields")

        reservation = {
            "id": len(reservations) + 1,
            "name": data["name"],
            "email": data["email"],
            "phone": data["phone"],
            "time": data["time"],
            "date": data["date"],
            "diners": data["diners"],
            "seating": data["seating"],
            "pickup": data["pickup"],
            "status": "Pending"
        }

        reservations.append(reservation)

        # Send Telegram message
        message = (
            f"New Reservation:\n"
            f"Name: {reservation['name']}\n"
            f"Email: {reservation['email']}\n"
            f"Phone: {reservation['phone']}\n"
            f"Date: {reservation['date']}\n"
            f"Time: {reservation['time']}\n"
            f"Diners: {reservation['diners']}\n"
            f"Seating: {reservation['seating']}\n"
            f"Pickup: {reservation['pickup']}"
        )

        if send_telegram_message(message):
            # Send initial email confirmation
            try:
                msg = Message(
                    subject="Reservation Request Received",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[reservation['email']],
                    body=f"""
                    Thank you for your reservation request, {reservation['name']}!
                    Date: {reservation['date']}
                    Time: {reservation['time']}
                    Diners: {reservation['diners']}
                    Seating: {reservation['seating']}
                    Pickup: {reservation['pickup']}

                    We will notify you once your reservation is confirmed.
                    """
                )
                mail.send(msg)
                logger.debug("Initial email sent successfully!")
            except Exception as e:
                logger.error(f"Failed to send initial email: {e}")
                return jsonify({"message": "Reservation created but failed to send email", "error": str(e)})

            return jsonify({"message": "Reservation created and confirmation email sent", "reservation": reservation})
        else:
            return jsonify({"message": "Reservation created but failed to send Telegram message", "reservation": reservation})
    except Exception as e:
        logger.error(f"Error in create_reservation: {e}")  # Log any exceptions
        abort(500, "Internal server error")

@app.route("/confirm-reservation", methods=["POST"])
def confirm_reservation():
    try:
        data = request.json
        reservation_id = data.get("reservation_id")

        # Find the reservation
        reservation = next((r for r in reservations if r["id"] == reservation_id), None)
        if not reservation:
            abort(404, "Reservation not found")

        # Update reservation status
        reservation["status"] = "Confirmed"

        # Send confirmation email
        try:
            msg = Message(
                subject="Reservation Confirmed",
                sender=app.config['MAIL_USERNAME'],
                recipients=[reservation['email']],
                body=f"""
                Your reservation has been confirmed, {reservation['name']}!
                Date: {reservation['date']}
                Time: {reservation['time']}
                Diners: {reservation['diners']}
                Seating: {reservation['seating']}
                Pickup: {reservation['pickup']}

                We look forward to seeing you!
                """
            )
            mail.send(msg)
            logger.debug("Confirmation email sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

        return jsonify({"message": "Reservation confirmed and email sent", "reservation": reservation})
    except Exception as e:
        logger.error(f"Error in confirm_reservation: {e}")
        abort(500, "Internal server error")

@app.route("/reservations", methods=["GET"])
def get_reservations():
    return jsonify({"reservations": reservations})

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)