import { ref, onUnmounted } from 'vue'
import { useMeetingStore } from '../stores/meeting'
import { WS_URL } from '../config'

export function useSignaling() {
  const store = useMeetingStore()
  const socket = ref(null)
  const isConnected = ref(false)
  const messageHandlers = ref({})

  function connect(roomId, userId) {
    return new Promise((resolve, reject) => {
      let wsBase = WS_URL
      if (!wsBase) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        wsBase = `${protocol}//${window.location.host}`
      }
      const wsUrl = `${wsBase}/ws/${roomId}/${userId}`

      store.setConnectionStatus('connecting')
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        isConnected.value = true
        store.setConnectionStatus('connected')
        resolve()
      }

      socket.value.onclose = () => {
        isConnected.value = false
        store.setConnectionStatus('disconnected')
      }

      socket.value.onerror = (err) => {
        console.error('WebSocket error:', err)
        reject(err)
      }

      socket.value.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Error parsing message:', err)
        }
      }
    })
  }

  function handleMessage(message) {
    const { type } = message
    const handler = messageHandlers.value[type]
    if (handler) {
      handler(message)
    } else {
      console.warn('Unhandled message type:', type)
    }
  }

  function on(type, handler) {
    messageHandlers.value[type] = handler
  }

  function off(type) {
    delete messageHandlers.value[type]
  }

  function send(message) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(message))
    }
  }

  function joinRoom(username) {
    send({
      type: 'join',
      username
    })
  }

  function sendOffer(toUserId, offer) {
    send({
      type: 'offer',
      toUserId,
      offer
    })
  }

  function sendAnswer(toUserId, answer) {
    send({
      type: 'answer',
      toUserId,
      answer
    })
  }

  function sendIceCandidate(toUserId, candidate) {
    send({
      type: 'ice-candidate',
      toUserId,
      candidate
    })
  }

  function sendChatMessage(message) {
    send({
      type: 'chat',
      message
    })
  }

  function disconnect() {
    if (socket.value) {
      send({ type: 'leave' })
      socket.value.close()
      socket.value = null
    }
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    connect,
    disconnect,
    on,
    off,
    send,
    joinRoom,
    sendOffer,
    sendAnswer,
    sendIceCandidate,
    sendChatMessage
  }
}
