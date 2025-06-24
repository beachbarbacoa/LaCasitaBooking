import express from 'express';
import path from 'path';
import { api } from '@wasp/api';
import fs from 'fs';

export const setupServer = (app) => {
  console.log('[SERVER] Initializing server setup');
  
  // Serve API routes
  app.use(api);
  console.log('[SERVER] API routes registered');

  // Use absolute path for production build
  const clientBuildPath = path.resolve(process.cwd(), 'build');
  console.log(`[SERVER] Static file path: ${clientBuildPath}`);
  
  // Verify build directory exists
  try {
    const files = fs.readdirSync(clientBuildPath);
    console.log(`[SERVER] Found ${files.length} files in build directory`);
    if (files.length === 0) {
      console.error('[ERROR] Build directory is empty!');
    }
  } catch (err) {
    console.error('[ERROR] Failed to access build directory:', err.message);
  }

  // Serve static files
  app.use(express.static(clientBuildPath));
  
  // Serve index.html for all routes
  app.get('*', (req, res) => {
    console.log(`[ROUTING] Serving index.html for: ${req.path}`);
    res.sendFile(path.join(clientBuildPath, 'index.html'));
  });
  console.log('[SERVER] Static file serving enabled');
  
  // Health check endpoint
  app.get('/health', (req, res) => {
    console.log('[HEALTH] Status check received');
    res.json({
      status: 'ok',
      version: process.env.npm_package_version,
      buildPath: clientBuildPath
    });
  });

  // Handle React routing - return all requests to React app
  app.get('*', (req, res) => {
    console.log(`[ROUTING] Serving index.html for: ${req.path}`);
    res.sendFile(path.join(clientBuildPath, 'index.html'));
  });
  
  console.log('[SERVER] Setup complete');
};