const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Simple test route
app.get('/test', (req, res) => {
  res.status(200).json({ message: 'Test route is working!' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});