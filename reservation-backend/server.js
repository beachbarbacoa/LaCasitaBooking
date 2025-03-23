const express = require('express');
const { Sequelize, DataTypes } = require('sequelize');
const bodyParser = require('body-parser');
const sgMail = require('@sendgrid/mail');
const TelegramBot = require('node-telegram-bot-api');

const app = express();
const PORT = process.env.PORT || 3000;
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// Initialize Sequelize with SQLite
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: './database.sqlite', // SQLite database file
});

// Define the Reservation model
const Reservation = sequelize.define('Reservation', {
  name: { type: DataTypes.STRING, allowNull: false },
  email: { type: DataTypes.STRING, allowNull: false },
  phone: { type: DataTypes.STRING, allowNull: false },
  date: { type: DataTypes.STRING, allowNull: false },
  time: { type: DataTypes.STRING, allowNull: false },
  diners: { type: DataTypes.STRING, allowNull: false },
  seating: { type: DataTypes.STRING, allowNull: false },
  pickup: { type: DataTypes.STRING, allowNull: false },
  status: { type: DataTypes.STRING, defaultValue: 'Pending' }, // New field
  denialReason: { type: DataTypes.STRING }, // Optional: Store the reason for denial
});

// Sync the database
sequelize.sync()
  .then(() => console.log('Database synced successfully'))
  .catch((err) => console.error('Failed to sync database:', err));

// SendGrid setup
sgMail.setApiKey(process.env.SENDGRID_API_KEY); // Replace with your SendGrid API key

// Middleware
app.use(bodyParser.json());

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
      <a href="https://yourapp.com/reservation?reservationId=${reservation.id}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">
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
          { text: 'Accept Reservation', callback_data: `accept_${reservation.id}` },
          { text: 'Deny Reservation', callback_data: `deny_${reservation.id}` },
        ],
      ],
    },
  };

  console.log('Sending Telegram message with options:', JSON.stringify(options, null, 2)); // Log the options

  bot.sendMessage(chatId, message, options)
    .then(() => console.log('Telegram message sent successfully'))
    .catch((error) => console.error('Failed to send Telegram message:', error));
}

// Handle new reservations
app.post('/reservations', async (req, res) => {
  const reservation = req.body;

  try {
    // Save the reservation to the database
    const savedReservation = await Reservation.create(reservation);
    console.log('Reservation saved:', savedReservation);

    // Send the reservation to the restaurant/tour operator via Telegram
    const operatorChatId = process.env.TELEGRAM_CHAT_ID; // Replace with the actual chat ID
    sendReservationToOperator(operatorChatId, savedReservation);

    res.status(201).json({ message: 'Reservation request sent successfully!', reservation: savedReservation });
  } catch (error) {
    console.error('Error saving reservation:', error);
    res.status(500).json({ message: 'Failed to submit reservation', error: error.message });
  }
});

// Endpoint to list all reservations
app.get('/reservations', async (req, res) => {
  try {
    const reservations = await Reservation.findAll();
    res.status(200).json(reservations);
  } catch (error) {
    console.error('Error fetching reservations:', error);
    res.status(500).json({ message: 'Failed to fetch reservations', error: error.message });
  }
});

// Test endpoint for Telegram bot
app.get('/test-telegram', (req, res) => {
  const chatId = process.env.TELEGRAM_CHAT_ID; // Use the chat ID from Render environment variables
  const message = 'Test message with inline buttons';
  const options = {
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'Accept', callback_data: 'accept' },
          { text: 'Deny', callback_data: 'deny' },
        ],
      ],
    },
  };

  console.log('Sending test message to Telegram with options:', JSON.stringify(options, null, 2));

  bot.sendMessage(chatId, message, options)
    .then(() => {
      console.log('Test message sent successfully!');
      res.status(200).json({ message: 'Test message sent successfully!' });
    })
    .catch((error) => {
      console.error('Failed to send test message:', error);
      res.status(500).json({ message: 'Failed to send test message', error: error.message });
    });
});

// Handle Telegram button clicks
bot.on('callback_query', async (callbackQuery) => {
  const chatId = callbackQuery.message.chat.id;
  const data = callbackQuery.data;
  const reservationId = data.split('_')[1];

  // Fetch the reservation details from the database
  const reservation = await Reservation.findByPk(reservationId);

  if (data.startsWith('accept')) {
    // Handle acceptance
    bot.sendMessage(chatId, `Reservation ${reservationId} has been accepted.`);
    await Reservation.update({ status: 'Confirmed' }, { where: { id: reservationId } });

    // Send confirmation email to the user
    sendConfirmationEmail(reservation.email, reservation);
  } else if (data.startsWith('deny')) {
    // Handle denial
    bot.sendMessage(chatId, `Please provide a reason for denying reservation ${reservationId}:`);
    bot.once('message', async (msg) => {
      const reason = msg.text;
      bot.sendMessage(chatId, `Reservation ${reservationId} has been denied. Reason: ${reason}`);
      await Reservation.update({ status: 'Denied', denialReason: reason }, { where: { id: reservationId } });

      // Send denial email to the user with a "Request New Time" button
      sendDenialEmail(reservation.email, reservation, reason);
    });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});