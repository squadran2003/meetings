<template>
  <div class="home">
    <div class="container">
      <h1>Meetings</h1>
      <p class="subtitle">Video calls with up to 4 participants</p>

      <div class="actions">
        <div class="card">
          <h2>Start New Meeting</h2>
          <input
            v-model="username"
            type="text"
            placeholder="Your name"
            class="input"
            maxlength="50"
            @input="validateUsername"
          />
          <button @click="createMeeting" :disabled="!isValidUsername" class="btn btn-primary">
            Create Meeting
          </button>
        </div>

        <div class="divider">
          <span>or</span>
        </div>

        <div class="card">
          <h2>Join Existing Meeting</h2>
          <input
            v-model="username"
            type="text"
            placeholder="Your name"
            class="input"
            maxlength="50"
            @input="validateUsername"
          />
          <input
            v-model="roomCode"
            type="text"
            placeholder="Meeting code"
            class="input"
            maxlength="50"
            @keyup.enter="joinMeeting"
          />
          <button @click="joinMeeting" :disabled="!isValidUsername || !roomCode.trim()" class="btn btn-secondary">
            Join Meeting
          </button>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingStore } from '../stores/meeting'

const router = useRouter()
const store = useMeetingStore()

const username = ref('')
const roomCode = ref('')
const error = ref('')

// Username validation
const isValidUsername = computed(() => {
  const name = username.value.trim()
  return name.length >= 1 && name.length <= 50
})

function validateUsername() {
  // Remove any HTML-like content
  username.value = username.value.replace(/<[^>]*>/g, '')
}

// Sanitize username before sending
function sanitizeUsername(name) {
  return name
    .trim()
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .substring(0, 50)
}

async function createMeeting() {
  if (!isValidUsername.value) return

  error.value = ''
  const cleanUsername = sanitizeUsername(username.value)

  try {
    const response = await fetch('/api/rooms', { method: 'POST' })

    if (!response.ok) {
      if (response.status === 429) {
        error.value = 'Too many requests. Please wait a moment and try again.'
        return
      }
      throw new Error('Failed to create room')
    }

    const data = await response.json()

    const userId = generateUserId()
    store.setRoomInfo(data.roomId, userId, cleanUsername)

    router.push(`/meeting/${data.roomId}`)
  } catch (err) {
    error.value = 'Failed to create meeting. Please try again.'
    console.error(err)
  }
}

async function joinMeeting() {
  if (!isValidUsername.value || !roomCode.value.trim()) return

  error.value = ''
  const code = roomCode.value.trim()
  const cleanUsername = sanitizeUsername(username.value)

  try {
    const response = await fetch(`/api/rooms/${encodeURIComponent(code)}`)

    if (!response.ok) {
      if (response.status === 429) {
        error.value = 'Too many requests. Please wait a moment and try again.'
        return
      }
      throw new Error('Failed to check room')
    }

    const data = await response.json()

    if (data.isFull) {
      error.value = 'This meeting is full (maximum 4 participants).'
      return
    }

    const userId = generateUserId()
    store.setRoomInfo(code, userId, cleanUsername)

    router.push(`/meeting/${code}`)
  } catch (err) {
    error.value = 'Failed to join meeting. Please check the code and try again.'
    console.error(err)
  }
}

function generateUserId() {
  // Use crypto API for secure random ID generation
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.container {
  max-width: 800px;
  width: 100%;
  text-align: center;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: #fff;
}

.subtitle {
  color: #888;
  margin-bottom: 3rem;
}

.actions {
  display: flex;
  gap: 2rem;
  align-items: stretch;
}

.card {
  flex: 1;
  background: #16213e;
  padding: 2rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.divider {
  display: flex;
  align-items: center;
  color: #666;
}

.input {
  padding: 12px 16px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #0f0f23;
  color: #fff;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #4f46e5;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #4f46e5;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
}

.btn-secondary {
  background: #374151;
  color: #fff;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.error {
  color: #ef4444;
  margin-top: 1rem;
}

@media (max-width: 640px) {
  .actions {
    flex-direction: column;
  }

  .divider {
    padding: 1rem 0;
  }
}
</style>
