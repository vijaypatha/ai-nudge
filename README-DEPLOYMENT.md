# AI Nudge - Deployment Setup

This document provides comprehensive deployment instructions for the AI Nudge application.

## 🎯 Deployment Options

### 1. Render (Recommended for Full Stack)
- **Best for**: Complete application stack with databases
- **Services**: Backend API, Celery workers, PostgreSQL, Redis, Frontend
- **Pros**: All-in-one solution, managed databases, easy scaling
- **Cons**: Higher cost for full stack

### 2. Vercel (Frontend) + External Backend
- **Best for**: Frontend deployment with external backend services
- **Services**: Frontend only (backend deployed elsewhere)
- **Pros**: Excellent frontend performance, global CDN
- **Cons**: Requires separate backend hosting

### 3. Hybrid Approach
- **Best for**: Optimized cost and performance
- **Services**: Frontend on Vercel, Backend on Render/Railway/Heroku
- **Pros**: Best of both worlds, cost-effective
- **Cons**: More complex setup

## 📁 Deployment Files

### Root Directory
- `build.sh` - Render build script
- `deploy-vercel.sh` - Vercel deployment script
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `README-DEPLOYMENT.md` - This file

### Backend Directory
- `backend/deployment/render.yaml` - Render blueprint configuration
- `backend/deployment/vercel.json` - Vercel backend configuration
- `backend/env.example` - Environment variables template

### Frontend Directory
- `frontend/vercel.json` - Vercel frontend configuration

## 🚀 Quick Start

### Option A: Render Full Stack Deployment

1. **Prepare Repository**
   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Prepare for deployment"
   git push
   ```

2. **Deploy to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Configure environment variables
   - Deploy

3. **Configure Environment Variables**
   ```bash
   # Backend Services
   DATABASE_URL=<from render database>
   REDIS_URL=<from render redis>
   JWT_SECRET_KEY=<generate secure key>
   OPENAI_API_KEY=<your-openai-key>
   TWILIO_ACCOUNT_SID=<your-twilio-sid>
   TWILIO_AUTH_TOKEN=<your-twilio-token>
   GOOGLE_CLIENT_ID=<your-google-client-id>
   GOOGLE_CLIENT_SECRET=<your-google-client-secret>
   
   # Frontend Service
   NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
   ```

### Option B: Vercel Frontend Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   ./deploy-vercel.sh frontend
   ```

3. **Configure Environment Variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   NEXT_PUBLIC_ENVIRONMENT=production
   ```

## 🔧 Environment Setup

### Required API Keys

1. **OpenAI API Key**
   - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Used for AI-powered features

2. **Twilio Credentials**
   - Get from [Twilio Console](https://console.twilio.com/)
   - Used for SMS/WhatsApp messaging

3. **Google OAuth**
   - Get from [Google Cloud Console](https://console.cloud.google.com/)
   - Used for user authentication

### Database Setup

#### PostgreSQL (Render)
- Automatically created by Render
- Connection string provided as environment variable

#### External PostgreSQL
```sql
CREATE DATABASE ai_nudge_db;
CREATE USER ai_nudge_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_nudge_db TO ai_nudge_user;
```

### Redis Setup

#### Redis (Render)
- Automatically created by Render
- Connection string provided as environment variable

#### External Redis
- Install Redis server
- Configure connection string: `redis://host:port`

## 📊 Service Architecture

### Render Deployment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Celery Worker  │
│  (Static Site)  │◄──►│   (Web Service) │◄──►│ (Background)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐
│  PostgreSQL DB  │    │   Redis Cache   │
│   (Database)    │    │   (Cache/Queue) │
└─────────────────┘    └─────────────────┘
```

### Vercel Deployment
```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Backend API   │
│  (Vercel)       │    │  (External)     │
└─────────────────┘    └─────────────────┘
```

## 🔍 Monitoring & Debugging

### Render Monitoring
```bash
# View service logs
render logs ai-nudge-backend
render logs ai-nudge-celery-worker
render logs ai-nudge-frontend

# SSH into service
render ssh ai-nudge-backend

# Check service status
render ps
```

### Vercel Monitoring
```bash
# View deployment logs
vercel logs

# Check deployment status
vercel ls

# View analytics
vercel analytics
```

## 🚨 Common Issues & Solutions

### 1. Database Connection Errors
**Symptoms**: 500 errors, database connection timeouts
**Solutions**:
- Verify `DATABASE_URL` is correct
- Check database service is running
- Ensure network connectivity

### 2. Redis Connection Errors
**Symptoms**: Celery worker failures, cache issues
**Solutions**:
- Verify `REDIS_URL` is correct
- Check Redis service is running
- Test Redis connectivity

### 3. CORS Errors
**Symptoms**: Frontend can't connect to backend
**Solutions**:
- Update `WEBSOCKET_ALLOWED_ORIGINS` with frontend URL
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS configuration in backend

### 4. Build Failures
**Symptoms**: Deployment fails during build
**Solutions**:
- Check dependency versions
- Verify all environment variables are set
- Review build logs for specific errors

## 🔐 Security Checklist

- [ ] All API keys are set as environment variables
- [ ] JWT secret key is secure and unique
- [ ] Database passwords are strong
- [ ] CORS is properly configured
- [ ] HTTPS is enabled for all services
- [ ] Environment variables are not committed to git
- [ ] Database access is restricted
- [ ] API rate limiting is configured

## 📈 Scaling Considerations

### Render Scaling
- **Starter Plan**: Good for development/testing
- **Standard Plan**: Recommended for production
- **Pro Plan**: For high-traffic applications

### Vercel Scaling
- **Hobby Plan**: Good for development
- **Pro Plan**: Recommended for production
- **Enterprise Plan**: For large-scale applications

## 🆘 Support Resources

### Documentation
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

### Community
- [Render Community](https://community.render.com/)
- [Vercel Community](https://github.com/vercel/vercel/discussions)

### Debugging Tools
- [Render Logs](https://dashboard.render.com/)
- [Vercel Analytics](https://vercel.com/analytics)
- [PostgreSQL Monitoring](https://www.postgresql.org/docs/current/monitoring.html)

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] All code is committed and pushed
- [ ] Environment variables are prepared
- [ ] API keys are obtained
- [ ] Database is set up
- [ ] Redis is configured

### Post-Deployment
- [ ] All services are running
- [ ] Environment variables are set
- [ ] Database migrations are applied
- [ ] Frontend can connect to backend
- [ ] Authentication is working
- [ ] SMS/WhatsApp integration is tested
- [ ] AI features are working
- [ ] Monitoring is set up

### Production Readiness
- [ ] SSL certificates are valid
- [ ] Domain is configured
- [ ] Backup strategy is in place
- [ ] Monitoring alerts are set
- [ ] Performance is acceptable
- [ ] Security audit is complete

---

**Note**: This deployment setup is designed to be flexible and scalable. Choose the deployment option that best fits your needs and budget. 