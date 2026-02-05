import { ref } from 'vue'
import { useMeetingStore } from '../stores/meeting'

export function useMediaStream() {
  const store = useMeetingStore()
  const error = ref(null)
  const isInitializing = ref(false)

  async function initializeMedia(video = true, audio = true) {
    isInitializing.value = true
    error.value = null

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: video ? {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        } : false,
        audio: audio ? {
          echoCancellation: true,
          noiseSuppression: true
        } : false
      })

      store.setLocalStream(stream)
      return stream
    } catch (err) {
      console.error('Error accessing media devices:', err)
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isInitializing.value = false
    }
  }

  function getErrorMessage(err) {
    switch (err.name) {
      case 'NotAllowedError':
        return 'Camera/microphone permission denied. Please allow access and try again.'
      case 'NotFoundError':
        return 'No camera or microphone found.'
      case 'NotReadableError':
        return 'Camera or microphone is already in use by another application.'
      default:
        return 'Failed to access camera/microphone.'
    }
  }

  async function startScreenShare() {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          cursor: 'always'
        },
        audio: false
      })

      store.setScreenSharing(true)

      // Handle when user stops sharing via browser UI
      screenStream.getVideoTracks()[0].onended = () => {
        stopScreenShare()
      }

      return screenStream
    } catch (err) {
      console.error('Error starting screen share:', err)
      if (err.name !== 'AbortError') {
        error.value = 'Failed to start screen sharing.'
      }
      throw err
    }
  }

  function stopScreenShare() {
    store.setScreenSharing(false)
  }

  function stopAllMedia() {
    if (store.localStream) {
      store.localStream.getTracks().forEach(track => track.stop())
      store.setLocalStream(null)
    }
  }

  return {
    error,
    isInitializing,
    initializeMedia,
    startScreenShare,
    stopScreenShare,
    stopAllMedia
  }
}
