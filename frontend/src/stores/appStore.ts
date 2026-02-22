import { create } from 'zustand';
import type { UIMode, MediaType, AuthType } from '@/types';

interface AppState {
  // UI mode
  uiMode: UIMode;
  setUIMode: (mode: UIMode) => void;

  // Current media tab (for studio mode)
  mediaTab: MediaType;
  setMediaTab: (tab: MediaType) => void;

  // Selected models
  imageModel: string;
  setImageModel: (model: string) => void;
  videoModel: string;
  setVideoModel: (model: string) => void;

  // Generation params
  aspectRatio: string;
  setAspectRatio: (ratio: string) => void;
  duration: number;
  setDuration: (d: number) => void;
  resolution: string;
  setResolution: (r: string) => void;

  // Auth
  authType: AuthType;
  setAuthType: (t: AuthType) => void;
  geminiApiKey: string;
  setGeminiApiKey: (key: string) => void;

  // Current conversation
  currentConversationId: string | null;
  setCurrentConversationId: (id: string | null) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  uiMode: 'chat',
  setUIMode: (mode) => set({ uiMode: mode }),

  mediaTab: 'image',
  setMediaTab: (tab) => set({ mediaTab: tab }),

  imageModel: 'gemini-2.5-flash-preview-image-generation',
  setImageModel: (model) => set({ imageModel: model }),
  videoModel: 'veo-3.1-fast-generate-preview',
  setVideoModel: (model) => set({ videoModel: model }),

  aspectRatio: '16:9',
  setAspectRatio: (ratio) => set({ aspectRatio: ratio }),
  duration: 8,
  setDuration: (d) => set({ duration: d }),
  resolution: '720p',
  setResolution: (r) => set({ resolution: r }),

  authType: 'gemini',
  setAuthType: (t) => set({ authType: t }),
  geminiApiKey: '',
  setGeminiApiKey: (key) => set({ geminiApiKey: key }),

  currentConversationId: null,
  setCurrentConversationId: (id) => set({ currentConversationId: id }),

  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
