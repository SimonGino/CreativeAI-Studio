import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './app/layout/AppLayout'
import { AssetsPage } from './app/pages/AssetsPage'
import { GeneratePage } from './app/pages/GeneratePage'
import { HistoryPage } from './app/pages/HistoryPage'
import { SettingsPage } from './app/pages/SettingsPage'

function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/generate" replace />} />
        <Route path="/generate" element={<GeneratePage />} />
        <Route path="/assets" element={<AssetsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppLayout>
  )
}

export default App
