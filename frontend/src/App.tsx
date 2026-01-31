import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import ChatPage from './pages/ChatPage'
import ModelConfigPage from './pages/ModelConfigPage'
import ProfilePage from './pages/ProfilePage'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route
            path="/model-config"
            element={isAuthenticated ? <ModelConfigPage /> : <Navigate to="/" replace />}
          />
          <Route
            path="/profile"
            element={isAuthenticated ? <ProfilePage /> : <Navigate to="/" replace />}
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
