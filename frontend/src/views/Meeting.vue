<template lang="pug">
.meeting
  //- Loading state
  .loading.d-flex.flex-column.align-center.justify-center(v-if="isLoading" style="flex: 1")
    v-progress-circular(indeterminate color="primary" size="48" width="3")
    p.mt-4 Connecting to meeting...

  //- Error state
  .d-flex.flex-column.align-center.justify-center.pa-5.text-center(v-else-if="error" style="flex: 1")
    h2.text-error Unable to Join Meeting
    p.text-medium-emphasis.mt-2(style="max-width: 400px") {{ error }}
    v-btn.mt-4(color="primary" @click="goHome") Return Home

  //- Meeting room
  template(v-else)
    .meeting-content
      VideoGrid
    Controls(
      @toggle-audio="toggleAudio"
      @toggle-video="toggleVideo"
      @toggle-screen-share="toggleScreenShare"
      @leave="leaveMeeting"
    )
    Chat(@send="sendChatMessage")
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

    // Initialize media and fetch TURN credentials in parallel
    await Promise.all([
      initializeMedia(),
      webrtc.fetchIceServers()
    ])
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
}

.meeting-content {
  flex: 1;
  overflow: hidden;
}
</style>
