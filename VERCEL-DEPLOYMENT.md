# Vercel Deployment Guide for AI Nudge

This guide provides step-by-step instructions for deploying the AI Nudge application to Vercel.

## 🚀 Quick Start

### Prerequisites
- ✅ Vercel CLI installed (`npm install -g vercel`)
- ✅ Logged into Vercel (`vercel login`)
- ✅ GitHub repository connected

## 📋 Deployment Options

### Option 1: Frontend Only (Recommended for most cases)
Deploy only the Next.js frontend to Vercel and use a separate backend service (Render, Railway, etc.)

### Option 2: Full Stack
Deploy both frontend and backend to Vercel (backend as serverless functions)

## 🔧 Step-by-Step Deployment

### Frontend Deployment

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Deploy to Vercel:**
   ```bash
   vercel --prod
   ```

3. **Configure environment variables in Vercel dashboard:**
   - `NEXT_PUBLIC_API_URL`: Your backend API URL
   - `NEXT_PUBLIC_ENVIRONMENT`: `production`

### Backend Deployment (Optional)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Copy Vercel configuration:**
   ```bash
   cp deployment/vercel.json .
   ```

3. **Deploy to Vercel:**
   ```bash
   vercel --prod
   ```

4. **Configure environment variables in Vercel dashboard:**
   ```bash
   DATABASE_URL=your-database-url
   REDIS_URL=your-redis-url
   JWT_SECRET_KEY=your-jwt-secret
   OPENAI_API_KEY=your-openai-key
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ENVIRONMENT=production
   ```

## 🛠️ Automated Deployment

Use the provided deployment script:

```bash
# Deploy frontend only
./deploy-vercel.sh frontend

# Deploy backend only
./deploy-vercel.sh backend

# Deploy both (default)
./deploy-vercel.sh all
```

## 🌐 Environment Variables

### Frontend Environment Variables
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Backend Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://host:port

# Authentication
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
```

## 🔧 Configuration Files

### Frontend (`frontend/vercel.json`)
```json
{
  "version": 2,
  "name": "ai-nudge-frontend",
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url",
    "NEXT_PUBLIC_ENVIRONMENT": "production"
  },
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "regions": ["iad1"],
  "public": true
}
```

### Backend (`backend/deployment/vercel.json`)
```json
{
  "version": 2,
  "name": "ai-nudge-backend",
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ],
  "env": {
    "PYTHONPATH": ".",
    "ENVIRONMENT": "production"
  },
  "functions": {
    "api/main.py": {
      "maxDuration": 30
    }
  },
  "regions": ["iad1"]
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check dependency versions
   - Verify all environment variables are set
   - Review build logs for specific errors

2. **API Connection Issues**
   - Verify `NEXT_PUBLIC_API_URL` is correct
   - Check CORS configuration
   - Ensure backend is accessible

3. **Database Connection Errors**
   - Verify `DATABASE_URL` is correctly set
   - Check database service is running
   - Ensure network connectivity

### Debug Commands

```bash
# Check Vercel deployment status
vercel ls

# View deployment logs
vercel logs

# Check environment variables
vercel env ls

# Remove deployment
vercel remove
```

## 📊 Monitoring

### Vercel Analytics
- Monitor frontend performance
- Track user interactions
- Analyze page load times

### Vercel Dashboard
- View deployment history
- Monitor function execution
- Check error rates

## 🔐 Security Considerations

1. **Environment Variables**: Never commit sensitive keys to version control
2. **API Keys**: Rotate keys regularly and use least privilege
3. **HTTPS**: All production traffic uses HTTPS automatically
4. **CORS**: Configure CORS properly for production domains

## 📈 Scaling

### Vercel Scaling
- Automatically scales based on traffic
- Consider upgrading to Pro plan for more features
- Use Edge Functions for better performance

## 🆘 Support

For deployment issues:

1. Check the Vercel dashboard logs
2. Verify environment variables
3. Test locally with Docker Compose
4. Review the troubleshooting section above
5. Contact Vercel support with specific error messages

---

**Note**: This deployment guide assumes you have the necessary API keys and external service accounts set up. Make sure to configure all external integrations before deploying to production. 