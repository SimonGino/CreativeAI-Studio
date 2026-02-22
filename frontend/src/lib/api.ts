import axios from 'axios';
import type {
  ImageGenerateRequest,
  ImageGenerateResponse,
  VideoGenerateRequest,
  VideoGenerateResponse,
  Conversation,
  ConversationDetail,
  Message,
  AppSettings,
} from '@/types';

const api = axios.create({ baseURL: '/api' });

// === Image ===
export const generateImage = (data: ImageGenerateRequest) =>
  api.post<ImageGenerateResponse>('/image/generate', data).then(r => r.data);

// === Video ===
export const generateVideo = (data: VideoGenerateRequest) =>
  api.post<VideoGenerateResponse>('/video/generate', data).then(r => r.data);

export const createVideoStatusStream = (taskId: string, authType = 'gemini', apiKey?: string) => {
  const params = new URLSearchParams({ auth_type: authType });
  if (apiKey) params.set('api_key', apiKey);
  return new EventSource(`/api/video/${taskId}/status?${params}`);
};

// === Conversations ===
export const listConversations = () =>
  api.get<Conversation[]>('/conversations').then(r => r.data);

export const createConversation = (title = 'New Conversation') =>
  api.post<Conversation>('/conversations', { title }).then(r => r.data);

export const getConversation = (id: string) =>
  api.get<ConversationDetail>(`/conversations/${id}`).then(r => r.data);

export const deleteConversation = (id: string) =>
  api.delete(`/conversations/${id}`);

export const addMessage = (convId: string, data: Partial<Message>) =>
  api.post<Message>(`/conversations/${convId}/messages`, data).then(r => r.data);

// === Settings ===
export const getSettings = () =>
  api.get<AppSettings>('/settings').then(r => r.data);

export const updateSettings = (data: { gemini_api_key?: string }) =>
  api.put('/settings', data);
