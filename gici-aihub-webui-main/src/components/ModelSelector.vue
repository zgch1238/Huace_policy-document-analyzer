<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  providers: Array,
  modelValue: Object // { providerID, modelID, mode }
});

const emit = defineEmits(['update:modelValue']);

const modes = [
  { id: 'plan', name: '计划模式 (Plan)' },
  { id: 'build', name: '构建模式 (Build)' }
];

const selectedProvider = computed({
  get: () => props.modelValue.providerID,
  set: (val) => {
    const provider = props.providers.find(p => p.id === val);
    const firstModelId = provider ? Object.keys(provider.models)[0] : '';
    emit('update:modelValue', { ...props.modelValue, providerID: val, modelID: firstModelId });
  }
});

const selectedModel = computed({
  get: () => props.modelValue.modelID,
  set: (val) => emit('update:modelValue', { ...props.modelValue, modelID: val })
});

const selectedMode = computed({
  get: () => props.modelValue.mode,
  set: (val) => emit('update:modelValue', { ...props.modelValue, mode: val })
});

const availableModels = computed(() => {
  const provider = props.providers.find(p => p.id === selectedProvider.value);
  return provider ? Object.values(provider.models) : [];
});
</script>

<template>
  <div class="model-selector">
    <div class="selector-group">
      <label><i class="fa-solid fa-microchip" style="font-size: 14px;"></i> 服务商</label>
      <select v-model="selectedProvider">
        <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <div class="selector-group">
      <label><i class="fa-solid fa-bolt" style="font-size: 14px;"></i> 模型</label>
      <select v-model="selectedModel">
        <option v-for="m in availableModels" :key="m.id" :value="m.id">{{ m.name }}</option>
      </select>
    </div>

    <div class="selector-group">
      <label><i class="fa-solid fa-sliders" style="font-size: 14px;"></i> 模式</label>
      <select v-model="selectedMode">
        <option v-for="mode in modes" :key="mode.id" :value="mode.id">{{ mode.name }}</option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.model-selector {
  display: flex;
  gap: 16px;
  padding: 12px 40px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selector-group label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 600;
}

select {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--background);
  color: var(--text-primary);
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
  min-width: 140px;
}

select:focus {
  border-color: var(--accent);
}

@media (max-width: 768px) {
  .model-selector {
    padding: 12px 20px;
    gap: 8px;
  }
  select {
    min-width: 100px;
  }
}
</style>
