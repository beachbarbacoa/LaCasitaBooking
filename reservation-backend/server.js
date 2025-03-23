const express = require('express');
const TelegramBot = require('node-telegram-bot-api');

const app = express();
const PORT = process.env.PORT || 3000;
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

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

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});