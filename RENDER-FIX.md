# Render Deployment Fix

## 🚨 Current Issue

The Render deployment is failing with:
```
bash: build.sh: No such file or directory
```

## 🔧 Quick Fix

### Option 1: Use Updated Render Configuration (Recommended)

The `backend/deployment/render.yaml` file has been updated with the correct build commands:

```yaml
buildCommand: pip install -r backend/requirements.txt
startCommand: cd backend && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Option 2: Use the Simplified Build Script

If you prefer to use a build script, use `render-build.sh` instead:

1. **Update Render Service Configuration**:
   - Go to your Render dashboard
   - Select your backend service
   - Go to Settings → Build & Deploy
   - Change Build Command to: `bash render-build.sh`

2. **Or update the render.yaml**:
   ```yaml
   buildCommand: bash render-build.sh
   ```

### Option 3: Manual Service Setup

If the blueprint approach continues to have issues:

1. **Create Individual Services**:
   - Create a new Web Service
   - Connect your GitHub repository
   - Set Root Directory to: `backend`
   - Set Build Command to: `pip install -r requirements.txt`
   - Set Start Command to: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **Create Database**:
   - Create a new PostgreSQL database
   - Note the connection string

3. **Create Redis**:
   - Create a new Redis instance
   - Note the connection string

4. **Set Environment Variables**:
   ```bash
   PYTHONPATH=.
   DATABASE_URL=<your-postgres-connection-string>
   REDIS_URL=<your-redis-connection-string>
   JWT_SECRET_KEY=<generate-secure-key>
   OPENAI_API_KEY=<your-openai-key>
   TWILIO_ACCOUNT_SID=<your-twilio-sid>
   TWILIO_AUTH_TOKEN=<your-twilio-token>
   GOOGLE_CLIENT_ID=<your-google-client-id>
   GOOGLE_CLIENT_SECRET=<your-google-client-secret>
   ENVIRONMENT=production
   ```

## 🔍 Verification Steps

1. **Check Build Logs**:
   - Go to your service in Render dashboard
   - Click on "Logs" tab
   - Look for any error messages

2. **Test the Service**:
   - Once deployed, visit your service URL
   - Add `/docs` to see the API documentation
   - Test a simple endpoint like `/health`

3. **Check Dependencies**:
   - Ensure `backend/requirements.txt` exists
   - Verify all Python packages are listed

## 🚀 Alternative: Vercel Deployment

If Render continues to have issues, consider using Vercel for the frontend:

```bash
# Deploy frontend to Vercel
./deploy-vercel.sh frontend
```

## 📞 Support

If you continue to have issues:

1. Check the Render documentation: https://render.com/docs
2. Review the build logs for specific error messages
3. Test locally with Docker Compose first
4. Contact Render support with specific error details

---

**Note**: The updated configuration should resolve the build script issue. The key change is using `pip install -r backend/requirements.txt` instead of relying on a build script that Render couldn't find. 