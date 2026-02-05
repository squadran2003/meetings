<template>
  <div class="meeting">
    <!-- Loading state -->
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>Connecting to meeting...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-container">
      <h2>Unable to Join Meeting</h2>
      <p>{{ error }}</p>
      <button @click="goHome" class="btn">Return Home</button>
    </div>

    <!-- Meeting room -->
    <template v-else>
      <div class="meeting-content" :class="{ 'chat-open': store.isChatOpen }">
        <VideoGrid />
      </div>

      <Controls
        @toggle-audio="toggleAudio"
        @toggle-video="toggleVideo"
        @toggle-screen-share="toggleScreenShare"
        @leave="leaveMeeting"
      />

      <Chat @send="sendChatMessage" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingStore } from '../stores/meeting'
import { useMediaStream } from '../composables/useMediaStream'
import { useSignaling } from '../composables/useSignaling'
import { useWebRTC } from '../composables/useWebRTC'
import VideoGrid from '../components/VideoGrid.vue'
import Controls from '../components/Controls.vue'
import Chat from '../components/Chat.vue'

const props = defineProps({
  roomId: {
    type: String,
    required: true
  }
})

const router = useRouter()
const store = useMeetingStore()
const { initializeMedia, startScreenShare, stopScreenShare, stopAllMedia, error: mediaError } = useMediaStream()
const signaling = useSignaling()
const webrtc = useWebRTC(signaling)

const isLoading = ref(true)
const error = ref(null)
let originalStream = null

// Secure user ID generation using crypto API
function generateSecureUserId() {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

onMounted(async () => {
  try {
    // Check if we have user info (came from Home page)
    if (!store.userId || !store.username) {
      // Generate user info if direct link access
      const userId = generateSecureUserId()
      const username = `Guest-${userId.substring(0, 4)}`
      store.setRoomInfo(props.roomId, userId, username)
    }

    // Initialize media
    await initializeMedia()
    originalStream = store.localStream

    // Connect to signaling server
    await signaling.connect(props.roomId, store.userId)

    // Setup WebRTC handlers
    webrtc.setupSignalingHandlers()

    // Join the room
    signaling.joinRoom(store.username)

    isLoading.value = false
  } catch (err) {
    console.error('Failed to join meeting:', err)
    error.value = mediaError.value || 'Failed to connect to the meeting. Please try again.'
    isLoading.value = false
  }
})

onUnmounted(() => {
  cleanup()
})

function cleanup() {
  webrtc.closeAllConnections()
  signaling.disconnect()
  stopAllMedia()
  store.reset()
}

function toggleAudio() {
  store.toggleAudio()
}

function toggleVideo() {
  store.toggleVideo()
}

async function toggleScreenShare() {
  if (store.isScreenSharing) {
    // Stop screen sharing, restore camera
    stopScreenShare()
    if (originalStream) {
      store.setLocalStream(originalStream)
      webrtc.replaceStream(originalStream)
    }
  } else {
    try {
      const screenStream = await startScreenShare()
      webrtc.replaceStream(screenStream)
      store.setLocalStream(screenStream)
    } catch (err) {
      // User cancelled or error
      console.log('Screen share cancelled or failed')
    }
  }
}

function sendChatMessage(message) {
  signaling.sendChatMessage(message)
  // Add to local messages immediately
  store.addChatMessage({
    fromUserId: store.userId,
    username: store.username,
    message
  })
}

function leaveMeeting() {
  cleanup()
  router.push('/')
}

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.meeting {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a2e;
}

.meeting-content {
  flex: 1;
  overflow: hidden;
  transition: margin-right 0.3s ease;
}

.meeting-content.chat-open {
  margin-right: 350px;
}

.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid #333;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px;
  text-align: center;
}

.error-container h2 {
  color: #ef4444;
}

.error-container p {
  color: #888;
  max-width: 400px;
}

.btn {
  padding: 12px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn:hover {
  background: #4338ca;
}

@media (max-width: 640px) {
  .meeting-content.chat-open {
    margin-right: 0;
  }
}
</style>
