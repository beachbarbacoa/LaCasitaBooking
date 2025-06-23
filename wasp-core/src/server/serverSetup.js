import express from 'express';
import path from 'path';
import { api } from '@wasp/api';

export const setupServer = (app) => {
  // Serve API routes
  app.use(api);

  // Serve static files from React build
  const __dirname = path.resolve();
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  // Handle React routing - return all requests to React app
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/build', 'index.html'));
  });
};