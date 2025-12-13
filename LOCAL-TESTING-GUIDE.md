# Local Testing Guide

## Quick Start

### Option 1: Docker Compose (Recommended - Full Stack)

```bash
# Start all services (backend, frontend, postgres, temporal, zep)
docker-compose up

# Frontend will be available at: http://localhost:5173
# Backend API at: http://localhost:8082
```

### Option 2: Frontend Only (Fastest for UI Testing)

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Set API URL to deployed backend
export VITE_API_URL=https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io

# Or use local backend
export VITE_API_URL=http://localhost:8082

# Start dev server
npm run dev

# Open http://localhost:5173
```

### Option 3: Frontend with Local Backend

```bash
# Terminal 1: Start backend
cd backend
# Set up environment variables
export ZEP_API_URL=https://app.getzep.com
export ZEP_API_KEY=<your-key-from-kv>
# ... other env vars
uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload

# Terminal 2: Start frontend
cd frontend
export VITE_API_URL=http://localhost:8082
npm run dev
```

## What to Check

### 1. Browser Console
Open DevTools (F12) and check:
- **Console tab**: Look for JavaScript errors
- **Network tab**: Check if API requests are failing
- **Sources tab**: Verify the JavaScript bundle loads

### 2. Common Issues

#### Blank Page
- Check console for React errors
- Verify `index-Bk43wPv1.js` loads (check Network tab)
- Check if API URL is correct in the bundle

#### API Connection Errors
- Verify `VITE_API_URL` is set correctly
- Check CORS settings in backend
- Verify backend is running and accessible

#### Build Issues
```bash
# Clean and rebuild
cd frontend
rm -rf dist node_modules
npm install
npm run build

# Check build output
ls -la dist/
cat dist/index.html
```

### 3. Verify Build Output

```bash
# Check if API URL is in the bundle
cd frontend
npm run build
grep -r "VITE_API_URL\|localhost:8082\|engram-api" dist/ || echo "No API URL found in build"

# Or check the actual bundle
cat dist/assets/index-*.js | grep -o "https://[^\"]*" | head -5
```

## Debugging the Blank Page Issue

### Step 1: Test Locally
```bash
cd frontend
export VITE_API_URL=https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io
npm run dev
```

### Step 2: Check Browser Console
- Open http://localhost:5173
- Open DevTools (F12)
- Look for errors in Console tab

### Step 3: Check Network Requests
- Network tab → Filter by "Fetch/XHR"
- Look for failed API calls
- Check CORS errors

### Step 4: Verify React is Rendering
- In Console, type: `document.getElementById('root')`
- Should return the root element
- Check if React has mounted: Look for React DevTools

## Expected Behavior

When working correctly:
1. Page loads with ENGRAM header
2. Three-column layout visible (TreeNav, ChatPanel, VisualPanel)
3. No console errors
4. API health check succeeds
5. Can send chat messages

## Troubleshooting

### Issue: Blank page, no console errors
**Possible causes:**
- React not mounting
- CSS hiding content
- JavaScript bundle not loading

**Fix:**
```bash
# Rebuild with verbose output
cd frontend
npm run build -- --debug

# Check if root element exists
# In browser console: document.getElementById('root')
```

### Issue: CORS errors
**Fix:**
- Backend needs to allow frontend origin
- Check `CORS_ORIGINS` in backend config
- For local dev: `http://localhost:5173`

### Issue: API URL not set in build
**Fix:**
```bash
# Ensure VITE_API_URL is set before build
export VITE_API_URL=https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io
npm run build

# Verify in build output
grep -r "engram-api" dist/
```

## Production Build Test

Test the production build locally:

```bash
cd frontend

# Build for production
export VITE_API_URL=https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io
npm run build

# Preview production build
npm run preview

# Open http://localhost:4173
```

This simulates what's deployed and helps catch production-only issues.

