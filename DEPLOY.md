# Render Deployment Guide

## Prerequisites
1. Render.com account
2. GitHub repository for this project

## Deployment Steps
1. **Create PostgreSQL Database**:
   - Go to Render Dashboard → Databases → New PostgreSQL
   - Name: `lacasita-db`
   - Region: Ohio (free)
   - Database Name: `lacasita`
   - User: `lacasita_user`

2. **Get Connection String**:
   - After database creation, copy the "Internal Connection String"
   - Format: `postgres://user:password@host:port/dbname`

3. **Create Web Service**:
   - Go to Dashboard → Web Services → New Web Service
   - Connect your GitHub repository
   - Configure:
     - Name: `lacasita-booking`
     - Region: Ohio
     - Branch: `main`
     - Runtime: Docker
     - Dockerfile Path: `Dockerfile.prod`
     - Environment Variables:
       - `NODE_ENV`: production
       - `DATABASE_URL`: (paste connection string)

4. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically

## Post-Deployment
1. Access your app at: `https://lacasita-booking.onrender.com`
2. Test QR scanning with:
   - https://quickchart.io/qr?text=https://lacasita-booking.onrender.com/business/test/reserve

## Troubleshooting
- Check logs in Render Dashboard
- Verify database connection string
- Ensure all environment variables are set