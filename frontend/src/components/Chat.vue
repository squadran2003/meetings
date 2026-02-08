<template lang="pug">
v-navigation-drawer(
  :model-value="store.isChatOpen"
  location="right"
  :width="350"
  temporary
  @update:model-value="v => { if (!v) store.toggleChat() }"
)
  .d-flex.flex-column(style="height: 100%")
    v-toolbar(color="surface" density="compact")
      v-toolbar-title Chat
      v-spacer
      v-btn(icon variant="text" @click="store.toggleChat")
        v-icon mdi-close

    .messages(ref="messagesEl")
      .message(
        v-for="(msg, index) in store.chatMessages"
        :key="index"
        :class="{ 'is-own': msg.fromUserId === store.userId }"
      )
        .message-header
          span.message-author {{ msg.fromUserId === store.userId ? 'You' : msg.username }}
          span.message-time {{ formatTime(msg.timestamp) }}
        .message-content {{ msg.message }}

      .text-center.text-medium-emphasis.pa-10(v-if="store.chatMessages.length === 0")
        | No messages yet. Start the conversation!

    v-divider
    form.d-flex.ga-2.pa-4(@submit.prevent="sendMessage")
      v-text-field(
        v-model="newMessage"
        placeholder="Type a message..."
        variant="outlined"
        density="compact"
        maxlength="500"
        hide-details
        rounded="pill"
      )
      v-btn(
        icon
        color="primary"
        type="submit"
        :disabled="!newMessage.trim()"
        size="40"
      )
        v-icon mdi-send
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useMeetingStore } from '../stores/meeting'

const store = useMeetingStore()

const emit = defineEmits(['send'])

const newMessage = ref('')
const messagesEl = ref(null)

function sanitizeMessage(msg) {
  // Remove HTML tags and limit length
  return msg
    .replace(/<[^>]*>/g, '')
    .trim()
    .substring(0, 500)
}

function sendMessage() {
  const sanitized = sanitizeMessage(newMessage.value)
  if (!sanitized) return

  emit('send', sanitized)
  newMessage.value = ''
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// Auto-scroll to bottom when new messages arrive
watch(() => store.chatMessages.length, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
})
</script>

<style scoped>
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 85%;
}

.message.is-own {
  align-self: flex-end;
}

.message-header {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin-bottom: 4px;
}

.message-author {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.message.is-own .message-author {
  color: #22c55e;
}

.message-time {
  font-size: 0.625rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.message-content {
  background: rgb(var(--v-theme-background));
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.4;
  word-wrap: break-word;
}

.message.is-own .message-content {
  background: rgb(var(--v-theme-primary));
}
</style>
