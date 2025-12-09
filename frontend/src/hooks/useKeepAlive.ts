/**
 * Keep-Alive Hook
 * 
 * Sends periodic health checks to keep backend containers warm
 * while the user has the frontend open.
 * 
 * Sends health checks every 5 minutes to keep containers active for 30 minutes
 * after the last user activity.
 */

import { useEffect, useRef } from 'react'
import { checkHealth } from '../services/api'

const KEEP_ALIVE_INTERVAL = 5 * 60 * 1000 // 5 minutes
const ACTIVITY_TIMEOUT = 30 * 60 * 1000 // 30 minutes

export function useKeepAlive() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastActivityRef = useRef<number>(Date.now())
  const isActiveRef = useRef<boolean>(true)

  useEffect(() => {
    // Track user activity
    const updateActivity = () => {
      lastActivityRef.current = Date.now()
      isActiveRef.current = true
    }

    // Listen for user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    events.forEach(event => {
      window.addEventListener(event, updateActivity, { passive: true })
    })

    // Send health check to keep backend warm
    const sendKeepAlive = async () => {
      const timeSinceActivity = Date.now() - lastActivityRef.current
      
      // Only send keep-alive if user was active within the last 30 minutes
      if (timeSinceActivity < ACTIVITY_TIMEOUT && isActiveRef.current) {
        try {
          await checkHealth()
          console.debug('[KeepAlive] Health check sent')
        } catch (error) {
          // Silently fail - don't spam console with errors
          console.debug('[KeepAlive] Health check failed (backend may be cold starting)')
        }
      } else {
        // User inactive for 30+ minutes, stop keep-alive
        isActiveRef.current = false
        console.debug('[KeepAlive] User inactive, stopping keep-alive')
      }
    }

    // Send initial health check when page loads
    sendKeepAlive()

    // Set up periodic keep-alive
    intervalRef.current = setInterval(sendKeepAlive, KEEP_ALIVE_INTERVAL)

    // Cleanup
    return () => {
      events.forEach(event => {
        window.removeEventListener(event, updateActivity)
      })
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Reset activity when component mounts (user returned to page)
  useEffect(() => {
    lastActivityRef.current = Date.now()
    isActiveRef.current = true
  }, [])
}

