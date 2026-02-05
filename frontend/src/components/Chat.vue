<template>
  <div class="chat" :class="{ open: store.isChatOpen }">
    <div class="chat-header">
      <h3>Chat</h3>
      <button @click="store.toggleChat" class="btn-close">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="messages" ref="messagesEl">
      <div
        v-for="(msg, index) in store.chatMessages"
        :key="index"
        class="message"
        :class="{ 'is-own': msg.fromUserId === store.userId }"
      >
        <div class="message-header">
          <span class="message-author">{{ msg.fromUserId === store.userId ? 'You' : msg.username }}</span>
          <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
        </div>
        <div class="message-content">{{ msg.message }}</div>
      </div>

      <div v-if="store.chatMessages.length === 0" class="no-messages">
        No messages yet. Start the conversation!
      </div>
    </div>

    <form @submit.prevent="sendMessage" class="chat-input">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Type a message..."
        maxlength="500"
      />
      <button type="submit" :disabled="!newMessage.trim()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </form>
  </div>
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
.chat {
  position: fixed;
  top: 0;
  right: -350px;
  width: 350px;
  height: 100%;
  background: #16213e;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  transition: right 0.3s ease;
  z-index: 100;
}

.chat.open {
  right: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #333;
}

.chat-header h3 {
  font-size: 1rem;
  font-weight: 600;
}

.btn-close {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-messages {
  color: #666;
  text-align: center;
  padding: 40px 20px;
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
  color: #4f46e5;
}

.message.is-own .message-author {
  color: #22c55e;
}

.message-time {
  font-size: 0.625rem;
  color: #666;
}

.message-content {
  background: #0f0f23;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.4;
  word-wrap: break-word;
}

.message.is-own .message-content {
  background: #4f46e5;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid #333;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #333;
  border-radius: 20px;
  background: #0f0f23;
  color: #fff;
  font-size: 0.875rem;
  outline: none;
}

.chat-input input:focus {
  border-color: #4f46e5;
}

.chat-input button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #4f46e5;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.chat-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input button:hover:not(:disabled) {
  background: #4338ca;
}

@media (max-width: 640px) {
  .chat {
    width: 100%;
    right: -100%;
  }
}
</style>
