import { ref } from 'vue'
import SimplePeer from 'simple-peer'
import { useMeetingStore } from '../stores/meeting'
import { ICE_SERVERS, getIceServers } from '../config'

export function useWebRTC(signaling) {
  const store = useMeetingStore()
  const peers = ref(new Map())
  // Resolved at init time via fetchIceServers()
  let resolvedIceServers = ICE_SERVERS

  async function fetchIceServers() {
    resolvedIceServers = await getIceServers()
    console.log('ICE servers resolved:', resolvedIceServers.length, 'servers')
  }

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
        iceServers: resolvedIceServers
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
      // Participant may already be in the store from user-joined handler.
      // createPeer will upsert the store entry with the actual peer object.
      const existing = store.participants.get(fromUserId)
      peer = createPeer(fromUserId, existing?.username || username, false)
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
      // Register the participant in the store so they appear in the video grid
      // immediately. Don't create the peer yet - the new user will send us an
      // offer because they are the initiator (see room-info handler above).
      store.addParticipant(message.userId, {
        username: message.username,
        peer: null,
        stream: null
      })
    })

    signaling.on('user-left', (message) => {
      console.log('User left:', message)
      removePeer(message.userId)
    })

    signaling.on('offer', (message) => {
      const existing = store.participants.get(message.fromUserId)
      const username = existing?.username || 'Unknown'
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
    fetchIceServers,
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
