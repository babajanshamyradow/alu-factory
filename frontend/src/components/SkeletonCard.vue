<template>
  <div class="sk-card">
    <div class="skeleton sk-card__img" />
    <div class="sk-card__body">
      <div class="skeleton" style="height: 20px; width: 70%" />
      <div class="skeleton" style="height: 14px; width: 95%" />
      <div class="skeleton" style="height: 14px; width: 55%" />
    </div>
  </div>
</template>

<style scoped>
.sk-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--c-line);
  overflow: hidden;
  background: #fff;
}

.sk-card__img {
  aspect-ratio: 4 / 3.2;
  border-radius: 0;
}

.sk-card__body {
  padding: 22px 24px 26px;
  display: grid;
  gap: 12px;
}
</style>
