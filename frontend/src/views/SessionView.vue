<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const store = useSessionStore();
const draft = ref("");

// Voice is the primary channel (半双工: tap → talk → tap → reply plays).
async function toggleMic(): Promise<void> {
  if (store.recording) {
    await store.finishVoice();
  } else {
    await store.beginVoice();
  }
}

// Text stays as a fallback for noisy front desks and mic failures.
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
    <p class="progress">Round {{ store.turn }} / {{ store.maxTurns }}</p>
    <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>
    <button
      type="button"
      class="mic-button"
      :class="{ recording: store.recording }"
      :disabled="store.busy"
      @click="toggleMic"
    >
      {{ store.recording ? "⏹ 停止 Stop" : "🎤 说话 Talk!" }}
    </button>
    <p class="hint" :class="{ listening: store.recording }">
      {{
        store.busy
          ? "Coco is thinking… Coco 想一想…"
          : store.recording
            ? "I'm listening… 我在听,请说英语"
            : "Tap the mic and answer in English · 点麦克风用英语回答"
      }}
    </p>
    <form class="mock-input" @submit.prevent="send">
      <input
        v-model="draft"
        type="text"
        :disabled="store.busy || store.recording"
        placeholder="文字备用 Text fallback(语音不可用时)"
      />
      <PrimaryButton :disabled="store.busy || store.recording || !draft.trim()">
        发送 Send
      </PrimaryButton>
    </form>
  </section>
</template>

<style scoped>
.session-page {
  position: relative;
}

.mic-button {
  width: 168px;
  height: 168px;
  border-radius: 50%;
  border: none;
  background: #e5484d;
  color: #fff;
  font-size: 1.5rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 0 #b3323a;
  transition:
    transform 0.05s ease,
    box-shadow 0.05s ease;
}

.mic-button:active {
  transform: translateY(5px);
  box-shadow: 0 3px 0 #b3323a;
}

.mic-button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.mic-button.recording {
  animation: pulse 1.2s ease-in-out infinite;
}

.hint {
  font-size: 1.15rem;
  margin: 0;
  text-align: center;
  min-height: 1.6em;
}

.progress {
  margin: 0;
  font-size: 1.1rem;
  color: #8a7a5c;
  letter-spacing: 0.04em;
}

.hint.listening {
  color: #2f6fed;
  font-weight: 700;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
}
</style>
