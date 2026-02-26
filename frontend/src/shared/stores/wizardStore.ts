import { create } from 'zustand'
import type { CatalogingRequest } from '@/shared/types/api'

type WizardStep = 'connect' | 'catalog' | 'browse'

interface WizardState {
  currentStep: WizardStep
  dbConfig: CatalogingRequest | null
  startTime: number | null
  endTime: number | null

  setStep: (step: WizardStep) => void
  setDbConfig: (config: CatalogingRequest) => void
  startCataloging: () => void
  completeCataloging: () => void
  reset: () => void
}

const defaultDbConfig: CatalogingRequest = {
  host: 'postgres',
  port: 5432,
  database: 'northwind',
  username: 'postgres',
  password: 'postgres',
  db_type: 'postgresql',
}

export const useWizardStore = create<WizardState>((set) => ({
  currentStep: 'connect',
  dbConfig: defaultDbConfig,
  startTime: null,
  endTime: null,

  setStep: (step) => set({ currentStep: step }),

  setDbConfig: (config) => set({ dbConfig: config }),

  startCataloging: () =>
    set({
      currentStep: 'catalog',
      startTime: Date.now(),
      endTime: null,
    }),

  completeCataloging: () =>
    set({
      endTime: Date.now(),
    }),

  reset: () =>
    set({
      currentStep: 'connect',
      dbConfig: defaultDbConfig,
      startTime: null,
      endTime: null,
    }),
}))
