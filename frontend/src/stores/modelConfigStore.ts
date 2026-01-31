import { create } from 'zustand'
import { ModelConfig } from '../services/modelConfig'

interface ModelConfigState {
  configs: ModelConfig[]
  selectedConfigId: number | null
  setConfigs: (configs: ModelConfig[]) => void
  addConfig: (config: ModelConfig) => void
  updateConfig: (config: ModelConfig) => void
  removeConfigs: (ids: number[]) => void
  setSelectedConfigId: (id: number | null) => void
  getSelectedConfig: () => ModelConfig | null
}

export const useModelConfigStore = create<ModelConfigState>((set, get) => ({
  configs: [],
  selectedConfigId: null,
  setConfigs: (configs) => set({ configs }),
  addConfig: (config) => set((state) => ({ configs: [...state.configs, config] })),
  updateConfig: (config) =>
    set((state) => ({
      configs: state.configs.map((c) => (c.config_id === config.config_id ? config : c)),
    })),
  removeConfigs: (ids) =>
    set((state) => ({
      configs: state.configs.filter((c) => !ids.includes(c.config_id)),
      selectedConfigId: ids.includes(state.selectedConfigId || 0) ? null : state.selectedConfigId,
    })),
  setSelectedConfigId: (id) => set({ selectedConfigId: id }),
  getSelectedConfig: () => {
    const state = get()
    return state.configs.find((c) => c.config_id === state.selectedConfigId) || null
  },
}))