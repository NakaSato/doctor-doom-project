// Zustand Store for Selected Items
import { create } from 'zustand';
import type { Site, Module, Defect, Inspection } from '@/types';

interface SelectionState {
  // Selected site
  selectedSite: Site | null;
  setSelectedSite: (site: Site | null) => void;

  // Selected module
  selectedModule: Module | null;
  setSelectedModule: (module: Module | null) => void;

  // Selected defect
  selectedDefect: Defect | null;
  setSelectedDefect: (defect: Defect | null) => void;

  // Selected inspection
  selectedInspection: Inspection | null;
  setSelectedInspection: (inspection: Inspection | null) => void;

  // Multi-select
  selectedDefectIds: string[];
  toggleDefectSelection: (defectId: string) => void;
  clearDefectSelection: () => void;

  // Comparison mode
  comparisonMode: boolean;
  toggleComparisonMode: () => void;
  comparisonItems: string[];
  addToComparison: (itemId: string) => void;
  removeFromComparison: (itemId: string) => void;
  clearComparison: () => void;
}

export const useSelectionStore = create<SelectionState>((set, get) => ({
  selectedSite: null,
  setSelectedSite: (site) => set({ selectedSite: site }),

  selectedModule: null,
  setSelectedModule: (module) => set({ selectedModule: module }),

  selectedDefect: null,
  setSelectedDefect: (defect) => set({ selectedDefect: defect }),

  selectedInspection: null,
  setSelectedInspection: (inspection) => set({ selectedInspection: inspection }),

  selectedDefectIds: [],
  toggleDefectSelection: (defectId) =>
    set((state) => ({
      selectedDefectIds: state.selectedDefectIds.includes(defectId)
        ? state.selectedDefectIds.filter((id) => id !== defectId)
        : [...state.selectedDefectIds, defectId],
    })),
  clearDefectSelection: () => set({ selectedDefectIds: [] }),

  comparisonMode: false,
  toggleComparisonMode: () =>
    set((state) => ({
      comparisonMode: !state.comparisonMode,
      comparisonItems: !state.comparisonMode ? [] : state.comparisonItems,
    })),
  comparisonItems: [],
  addToComparison: (itemId) =>
    set((state) => {
      if (state.comparisonItems.length >= 4) {
        return state; // Max 4 items
      }
      if (state.comparisonItems.includes(itemId)) {
        return state;
      }
      return { comparisonItems: [...state.comparisonItems, itemId] };
    }),
  removeFromComparison: (itemId) =>
    set((state) => ({
      comparisonItems: state.comparisonItems.filter((id) => id !== itemId),
    })),
  clearComparison: () => set({ comparisonItems: [] }),
}));
