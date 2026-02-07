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
// STUN servers discover public IP; TURN servers relay traffic when direct
// peer-to-peer connections fail (e.g. both users behind symmetric NAT).
const ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
  // Free TURN relay from Open Relay (metered.ca) — good for development/testing.
  // For production, replace with your own TURN server credentials.
  {
    urls: 'turn:openrelay.metered.ca:80',
    username: 'openrelayproject',
    credential: 'openrelayproject',
  },
  {
    urls: 'turn:openrelay.metered.ca:443',
    username: 'openrelayproject',
    credential: 'openrelayproject',
  },
  {
    urls: 'turn:openrelay.metered.ca:443?transport=tcp',
    username: 'openrelayproject',
    credential: 'openrelayproject',
  },
]

// Override with custom TURN server from environment variables if provided
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
