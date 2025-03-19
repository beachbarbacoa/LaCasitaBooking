const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const sgMail = require('@sendgrid/mail');
const TelegramBot = require('node-telegram-bot-api');

const app = express();
const PORT = process.env.PORT || 3000;
const bot = new TelegramBot('YOUR_TELEGRAM_BOT_TOKEN', { polling: true });

// Connect to MongoDB
mongoose.connect('YOUR_MONGODB_URI', { useNewUrlParser: true, useUnifiedTopology: true });

// Reservation Schema
const reservationSchema = new mongoose.Schema({
  name: String,
  email: String,
  phone: String,
  date: String,
  time: String,
  diners: String,
  seating: String,
  pickup: String,
  status: { type: String, default: 'Pending' }, // New field
  denialReason: String, // Optional: Store the reason for denial
});

const Reservation = mongoose.model('Reservation', reservationSchema);

// Middleware
app.use(bodyParser.json());

// SendGrid setup
sgMail.setApiKey('YOUR_SENDGRID_API_KEY');

// Function to send confirmation email
function sendConfirmationEmail(email, reservation) {
  const msg = {
    to: email,
    from: 'your-email@example.com', // Replace with your email
    subject: 'Reservation Confirmed',
    html: `
      <p>Your reservation has been confirmed!</p>
      <p>Details:</p>
      <ul>
        <li>Name: ${reservation.name}</li>
        <li>Email: ${reservation.email}</li>
        <li>Phone: ${reservation.phone}</li>
        <li>Date: ${reservation.date}</li>
        <li>Time: ${reservation.time}</li>
        <li>Diners: ${reservation.diners}</li>
        <li>Seating: ${reservation.seating}</li>
        <li>Pickup: ${reservation.pickup}</li>
      </ul>
    `,
  };

  sgMail.send(msg);
}

// Function to send denial email with "Request New Time" button
function sendDenialEmail(email, reservation, reason) {
  const msg = {
    to: email,
    from: 'your-email@example.com', // Replace with your email
    subject: 'Reservation Denied',
    html: `
      <p>We regret to inform you that your reservation has been denied.</p>
      <p>Reason: ${reason}</p>
      <p>Click the button below to request a new time:</p>
      <a href="https://yourapp.com/reservation?reservationId=${reservation._id}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">
        Request New Time
      </a>
    `,
  };

  sgMail.send(msg);
}

// Function to send reservation details to Telegram with buttons
function sendReservationToOperator(chatId, reservation) {
  const message = `New Reservation Request:\n\nName: ${reservation.name}\nEmail: ${reservation.email}\nPhone: ${reservation.phone}\nDate: ${reservation.date}\nTime: ${reservation.time}\nDiners: ${reservation.diners}\nSeating: ${reservation.seating}\nPickup: ${reservation.pickup}`;

  const options = {
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'Accept Reservation', callback_data: `accept_${reservation._id}` },
          { text: 'Deny Reservation', callback_data: `deny_${reservation._id}` },
        ],
      ],
    },
  };

  bot.sendMessage(chatId, message, options);
}

// Handle new reservations
app.post('/reservations', async (req, res) => {
  const reservation = req.body;

  // Save the reservation to the database
  const savedReservation = await Reservation.create(reservation);

  // Send the reservation to the restaurant/tour operator via Telegram
  const operatorChatId = 'RESTAURANT_OR_TOUR_OPERATOR_CHAT_ID'; // Replace with the actual chat ID
  sendReservationToOperator(operatorChatId, savedReservation);

  res.status(201).json({ message: 'Reservation request sent successfully!' });
});

// Handle Telegram button clicks
bot.on('callback_query', async (callbackQuery) => {
  const chatId = callbackQuery.message.chat.id;
  const data = callbackQuery.data;
  const reservationId = data.split('_')[1];

  // Fetch the reservation details from the database
  const reservation = await Reservation.findById(reservationId);

  if (data.startsWith('accept')) {
    // Handle acceptance
    bot.sendMessage(chatId, `Reservation ${reservationId} has been accepted.`);
    await Reservation.findByIdAndUpdate(reservationId, { status: 'Confirmed' });

    // Send confirmation email to the user
    sendConfirmationEmail(reservation.email, reservation);
  } else if (data.startsWith('deny')) {
    // Handle denial
    bot.sendMessage(chatId, `Please provide a reason for denying reservation ${reservationId}:`);
    bot.once('message', async (msg) => {
      const reason = msg.text;
      bot.sendMessage(chatId, `Reservation ${reservationId} has been denied. Reason: ${reason}`);
      await Reservation.findByIdAndUpdate(reservationId, { status: 'Denied', denialReason: reason });

      // Send denial email to the user with a "Request New Time" button
      sendDenialEmail(reservation.email, reservation, reason);
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});