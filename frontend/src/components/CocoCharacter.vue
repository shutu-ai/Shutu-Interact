<script setup lang="ts">
import { computed } from "vue";

import { assetFor, type CharacterState } from "../services/character";

const props = defineProps<{ state: CharacterState }>();

const src = computed(() => assetFor(props.state));
</script>

<template>
  <img class="coco-character" :src="src" alt="Coco the camel mascot" />
</template>

<style scoped>
.coco-character {
  width: min(46vmin, 320px);
  max-width: 100%;
  user-select: none;
  -webkit-user-drag: none;
}
</style>
