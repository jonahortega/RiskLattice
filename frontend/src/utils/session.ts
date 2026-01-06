/**
 * Session management for anonymous users
 * Generates and stores a unique session ID in localStorage
 */

const SESSION_ID_KEY = 'risklattice_session_id'

/**
 * Get or create a session ID
 * If one doesn't exist, generates a new unique ID
 */
export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_ID_KEY)
  
  if (!sessionId) {
    // Generate a unique session ID
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
    localStorage.setItem(SESSION_ID_KEY, sessionId)
    console.log('Generated new session ID:', sessionId)
  }
  
  return sessionId
}

/**
 * Clear session ID (for logout/reset)
 */
export function clearSessionId(): void {
  localStorage.removeItem(SESSION_ID_KEY)
}

