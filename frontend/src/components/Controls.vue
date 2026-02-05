<template>
  <div class="controls">
    <div class="controls-left">
      <span class="room-id">Meeting: {{ store.roomId }}</span>
      <button @click="copyLink" class="btn-icon" title="Copy meeting link">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
    </div>

    <div class="controls-center">
      <button
        @click="toggleAudio"
        class="btn-control"
        :class="{ 'btn-off': !store.isAudioEnabled }"
        :title="store.isAudioEnabled ? 'Mute' : 'Unmute'"
      >
        <svg v-if="store.isAudioEnabled" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" y1="19" x2="12" y2="23"></line>
          <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="1" y1="1" x2="23" y2="23"></line>
          <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path>
          <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path>
          <line x1="12" y1="19" x2="12" y2="23"></line>
          <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
      </button>

      <button
        @click="toggleVideo"
        class="btn-control"
        :class="{ 'btn-off': !store.isVideoEnabled }"
        :title="store.isVideoEnabled ? 'Turn off camera' : 'Turn on camera'"
      >
        <svg v-if="store.isVideoEnabled" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="23 7 16 12 23 17 23 7"></polygon>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 16v1a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2m5.66 0H14a2 2 0 0 1 2 2v3.34l1 1L23 7v10"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      </button>

      <button
        @click="toggleScreenShare"
        class="btn-control"
        :class="{ 'btn-active': store.isScreenSharing }"
        title="Share screen"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
          <line x1="8" y1="21" x2="16" y2="21"></line>
          <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
      </button>

      <button
        @click="toggleChat"
        class="btn-control"
        :class="{ 'btn-active': store.isChatOpen }"
        title="Chat"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
      </button>

      <button @click="leaveMeeting" class="btn-control btn-leave" title="Leave meeting">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 2.59 3.4z"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      </button>
    </div>

    <div class="controls-right">
      <span class="participant-count">{{ store.participantCount }} participant{{ store.participantCount !== 1 ? 's' : '' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMeetingStore } from '../stores/meeting'

const store = useMeetingStore()

const emit = defineEmits(['toggle-audio', 'toggle-video', 'toggle-screen-share', 'leave'])

const lastSeenMessageCount = ref(0)

const unreadCount = computed(() => {
  if (store.isChatOpen) {
    lastSeenMessageCount.value = store.chatMessages.length
    return 0
  }
  return store.chatMessages.length - lastSeenMessageCount.value
})

function toggleAudio() {
  emit('toggle-audio')
}

function toggleVideo() {
  emit('toggle-video')
}

function toggleScreenShare() {
  emit('toggle-screen-share')
}

function toggleChat() {
  store.toggleChat()
  if (store.isChatOpen) {
    lastSeenMessageCount.value = store.chatMessages.length
  }
}

function leaveMeeting() {
  emit('leave')
}

function copyLink() {
  const url = window.location.href
  navigator.clipboard.writeText(url)
}
</script>

<style scoped>
.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #16213e;
  border-top: 1px solid #333;
}

.controls-left,
.controls-right {
  flex: 1;
}

.controls-right {
  text-align: right;
}

.controls-center {
  display: flex;
  gap: 12px;
}

.room-id {
  font-size: 0.875rem;
  color: #888;
  margin-right: 8px;
}

.participant-count {
  font-size: 0.875rem;
  color: #888;
}

.btn-icon {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-icon:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.btn-control {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: #374151;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-control:hover {
  background: #4b5563;
}

.btn-control.btn-off {
  background: #ef4444;
}

.btn-control.btn-off:hover {
  background: #dc2626;
}

.btn-control.btn-active {
  background: #4f46e5;
}

.btn-control.btn-leave {
  background: #ef4444;
}

.btn-control.btn-leave:hover {
  background: #dc2626;
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: #fff;
  font-size: 0.75rem;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

@media (max-width: 640px) {
  .controls-left,
  .controls-right {
    display: none;
  }

  .controls {
    justify-content: center;
  }
}
</style>
