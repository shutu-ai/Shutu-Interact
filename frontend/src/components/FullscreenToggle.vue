<script setup lang="ts">
/** Kiosk fullscreen toggle (plan §8 Phase 4): one corner button, no chrome.
 *
 * The label follows real fullscreen state via `fullscreenchange`, so an
 * ESC-press or OS-level exit stays reflected. The listener is removed on
 * unmount.
 */
import { onBeforeUnmount, onMounted, ref } from "vue";

const isFullscreen = ref(false);

function toggle(): void {
  if (document.fullscreenElement) {
    void document.exitFullscreen();
  } else {
    void document.documentElement.requestFullscreen();
  }
}

function sync(): void {
  isFullscreen.value = document.fullscreenElement !== null;
}

onMounted(() => {
  sync();
  document.addEventListener("fullscreenchange", sync);
});

onBeforeUnmount(() => {
  document.removeEventListener("fullscreenchange", sync);
});
</script>

<template>
  <button type="button" class="fullscreen-toggle" @click="toggle">
    {{ isFullscreen ? "🗗 退出全屏 Exit Fullscreen" : "⛶ 全屏 Fullscreen" }}
  </button>
</template>

<style scoped>
.fullscreen-toggle {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 10;
  min-height: 48px;
  padding: 6px 16px;
  font-size: 1rem;
  border-radius: 14px;
  border: 2px solid #d9c9a8;
  background: #fff;
  cursor: pointer;
}
</style>
