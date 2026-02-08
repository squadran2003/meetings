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
//
// TURN credentials are fetched at runtime from the backend (which reads them
// from the METERED_API_KEY env var). If no API key is configured, only STUN
// is available and calls between different networks will fail.
const DEFAULT_ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
]

/**
 * Fetches TURN server credentials from the backend at runtime.
 * Falls back to STUN-only if the backend has no TURN config.
 */
export async function getIceServers() {
  try {
    const res = await fetch(`${API_URL}/api/turn-credentials`)
    if (res.ok) {
      const data = await res.json()
      if (data.iceServers && data.iceServers.length > 0) {
        return data.iceServers
      }
    }
  } catch (e) {
    console.warn('Could not fetch TURN credentials, using STUN only:', e)
  }
  return DEFAULT_ICE_SERVERS
}

export { DEFAULT_ICE_SERVERS as ICE_SERVERS }
