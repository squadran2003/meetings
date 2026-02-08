<template lang="pug">
v-toolbar.controls(color="surface" density="comfortable")
  .controls-left.d-none.d-sm-flex.align-center(style="flex: 1")
    span.text-body-2.text-medium-emphasis Meeting: {{ store.roomId }}
    v-btn(icon size="small" variant="text" @click="copyLink" title="Copy meeting link")
      v-icon(size="20") mdi-content-copy

  .controls-center.d-flex.ga-3
    v-btn(
      icon
      :color="store.isAudioEnabled ? 'grey-darken-1' : 'error'"
      @click="toggleAudio"
      :title="store.isAudioEnabled ? 'Mute' : 'Unmute'"
    )
      v-icon {{ store.isAudioEnabled ? 'mdi-microphone' : 'mdi-microphone-off' }}

    v-btn(
      icon
      :color="store.isVideoEnabled ? 'grey-darken-1' : 'error'"
      @click="toggleVideo"
      :title="store.isVideoEnabled ? 'Turn off camera' : 'Turn on camera'"
    )
      v-icon {{ store.isVideoEnabled ? 'mdi-video' : 'mdi-video-off' }}

    v-btn(
      icon
      :color="store.isScreenSharing ? 'primary' : 'grey-darken-1'"
      @click="toggleScreenShare"
      title="Share screen"
    )
      v-icon mdi-monitor-share

    v-badge(
      :content="unreadCount"
      :model-value="unreadCount > 0"
      color="error"
      floating
    )
      v-btn(
        icon
        :color="store.isChatOpen ? 'primary' : 'grey-darken-1'"
        @click="toggleChat"
        title="Chat"
      )
        v-icon mdi-chat

    v-btn(
      icon
      color="error"
      @click="leaveMeeting"
      title="Leave meeting"
    )
      v-icon mdi-phone-hangup

  .controls-right.d-none.d-sm-flex.align-center.justify-end.ga-2(style="flex: 1")
    span.text-body-2.text-medium-emphasis {{ store.participantCount }} participant{{ store.participantCount !== 1 ? 's' : '' }}
    v-btn(
      icon
      size="small"
      variant="text"
      @click="toggleTheme"
      :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    )
      v-icon(size="20") {{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'
import { useMeetingStore } from '../stores/meeting'

const store = useMeetingStore()
const theme = useTheme()

const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

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
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.controls-center {
  display: flex;
  align-items: center;
}
</style>
