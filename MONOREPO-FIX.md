# Monorepo Deployment Fix

## 🚨 The Problem

The original deployment was failing because:

1. **Monorepo Structure**: The project has `backend/` and `frontend/` directories
2. **Wrong Build Commands**: Render was trying to run `bash build.sh` from the root
3. **Missing rootDir**: Services weren't configured to use the correct subdirectory

## ✅ The Solution

### 1. **Proper rootDir Configuration**

Each service now has the correct `rootDir` set:

```yaml
# Backend services
- type: web
  name: ai-nudge-backend
  rootDir: backend          # ✅ Points to backend directory
  buildCommand: pip install -r requirements.txt
  startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT

# Frontend service  
- type: static_site
  name: ai-nudge-frontend
  rootDir: frontend         # ✅ Points to frontend directory
  buildCommand: npm ci && npm run build
  staticPublishPath: .next
```

### 2. **Simplified Build Commands**

Instead of complex build scripts, we use direct commands:

- **Backend**: `pip install -r requirements.txt`
- **Frontend**: `npm ci && npm run build`

### 3. **Correct Environment Variables**

- **PYTHONPATH**: Set to `.` (current directory) since we're already in the backend
- **Build paths**: All relative to the service's rootDir

## 🚀 How to Deploy

### Option 1: Render Blueprint (Recommended)

1. **Connect Repository**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository

2. **Deploy**:
   - Render will detect `render.yaml` in the root
   - It will create all services with proper rootDir
   - Configure environment variables
   - Deploy

### Option 2: Manual Service Setup

If you prefer manual setup:

1. **Backend Service**:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **Frontend Service**:
   - Root Directory: `frontend`
   - Build Command: `npm ci && npm run build`
   - Publish Path: `.next`

## 📁 File Structure

```
ai-nudge/
├── render.yaml              # ✅ Main blueprint configuration
├── backend/
│   ├── requirements.txt     # Python dependencies
│   ├── api/main.py         # FastAPI application
│   └── deployment/
│       └── render.yaml     # Alternative config
├── frontend/
│   ├── package.json        # Node.js dependencies
│   ├── next.config.js      # Next.js config
│   └── vercel.json         # Vercel config
└── ...
```

## 🔧 Key Changes Made

1. **Added `rootDir`** to all services in `render.yaml`
2. **Simplified build commands** to use direct package manager commands
3. **Fixed environment variables** to work with the new structure
4. **Updated documentation** to reflect the correct approach

## 🎯 Benefits

- **Cleaner deployment**: Each service builds from its own directory
- **Better isolation**: Backend and frontend are completely separate
- **Easier debugging**: Build logs are specific to each service
- **Scalable**: Easy to add more services or modify existing ones

## 🚨 Common Issues Fixed

1. **"build.sh: No such file or directory"** → Fixed with proper rootDir
2. **"Module not found"** → Fixed with correct PYTHONPATH
3. **"npm not found"** → Fixed with frontend rootDir
4. **"uvicorn not found"** → Fixed with backend rootDir

---

**The deployment should now work correctly!** The key was understanding that this is a monorepo and each service needs to be configured with the correct `rootDir` to build from the right subdirectory. 