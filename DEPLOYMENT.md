# AI Nudge Deployment Guide

This guide covers deployment options for the AI Nudge application on both Render and Vercel platforms.

## 🚀 Quick Start

### Option 1: Render Deployment (Recommended for Full Stack)

Render provides a complete solution for deploying the entire application stack including databases.

### Option 2: Vercel Deployment

Vercel is excellent for frontend deployment and can be combined with other backend services.

## 📋 Prerequisites

- GitHub repository with the AI Nudge codebase
- API keys for external services (OpenAI, Twilio, Google OAuth)
- Render account (for full stack deployment)
- Vercel account (for frontend deployment)

## 🔧 Environment Variables

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here

# External APIs
OPENAI_API_KEY=your-openai-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Application
ENVIRONMENT=production
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## 🎯 Render Deployment

### Step 1: Connect Repository

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Select the repository containing the AI Nudge codebase

### Step 2: Deploy with Blueprint

1. Render will automatically detect the `backend/deployment/render.yaml` file
2. Configure the following services:
   - **ai-nudge-backend**: Main API service
   - **ai-nudge-celery-worker**: Background task processing
   - **ai-nudge-celery-beat**: Scheduled task processing
   - **ai-nudge-frontend**: Static frontend site
   - **ai-nudge-db**: PostgreSQL database
   - **ai-nudge-redis**: Redis cache

### Step 3: Configure Environment Variables

For each service, add the required environment variables:

#### Backend Services (ai-nudge-backend, ai-nudge-celery-worker, ai-nudge-celery-beat)

```bash
PYTHONPATH=./backend
DATABASE_URL=<from database service>
REDIS_URL=<from redis service>
JWT_SECRET_KEY=<generate or set manually>
OPENAI_API_KEY=<your-openai-key>
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
ENVIRONMENT=production
```

#### Frontend Service (ai-nudge-frontend)

```bash
NEXT_PUBLIC_API_URL=https://ai-nudge-backend.onrender.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Step 4: Deploy

1. Click "Create Blueprint Instance"
2. Render will automatically build and deploy all services
3. Monitor the deployment logs for any issues

## 🌐 Vercel Deployment

### Frontend Deployment

#### Step 1: Connect Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the `frontend` directory as the root

#### Step 2: Configure Build Settings

- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

#### Step 3: Set Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_ENVIRONMENT=production
```

#### Step 4: Deploy

1. Click "Deploy"
2. Vercel will build and deploy your frontend
3. Your site will be available at `https://your-project.vercel.app`

### Backend Deployment (Optional)

If you want to deploy the backend on Vercel as well:

#### Step 1: Create Backend Project

1. Create a new Vercel project
2. Select the `backend` directory as root
3. Use the `vercel.json` configuration in `backend/deployment/`

#### Step 2: Configure Environment Variables

Add all the required environment variables for the backend.

## 🔄 Database Setup

### PostgreSQL (Render)

The PostgreSQL database will be automatically created by Render. The connection string will be provided as an environment variable.

### Manual Database Setup (if needed)

```sql
-- Create database
CREATE DATABASE ai_nudge_db;

-- Create user
CREATE USER ai_nudge_user WITH PASSWORD 'your-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_nudge_db TO ai_nudge_user;
```

## 🔧 Build Scripts

### Render Build Scripts

- **`render-build.sh`**: Simplified build script for Render deployment
- **`build.sh`**: Comprehensive build script with error handling

### Vercel Build Scripts

- **`deploy-vercel.sh`**: Automated Vercel deployment script

### Usage

```bash
# For Render deployment
chmod +x render-build.sh
./render-build.sh

# For Vercel deployment
chmod +x deploy-vercel.sh
./deploy-vercel.sh frontend
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `DATABASE_URL` is correctly set
   - Check database service is running
   - Ensure network connectivity

2. **Redis Connection Errors**
   - Verify `REDIS_URL` is correctly set
   - Check Redis service is running

3. **Build Failures**
   - Check dependency versions in `requirements.txt` and `package.json`
   - Verify all environment variables are set
   - Review build logs for specific errors

4. **CORS Errors**
   - Ensure `WEBSOCKET_ALLOWED_ORIGINS` includes your frontend URL
   - Check API URL configuration in frontend

### Debug Commands

```bash
# Check backend logs
render logs ai-nudge-backend

# Check worker logs
render logs ai-nudge-celery-worker

# Check frontend logs
render logs ai-nudge-frontend

# SSH into service (if needed)
render ssh ai-nudge-backend
```

## 📊 Monitoring

### Render Dashboard

- Monitor service health and performance
- View logs in real-time
- Check resource usage
- Set up alerts for downtime

### Vercel Analytics

- Monitor frontend performance
- Track user interactions
- Analyze page load times

## 🔐 Security Considerations

1. **Environment Variables**: Never commit sensitive keys to version control
2. **Database Security**: Use strong passwords and limit access
3. **API Keys**: Rotate keys regularly and use least privilege
4. **HTTPS**: All production traffic should use HTTPS
5. **CORS**: Configure CORS properly for production domains

## 📈 Scaling

### Render Scaling

- Upgrade to higher plans for more resources
- Enable auto-scaling for web services
- Monitor resource usage and adjust accordingly

### Vercel Scaling

- Vercel automatically scales based on traffic
- Consider upgrading to Pro plan for more features
- Use Edge Functions for better performance

## 🆘 Support

For deployment issues:

1. Check the service logs
2. Verify environment variables
3. Test locally with Docker Compose
4. Review the troubleshooting section above
5. Contact support with specific error messages

---

**Note**: This deployment guide assumes you have the necessary API keys and external service accounts set up. Make sure to configure all external integrations before deploying to production. 