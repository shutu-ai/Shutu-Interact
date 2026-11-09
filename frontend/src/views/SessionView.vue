<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const store = useSessionStore();
const draft = ref("");

// MOCK INPUT (Phase 1). REPLACEMENT POINT: Task 3 (Phase 2) swaps this for
// MediaRecorder voice capture with ASR upload.
async function send(): Promise<void> {
  await store.sendChildText(draft.value);
  draft.value = "";
}

function exit(): void {
  void store.endSession().then(() => router.replace("/"));
}

watch(
  () => store.phase,
  (phase) => {
    if (phase === "end") {
      router.replace("/end");
    }
  },
);
</script>

<template>
  <section class="page session-page">
    <button type="button" class="exit-button" @click="exit">
      ✕ 退出 Exit
    </button>
    <CocoCharacter :state="store.characterState" />
    <div class="bubble">{{ store.assistantText }}</div>
    <p v-if="store.error" class="error">{{ store.error }}</p>
    <form class="mock-input" @submit.prevent="send">
      <input
        v-model="draft"
        type="text"
        :disabled="store.busy"
        placeholder="Mock: 请输入孩子说的话(语音功能下一阶段接入)"
      />
      <PrimaryButton :disabled="store.busy || !draft.trim()">
        发送 Send
      </PrimaryButton>
    </form>
  </section>
</template>

<style scoped>
.session-page {
  position: relative;
}
</style>
