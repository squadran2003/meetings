import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMeetingStore = defineStore('meeting', () => {
  // State
  const roomId = ref(null)
  const userId = ref(null)
  const username = ref('')
  const participants = ref(new Map()) // userId -> { username, stream, peer }
  const localStream = ref(null)
  const isAudioEnabled = ref(true)
  const isVideoEnabled = ref(true)
  const isScreenSharing = ref(false)
  const chatMessages = ref([])
  const isChatOpen = ref(false)
  const connectionStatus = ref('disconnected') // disconnected, connecting, connected

  // Getters
  const participantList = computed(() => Array.from(participants.value.values()))
  const participantCount = computed(() => participants.value.size + 1) // +1 for local user

  // Actions
  function setRoomInfo(room, user, name) {
    roomId.value = room
    userId.value = user
    username.value = name
  }

  function setLocalStream(stream) {
    localStream.value = stream
  }

  function addParticipant(userId, data) {
    participants.value.set(userId, { ...data })
    // Trigger reactivity
    participants.value = new Map(participants.value)
  }

  function updateParticipant(userId, data) {
    const existing = participants.value.get(userId)
    if (existing) {
      participants.value.set(userId, { ...existing, ...data })
      participants.value = new Map(participants.value)
    }
  }

  function removeParticipant(userId) {
    const participant = participants.value.get(userId)
    if (participant?.peer) {
      participant.peer.destroy()
    }
    participants.value.delete(userId)
    participants.value = new Map(participants.value)
  }

  function toggleAudio() {
    isAudioEnabled.value = !isAudioEnabled.value
    if (localStream.value) {
      localStream.value.getAudioTracks().forEach(track => {
        track.enabled = isAudioEnabled.value
      })
    }
  }

  function toggleVideo() {
    isVideoEnabled.value = !isVideoEnabled.value
    if (localStream.value) {
      localStream.value.getVideoTracks().forEach(track => {
        track.enabled = isVideoEnabled.value
      })
    }
  }

  function setScreenSharing(value) {
    isScreenSharing.value = value
  }

  function addChatMessage(message) {
    chatMessages.value.push({
      ...message,
      timestamp: new Date()
    })
  }

  function toggleChat() {
    isChatOpen.value = !isChatOpen.value
  }

  function setConnectionStatus(status) {
    connectionStatus.value = status
  }

  function reset() {
    // Clean up streams and peers
    if (localStream.value) {
      localStream.value.getTracks().forEach(track => track.stop())
    }
    participants.value.forEach(p => {
      if (p.peer) p.peer.destroy()
      if (p.stream) p.stream.getTracks().forEach(t => t.stop())
    })

    roomId.value = null
    userId.value = null
    username.value = ''
    participants.value = new Map()
    localStream.value = null
    isAudioEnabled.value = true
    isVideoEnabled.value = true
    isScreenSharing.value = false
    chatMessages.value = []
    isChatOpen.value = false
    connectionStatus.value = 'disconnected'
  }

  return {
    // State
    roomId,
    userId,
    username,
    participants,
    localStream,
    isAudioEnabled,
    isVideoEnabled,
    isScreenSharing,
    chatMessages,
    isChatOpen,
    connectionStatus,
    // Getters
    participantList,
    participantCount,
    // Actions
    setRoomInfo,
    setLocalStream,
    addParticipant,
    updateParticipant,
    removeParticipant,
    toggleAudio,
    toggleVideo,
    setScreenSharing,
    addChatMessage,
    toggleChat,
    setConnectionStatus,
    reset
  }
})
