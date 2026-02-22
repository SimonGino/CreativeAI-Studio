// === Model Definitions ===

export type MediaType = 'image' | 'video';
export type AuthType = 'gemini' | 'vertex';
export type UIMode = 'chat' | 'studio';

export interface ModelOption {
  id: string;
  name: string;
  type: MediaType;
  variant?: string;
  provider: string;
}

export const IMAGE_MODELS: ModelOption[] = [
  { id: 'gemini-2.5-flash-preview-image-generation', name: 'Gemini 2.5 Flash', type: 'image', provider: 'Google' },
  { id: 'gemini-2.0-flash-exp-image-generation', name: 'Gemini 2.0 Flash', type: 'image', provider: 'Google' },
  { id: 'gemini-3-pro-image-preview', name: 'Gemini 3 Pro', type: 'image', variant: 'Pro', provider: 'Google' },
];

export const VIDEO_MODELS: ModelOption[] = [
  { id: 'veo-3.1-fast-generate-preview', name: 'Veo 3.1 Fast', type: 'video', variant: 'Fast', provider: 'Google' },
  { id: 'veo-3.1-generate-preview', name: 'Veo 3.1', type: 'video', provider: 'Google' },
];

export const ASPECT_RATIOS = ['1:1', '3:4', '4:3', '9:16', '16:9'] as const;
export const VIDEO_DURATIONS = [4, 6, 8] as const;
export const VIDEO_RESOLUTIONS = ['720p', '1080p'] as const;

// === API Types ===

export interface ImageGenerateRequest {
  prompt: string;
  model: string;
  aspect_ratio: string;
  number_of_images: number;
  api_key?: string;
  auth_type: AuthType;
}

export interface ImageGenerateResponse {
  images: string[];
  model: string;
}

export interface VideoGenerateRequest {
  prompt: string;
  model: string;
  aspect_ratio: string;
  duration_seconds: number;
  resolution: string;
  generate_audio: boolean;
  api_key?: string;
  auth_type: AuthType;
}

export interface VideoGenerateResponse {
  task_id: string;
  status: string;
}

export interface VideoStatusUpdate {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  video_url?: string;
  error?: string;
}

// === Conversation Types ===

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  media_type?: MediaType | null;
  media_url?: string | null;
  model?: string | null;
  config?: Record<string, unknown> | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// === Settings ===

export interface AppSettings {
  gemini_api_key_configured: boolean;
  vertex_ai_configured: boolean;
}
