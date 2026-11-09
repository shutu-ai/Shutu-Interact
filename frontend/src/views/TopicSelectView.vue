<script setup lang="ts">
import { useRouter } from "vue-router";

import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";
import type { Topic } from "../types/session";

const router = useRouter();
const store = useSessionStore();

const TOPICS: ReadonlyArray<{
  value: Topic;
  emoji: string;
  label: string;
}> = [
  { value: "animals", emoji: "🐶", label: "Animals 动物" },
  { value: "colors", emoji: "🎨", label: "Colors 颜色" },
  { value: "fruits", emoji: "🍎", label: "Fruits 水果" },
  { value: "sports", emoji: "⚽", label: "Sports 运动" },
  { value: "hobbies", emoji: "🎸", label: "Hobbies 爱好" },
];

async function choose(value: Topic): Promise<void> {
  await store.chooseTopic(value);
  if (store.sessionId && !store.error) {
    router.push("/session");
  }
}
</script>

<template>
  <section class="page">
    <h1 class="title">聊什么? · Pick a topic</h1>
    <p v-if="store.error" class="error">{{ store.error }}</p>
    <div class="choices">
      <PrimaryButton
        v-for="topic in TOPICS"
        :key="topic.value"
        :disabled="store.busy"
        @click="choose(topic.value)"
      >
        {{ topic.emoji }} {{ topic.label }}
      </PrimaryButton>
    </div>
  </section>
</template>
