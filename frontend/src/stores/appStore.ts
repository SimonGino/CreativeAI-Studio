import { create } from 'zustand';
import type { UIMode, MediaType, AuthType } from '@/types';
import type { Locale } from '@/lib/i18n';

const LOCALE_STORAGE_KEY = 'creativeai-studio:locale';

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'en';
  const saved = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  if (saved === 'en' || saved === 'zh-CN') return saved;
  return window.navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en';
}

interface AppState {
  // Locale
  locale: Locale;
  setLocale: (locale: Locale) => void;

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
  locale: getInitialLocale(),
  setLocale: (locale) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    }
    set({ locale });
  },

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
