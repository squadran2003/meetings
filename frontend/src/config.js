/**
 * Centralized configuration from environment variables.
 * All env-dependent values should be read from here.
 */

// Base URL for API calls (e.g. "https://api.example.com")
// Empty string means use same-origin relative paths.
export const API_URL = import.meta.env.VITE_API_URL || ''

// Base URL for WebSocket connections (e.g. "wss://api.example.com")
// Empty string means auto-detect from window.location.
export const WS_URL = import.meta.env.VITE_WS_URL || ''

// ICE server configuration
const ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  { urls: 'stun:stun2.l.google.com:19302' },
]

const turnUrl = import.meta.env.VITE_TURN_URL
const turnUsername = import.meta.env.VITE_TURN_USERNAME
const turnCredential = import.meta.env.VITE_TURN_CREDENTIAL

if (turnUrl && turnUsername && turnCredential) {
  ICE_SERVERS.push({
    urls: turnUrl,
    username: turnUsername,
    credential: turnCredential,
  })
}

export { ICE_SERVERS }
