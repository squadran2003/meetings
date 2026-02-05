<template>
  <div class="participant-video" :class="{ 'is-local': isLocal }">
    <video
      ref="videoEl"
      :muted="isLocal"
      autoplay
      playsinline
    ></video>
    <div class="overlay">
      <span class="name">{{ name }}{{ isLocal ? ' (You)' : '' }}</span>
    </div>
    <div v-if="!hasVideo" class="no-video">
      <div class="avatar">{{ initials }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  stream: {
    type: MediaStream,
    default: null
  },
  name: {
    type: String,
    default: 'Unknown'
  },
  isLocal: {
    type: Boolean,
    default: false
  }
})

const videoEl = ref(null)

const hasVideo = computed(() => {
  if (!props.stream) return false
  const videoTracks = props.stream.getVideoTracks()
  return videoTracks.length > 0 && videoTracks[0].enabled
})

const initials = computed(() => {
  return props.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
})

function attachStream() {
  if (videoEl.value && props.stream) {
    videoEl.value.srcObject = props.stream
  }
}

watch(() => props.stream, () => {
  attachStream()
})

onMounted(() => {
  attachStream()
})
</script>

<style scoped>
.participant-video {
  position: relative;
  background: #0f0f23;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}

.participant-video.is-local video {
  transform: scaleX(-1);
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
}

.name {
  font-size: 0.875rem;
  color: #fff;
}

.no-video {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
}
</style>
