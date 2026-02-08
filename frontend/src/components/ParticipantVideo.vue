<template lang="pug">
.participant-video(:class="{ 'is-local': isLocal }")
  video(ref="videoEl" :muted="isLocal" autoplay playsinline)
  .overlay
    span.name {{ name }}{{ isLocal ? ' (You)' : '' }}
  .no-video.d-flex.align-center.justify-center(v-if="!hasVideo")
    v-avatar(color="primary" size="80")
      span.text-h5.font-weight-bold {{ initials }}
</template>

<script setup>
import { ref, computed, watch, onMounted, toRaw } from 'vue'

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
    // toRaw() strips any Vue Proxy wrapper so the browser gets the native MediaStream
    videoEl.value.srcObject = toRaw(props.stream)
    // Explicit play() required on mobile browsers even with autoplay attribute
    videoEl.value.play().catch(() => {})
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
  background: rgb(var(--v-theme-background));
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
  background: rgb(var(--v-theme-background));
}
</style>
