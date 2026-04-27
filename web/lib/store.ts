"use client";

import { create } from "zustand";

interface UIState {
  selectedRowIndex: number | null;
  hoveredRowIndex: number | null;
  inspectorOpen: boolean;
  setSelectedRow: (i: number | null) => void;
  setHoveredRow: (i: number | null) => void;
  setInspectorOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedRowIndex: null,
  hoveredRowIndex: null,
  inspectorOpen: false,
  setSelectedRow: (selectedRowIndex) =>
    set((s) => ({
      selectedRowIndex,
      inspectorOpen: selectedRowIndex !== null ? true : s.inspectorOpen,
    })),
  setHoveredRow: (hoveredRowIndex) => set({ hoveredRowIndex }),
  setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),
}));
