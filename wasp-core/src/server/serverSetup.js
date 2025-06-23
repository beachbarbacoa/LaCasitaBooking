import express from 'express';
import path from 'path';
import { api } from '@wasp/api';

export const setupServer = (app) => {
  // Serve API routes
  app.use(api);

  // Serve static files from React build
  // Use absolute path for production build
  const clientBuildPath = path.resolve(process.cwd(), 'client/build');
  app.use(express.static(clientBuildPath));
  
  // Handle React routing - return all requests to React app
  app.get('*', (req, res) => {
    res.sendFile(path.join(clientBuildPath, 'index.html'));
  });
};