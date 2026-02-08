<template lang="pug">
.video-grid(:class="gridClass")
  //- Local video
  ParticipantVideo(
    :stream="store.localStream"
    :name="store.username"
    :is-local="true"
  )
  //- Remote participants
  ParticipantVideo(
    v-for="participant in store.participantList"
    :key="participant.username"
    :stream="participant.stream"
    :name="participant.username"
  )
</template>

<script setup>
import { computed } from 'vue'
import { useMeetingStore } from '../stores/meeting'
import ParticipantVideo from './ParticipantVideo.vue'

const store = useMeetingStore()

const gridClass = computed(() => {
  const count = store.participantCount
  if (count === 1) return 'grid-1'
  if (count === 2) return 'grid-2'
  if (count <= 4) return 'grid-4'
  return 'grid-4'
})
</script>

<style scoped>
.video-grid {
  display: grid;
  gap: 12px;
  padding: 12px;
  height: 100%;
  width: 100%;
}

.grid-1 {
  grid-template-columns: 1fr;
  max-width: 900px;
  margin: 0 auto;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
  align-items: center;
}

.grid-4 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}

@media (max-width: 640px) {
  .grid-2,
  .grid-4 {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
}
</style>
