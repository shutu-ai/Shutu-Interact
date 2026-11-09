<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import CocoCharacter from "../components/CocoCharacter.vue";
import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";

const router = useRouter();
const store = useSessionStore();

/** G3 (MVP closure): an adult must confirm before the interaction —
 * this is the guardian gate the privacy pilot requires. */
const consented = ref(false);

function toggleConsent(): void {
  consented.value = !consented.value;
}

function start(): void {
  if (!consented.value) {
    return;
  }
  router.push("/age");
}
</script>

<template>
  <section class="page">
    <CocoCharacter state="idle" />
    <h1 class="title">Coco English</h1>
    <p class="subtitle">你好!我是 Coco,AI 英语互动机器人,一起说英语吧!</p>
    <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>
    <p class="privacy-note">
      语音会上传到服务器做识别,仅在互动期间临时保存,互动结束即删除。
      请由家长或监护人陪同使用 · Speech audio is uploaded for recognition,
      kept only during the interaction, and deleted when it ends. A parent
      or guardian should be present.
    </p>
    <button
      type="button"
      class="consent-button"
      :class="{ confirmed: consented }"
      @click="toggleConsent"
    >
      {{ consented ? "✓ 家长/监护人已确认 Consent confirmed" : "我是家长/监护人,同意孩子参与 · I am the parent/guardian" }}
    </button>
    <PrimaryButton :disabled="!consented" @click="start">
      Start · 开始互动
    </PrimaryButton>
  </section>
</template>

<style scoped>
.privacy-note {
  font-size: 0.95rem;
  color: #8a7a5c;
  text-align: center;
  margin: 0;
  max-width: 560px;
}

.error {
  font-size: 1rem;
  color: #b3323a;
  text-align: center;
  margin: 0;
}

.consent-button {
  font-size: 1rem;
  padding: 12px 20px;
  border-radius: 12px;
  border: 2px solid #d8c9a5;
  background: #fff;
  color: #6b5b3e;
  cursor: pointer;
  max-width: 560px;
}

.consent-button.confirmed {
  border-color: #2e9e5b;
  background: #eafaf0;
  color: #1f7a44;
  font-weight: 700;
}

.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
