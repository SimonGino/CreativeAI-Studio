import { useState, useCallback, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { useAppStore } from '@/stores/appStore'
import Header from '@/components/layout/Header'
import Sidebar from '@/components/layout/Sidebar'
import ChatView from '@/components/chat/ChatView'
import StudioView from '@/components/studio/StudioView'
import { SettingsPage } from '@/components/settings/SettingsPage'
import {
  listConversations,
  createConversation,
  getConversation,
  deleteConversation,
  addMessage,
  generateImage,
  generateVideo,
  createVideoStatusStream,
} from '@/lib/api'
import type { Conversation, Message, VideoStatusUpdate } from '@/types'

function MainPage() {
  const {
    uiMode, mediaTab, imageModel, videoModel,
    aspectRatio, duration, resolution, authType, geminiApiKey,
    currentConversationId, setCurrentConversationId, sidebarOpen,
  } = useAppStore()

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [studioResults, setStudioResults] = useState<string[]>([])

  useEffect(() => {
    listConversations().then(setConversations).catch(console.error)
  }, [])

  useEffect(() => {
    if (!currentConversationId) {
      setMessages([])
      return
    }
    getConversation(currentConversationId)
      .then(conv => setMessages(conv.messages))
      .catch(console.error)
  }, [currentConversationId])

  const handleNewConversation = useCallback(async () => {
    const conv = await createConversation()
    setConversations(prev => [conv, ...prev])
    setCurrentConversationId(conv.id)
  }, [setCurrentConversationId])

  const handleDeleteConversation = useCallback(async (id: string) => {
    await deleteConversation(id)
    setConversations(prev => prev.filter(c => c.id !== id))
    if (currentConversationId === id) {
      setCurrentConversationId(null)
      setMessages([])
    }
  }, [currentConversationId, setCurrentConversationId])

  const handleSendMessage = useCallback(async (content: string) => {
    setLoading(true)
    try {
      let convId = currentConversationId
      if (!convId) {
        const conv = await createConversation(content.slice(0, 50))
        setConversations(prev => [conv, ...prev])
        setCurrentConversationId(conv.id)
        convId = conv.id
      }

      const userMsg = await addMessage(convId, { role: 'user', content })
      setMessages(prev => [...prev, userMsg])

      const isVideo = mediaTab === 'video'
      const model = isVideo ? videoModel : imageModel

      if (isVideo) {
        const { task_id } = await generateVideo({
          prompt: content, model, aspect_ratio: aspectRatio,
          duration_seconds: duration, resolution, generate_audio: true,
          auth_type: authType, api_key: geminiApiKey || undefined,
        })

        const assistantMsg = await addMessage(convId, {
          role: 'assistant', content: 'Generating video...', media_type: 'video', model,
        })
        setMessages(prev => [...prev, assistantMsg])

        const es = createVideoStatusStream(task_id, authType, geminiApiKey || undefined)
        es.addEventListener('status', (e: MessageEvent) => {
          const data: VideoStatusUpdate = JSON.parse(e.data)
          if (data.status === 'completed' && data.video_url) {
            setMessages(prev => prev.map(m =>
              m.id === assistantMsg.id ? { ...m, content: 'Video generated', media_url: data.video_url } : m
            ))
            es.close()
          } else if (data.status === 'failed') {
            setMessages(prev => prev.map(m =>
              m.id === assistantMsg.id ? { ...m, content: `Failed: ${data.error}` } : m
            ))
            es.close()
          }
        })
        es.onerror = () => es.close()
      } else {
        const result = await generateImage({
          prompt: content, model, aspect_ratio: aspectRatio,
          number_of_images: 1, auth_type: authType,
          api_key: geminiApiKey || undefined,
        })

        for (const url of result.images) {
          const assistantMsg = await addMessage(convId, {
            role: 'assistant', content: 'Image generated', media_type: 'image', media_url: url, model,
          })
          setMessages(prev => [...prev, assistantMsg])
        }
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [currentConversationId, mediaTab, imageModel, videoModel, aspectRatio, duration, resolution, authType, geminiApiKey, setCurrentConversationId])

  const handleStudioGenerate = useCallback(async (prompt: string) => {
    setLoading(true)
    setStudioResults([])
    try {
      const isVideo = mediaTab === 'video'
      const model = isVideo ? videoModel : imageModel

      if (isVideo) {
        const { task_id } = await generateVideo({
          prompt, model, aspect_ratio: aspectRatio,
          duration_seconds: duration, resolution, generate_audio: true,
          auth_type: authType, api_key: geminiApiKey || undefined,
        })
        const es = createVideoStatusStream(task_id, authType, geminiApiKey || undefined)
        es.addEventListener('status', (e: MessageEvent) => {
          const data: VideoStatusUpdate = JSON.parse(e.data)
          if (data.status === 'completed' && data.video_url) {
            setStudioResults([data.video_url])
            setLoading(false)
            es.close()
          } else if (data.status === 'failed') {
            setLoading(false)
            es.close()
          }
        })
        es.onerror = () => { setLoading(false); es.close() }
      } else {
        const result = await generateImage({
          prompt, model, aspect_ratio: aspectRatio,
          number_of_images: 1, auth_type: authType,
          api_key: geminiApiKey || undefined,
        })
        setStudioResults(result.images)
        setLoading(false)
      }
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }, [mediaTab, imageModel, videoModel, aspectRatio, duration, resolution, authType, geminiApiKey])

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg)]">
      <Sidebar
        conversations={conversations}
        onNewConversation={handleNewConversation}
        onSelectConversation={setCurrentConversationId}
        onDeleteConversation={handleDeleteConversation}
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden">
          {uiMode === 'chat' ? (
            <ChatView
              messages={messages}
              loading={loading}
              onSendMessage={handleSendMessage}
            />
          ) : (
            <StudioView
              onGenerate={handleStudioGenerate}
              loading={loading}
              results={studioResults}
              mediaType={mediaTab}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  )
}
