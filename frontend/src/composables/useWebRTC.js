import { ref } from 'vue'
import SimplePeer from 'simple-peer'
import { useMeetingStore } from '../stores/meeting'
import { ICE_SERVERS } from '../config'

export function useWebRTC(signaling) {
  const store = useMeetingStore()
  const peers = ref(new Map())

  function createPeer(userId, username, initiator = false) {
    if (peers.value.has(userId)) {
      console.log('Peer already exists for:', userId)
      return peers.value.get(userId)
    }

    console.log(`Creating peer for ${username} (${userId}), initiator: ${initiator}`)

    const peer = new SimplePeer({
      initiator,
      stream: store.localStream,
      trickle: true,
      config: {
        iceServers: ICE_SERVERS
      }
    })

    peer.on('signal', (data) => {
      if (data.type === 'offer') {
        signaling.sendOffer(userId, data)
      } else if (data.type === 'answer') {
        signaling.sendAnswer(userId, data)
      } else if (data.candidate) {
        signaling.sendIceCandidate(userId, data)
      }
    })

    peer.on('stream', (stream) => {
      console.log('Received stream from:', userId)
      store.updateParticipant(userId, { stream })
    })

    peer.on('connect', () => {
      console.log('Peer connected:', userId)
    })

    peer.on('close', () => {
      console.log('Peer closed:', userId)
      removePeer(userId)
    })

    peer.on('error', (err) => {
      console.error('Peer error:', userId, err)
      removePeer(userId)
    })

    peers.value.set(userId, peer)
    store.addParticipant(userId, { username, peer, stream: null })

    return peer
  }

  function handleOffer(fromUserId, offer, username = 'Unknown') {
    console.log('Handling offer from:', fromUserId)
    let peer = peers.value.get(fromUserId)

    if (!peer) {
      peer = createPeer(fromUserId, username, false)
    }

    peer.signal(offer)
  }

  function handleAnswer(fromUserId, answer) {
    console.log('Handling answer from:', fromUserId)
    const peer = peers.value.get(fromUserId)

    if (peer) {
      peer.signal(answer)
    }
  }

  function handleIceCandidate(fromUserId, candidate) {
    const peer = peers.value.get(fromUserId)

    if (peer) {
      peer.signal(candidate)
    }
  }

  function removePeer(userId) {
    const peer = peers.value.get(userId)
    if (peer) {
      peer.destroy()
      peers.value.delete(userId)
    }
    store.removeParticipant(userId)
  }

  function replaceStream(newStream) {
    // Replace the stream in all peer connections
    peers.value.forEach((peer, userId) => {
      try {
        // Remove old tracks
        if (peer._senders) {
          peer._senders.forEach(sender => {
            peer.removeTrack(sender.track, peer.streams[0])
          })
        }

        // Add new tracks
        newStream.getTracks().forEach(track => {
          peer.addTrack(track, newStream)
        })
      } catch (err) {
        console.error('Error replacing stream for peer:', userId, err)
      }
    })
  }

  function closeAllConnections() {
    peers.value.forEach((peer, userId) => {
      peer.destroy()
    })
    peers.value.clear()
  }

  function setupSignalingHandlers() {
    signaling.on('room-info', (message) => {
      console.log('Room info received:', message)
      // Connect to existing participants
      message.participants.forEach(({ userId, username }) => {
        // We are the initiator since we're joining an existing room
        createPeer(userId, username, true)
      })
    })

    signaling.on('user-joined', (message) => {
      console.log('User joined:', message)
      // Don't create peer here - wait for their offer
      // The new user will initiate connections to existing participants
    })

    signaling.on('user-left', (message) => {
      console.log('User left:', message)
      removePeer(message.userId)
    })

    signaling.on('offer', (message) => {
      const participant = store.participants.get(message.fromUserId)
      const username = participant?.username || 'Unknown'
      handleOffer(message.fromUserId, message.offer, username)
    })

    signaling.on('answer', (message) => {
      handleAnswer(message.fromUserId, message.answer)
    })

    signaling.on('ice-candidate', (message) => {
      handleIceCandidate(message.fromUserId, message.candidate)
    })

    signaling.on('chat', (message) => {
      // Skip own messages - already added locally when sent
      if (message.fromUserId === store.userId) return

      store.addChatMessage({
        fromUserId: message.fromUserId,
        username: message.username,
        message: message.message
      })
    })

    signaling.on('error', (message) => {
      console.error('Signaling error:', message.message)
    })
  }

  return {
    peers,
    createPeer,
    handleOffer,
    handleAnswer,
    handleIceCandidate,
    removePeer,
    replaceStream,
    closeAllConnections,
    setupSignalingHandlers
  }
}
