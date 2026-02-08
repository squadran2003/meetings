<template lang="pug">
v-container.fill-height(style="position: relative")
  v-btn.theme-toggle(
    icon
    variant="text"
    @click="toggleTheme"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    style="position: absolute; top: 16px; right: 16px; z-index: 1"
  )
    v-icon {{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}
  v-row.justify-center.align-center
    v-col(cols="12" md="10" lg="8")
      .text-center.mb-10
        h1.text-h3.font-weight-bold Meetings
        p.text-subtitle-1.text-medium-emphasis Video calls with up to 4 participants

      v-row(align="center" justify="center")
        v-col(cols="12" sm="6" md="5")
          v-card.pa-6(color="surface" rounded="lg")
            v-card-title.text-h6 Start New Meeting
            v-card-text
              v-text-field(
                v-model="username"
                label="Your name"
                variant="outlined"
                density="comfortable"
                maxlength="50"
                @input="validateUsername"
                hide-details
              )
            v-card-actions
              v-btn(
                block
                color="primary"
                size="large"
                :disabled="!isValidUsername"
                @click="createMeeting"
              ) Create Meeting

        v-col.text-center.d-none.d-md-flex.align-center.justify-center(cols="auto")
          span.text-medium-emphasis or

        v-col(cols="12" sm="6" md="5")
          v-card.pa-6(color="surface" rounded="lg")
            v-card-title.text-h6 Join Existing Meeting
            v-card-text
              v-text-field.mb-3(
                v-model="username"
                label="Your name"
                variant="outlined"
                density="comfortable"
                maxlength="50"
                @input="validateUsername"
                hide-details
              )
              v-text-field(
                v-model="roomCode"
                label="Meeting code"
                variant="outlined"
                density="comfortable"
                maxlength="50"
                @keyup.enter="joinMeeting"
                hide-details
              )
            v-card-actions
              v-btn(
                block
                variant="tonal"
                size="large"
                :disabled="!isValidUsername || !roomCode.trim()"
                @click="joinMeeting"
              ) Join Meeting

      v-alert.mt-4(
        v-if="error"
        type="error"
        variant="tonal"
        closable
      ) {{ error }}
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useMeetingStore } from '../stores/meeting'
import { API_URL } from '../config'

const router = useRouter()
const store = useMeetingStore()
const theme = useTheme()

const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

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
    const response = await fetch(`${API_URL}/api/rooms`, { method: 'POST' })

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
    const response = await fetch(`${API_URL}/api/rooms/${encodeURIComponent(code)}`)

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
