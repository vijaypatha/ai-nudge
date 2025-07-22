# Render Build Command Fix

## 🚨 Current Issue

Render is still trying to run `bash build.sh` even though we've updated the `render.yaml` file. This suggests that:

1. **Service was created before the render.yaml update**
2. **Render is using cached configuration**
3. **The service is manually configured to use the old build command**

## 🔧 Immediate Solutions

### Option 1: Update Service Configuration (Recommended)

1. **Go to Render Dashboard**:
   - Navigate to your service
   - Go to **Settings** → **Build & Deploy**

2. **Update Build Command**:
   - Change from: `bash build.sh`
   - Change to: `pip install -r backend/requirements.txt`

3. **Update Start Command**:
   - Change from: `bash build.sh` (if that's what it's set to)
   - Change to: `cd backend && uvicorn api.main:app --host 0.0.0.0 --port $PORT`

4. **Set Root Directory**:
   - Set to: `backend` (for backend services)
   - Set to: `frontend` (for frontend services)

### Option 2: Use the Updated Build Script

If you prefer to keep using a build script:

1. **Update Build Command**:
   - Change to: `bash build-minimal.sh`

2. **Or use the comprehensive script**:
   - Change to: `bash build.sh`

### Option 3: Create New Service with Blueprint

1. **Delete the current service** (if it's not working)
2. **Create new service using Blueprint**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Use the updated `render.yaml`

## 🎯 Root Cause Analysis

The issue occurs because:

1. **Service Configuration**: The service was created with the old build command
2. **Cached Settings**: Render might be using cached configuration
3. **Manual Override**: The service settings might override the blueprint

## 📋 Step-by-Step Fix

### For Backend Service:

1. **Settings** → **Build & Deploy**
2. **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### For Frontend Service:

1. **Settings** → **Build & Deploy**
2. **Root Directory**: `frontend`
3. **Build Command**: `npm ci && npm run build`
4. **Publish Path**: `.next`

## 🔍 Verification

After making changes:

1. **Check the logs** to see if the build command is working
2. **Verify the service starts** without errors
3. **Test the endpoints** to ensure everything is working

## 🚀 Alternative: Manual Service Creation

If the blueprint approach continues to have issues:

1. **Create new Web Service**:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **Create new Static Site**:
   - Root Directory: `frontend`
   - Build Command: `npm ci && npm run build`
   - Publish Path: `.next`

3. **Create databases manually**:
   - PostgreSQL database
   - Redis instance

4. **Set environment variables** for each service

## 📞 Support

If you continue to have issues:

1. **Check Render documentation**: https://render.com/docs
2. **Review service logs** for specific error messages
3. **Contact Render support** with the specific error details
4. **Consider using Vercel** for frontend deployment as an alternative

---

**Note**: The key is to ensure that each service is configured with the correct `rootDir` and build commands that work with the monorepo structure. 