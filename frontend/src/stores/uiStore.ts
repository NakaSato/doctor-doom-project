// Zustand Store for UI State
import { create } from 'zustand';

interface UIState {
  // Sidebar
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Theme
  darkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (dark: boolean) => void;

  // Modal
  modalOpen: boolean;
  modalContent: React.ReactNode | null;
  openModal: (content: React.ReactNode) => void;
  closeModal: () => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;

  // Map
  mapZoom: number;
  setMapZoom: (zoom: number) => void;
  mapCenter: [number, number];
  setMapCenter: (center: [number, number]) => void;
}

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Theme
  darkMode: false,
  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    document.documentElement.classList.toggle('dark', newDarkMode);
    return { darkMode: newDarkMode };
  }),
  setDarkMode: (dark) => set({ darkMode: dark }),

  // Modal
  modalOpen: false,
  modalContent: null,
  openModal: (content) => set({ modalOpen: true, modalContent: content }),
  closeModal: () => set({ modalOpen: false, modalContent: null }),

  // Toast notifications
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { id, duration: 5000, ...toast };
    set((state) => ({ toasts: [...state.toasts, newToast] }));

    // Auto-remove after duration
    if (newToast.duration) {
      setTimeout(() => {
        get().removeToast(id);
      }, newToast.duration);
    }
  },
  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),

  // Map
  mapZoom: 15,
  setMapZoom: (zoom) => set({ mapZoom: zoom }),
  mapCenter: [0, 0],
  setMapCenter: (center) => set({ mapCenter: center }),
}));
