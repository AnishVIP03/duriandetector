/**
 * Zustand environment store.
 * Tracks the currently active environment.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useEnvironmentStore = create(
  persist(
    (set) => ({
      currentEnvironment: null,
      members: [],

      setEnvironment: (env) => set({ currentEnvironment: env }),
      setMembers: (members) => set({ members }),
      clearEnvironment: () => set({ currentEnvironment: null, members: [] }),
    }),
    {
      name: 'ids-environment',
    }
  )
);
