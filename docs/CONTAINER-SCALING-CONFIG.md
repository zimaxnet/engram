# Container Scaling Configuration

## Overview
Configured Container Apps to stay warm for 30 minutes after user activity, then scale to zero to minimize costs.

## Configuration

### Infrastructure (Bicep)

#### Backend Container App
- **Scale Rules**: HTTP-based scaling on concurrent requests
- **Min Replicas**: 0 (scale to zero when idle)
- **Max Replicas**: 10
- **Scale Trigger**: 10 concurrent requests per replica

#### Worker Container App
- **Scale Rules**: HTTP-based scaling on concurrent requests
- **Min Replicas**: 0 (scale to zero when idle)
- **Max Replicas**: 5
- **Scale Trigger**: 5 concurrent requests per replica

### Frontend Keep-Alive

#### `useKeepAlive` Hook
- **Location**: `frontend/src/hooks/useKeepAlive.ts`
- **Behavior**:
  - Sends health check to backend every 5 minutes
  - Tracks user activity (mouse, keyboard, scroll, touch, click)
  - Keeps containers warm for 30 minutes after last activity
  - Automatically stops after 30 minutes of inactivity

#### Integration
- Integrated into `App.tsx` - automatically active when frontend loads
- No user configuration required
- Silent operation (errors logged to console debug only)

## How It Works

1. **User Opens Site**: Frontend loads, keep-alive hook activates
2. **Initial Request**: First health check wakes backend (cold start ~30-60s)
3. **Active Period**: Health checks every 5 minutes keep containers warm
4. **User Activity**: Any interaction resets the 30-minute timer
5. **Inactivity**: After 30 minutes of no activity, keep-alive stops
6. **Scale Down**: Containers scale to zero after Azure's default inactivity period (~5-10 minutes after last request)

## Benefits

- ✅ **Cost Optimization**: Containers scale to zero when not in use
- ✅ **User Experience**: Containers stay warm during active sessions
- ✅ **Automatic**: No manual intervention required
- ✅ **Smart**: Stops keep-alive when user is inactive

## Testing

1. Open https://engram.work
2. Check browser console (F12) - should see `[KeepAlive] Health check sent` every 5 minutes
3. Verify containers stay warm by checking Azure Portal
4. Wait 30+ minutes with no activity - keep-alive should stop
5. Containers should scale to zero after additional inactivity period

## Monitoring

- **Container Status**: `az containerapp show --name engram-api --resource-group engram-rg --query "properties.template.scale"`
- **Replica Count**: Check Azure Portal or use `az containerapp replica list`
- **Frontend Logs**: Browser console shows keep-alive activity

## Notes

- First request after scale-to-zero will experience cold start (30-60 seconds)
- Keep-alive uses health check endpoint (`/api/v1/health`) - lightweight
- Activity tracking is passive and doesn't impact performance
- Scale rules use HTTP concurrent requests, not request count

