<script setup lang="ts">
import { useRouter } from "vue-router";

import PrimaryButton from "../components/PrimaryButton.vue";
import { useSessionStore } from "../stores/session";
import type { AgeGroup } from "../types/session";

const router = useRouter();
const store = useSessionStore();

const AGES: ReadonlyArray<{ value: AgeGroup; label: string }> = [
  { value: "4-6", label: "4–6 岁 · Little Kids" },
  { value: "7-9", label: "7–9 岁 · Kids" },
  { value: "10-12", label: "10–12 岁 · Big Kids" },
];

function choose(value: AgeGroup): void {
  store.chooseAge(value);
  router.push("/topic");
}

function goBack(): void {
  router.push("/");
}
</script>

<template>
  <section class="page">
    <button type="button" class="back-button" @click="goBack">
      ← 上一步 Back
    </button>
    <h1 class="title">你几岁啦? · How old are you?</h1>
    <div class="choices">
      <PrimaryButton
        v-for="age in AGES"
        :key="age.value"
        @click="choose(age.value)"
      >
        {{ age.label }}
      </PrimaryButton>
    </div>
  </section>
</template>
