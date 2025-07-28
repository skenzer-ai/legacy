import { Routes, Route } from 'react-router-dom'
import { useThemeStore } from '@/stores/theme'
import { useSettingsStore } from '@/stores/settings'
import { useEffect } from 'react'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import ServiceDetail from '@/pages/ServiceDetail'
import ApiTesting from '@/pages/ApiTesting'
import Knowledge from '@/pages/Knowledge'
import Analytics from '@/pages/Analytics'
import Settings from '@/pages/Settings'

function App() {
  const { theme, initializeTheme } = useThemeStore()
  const { loadSettings } = useSettingsStore()

  useEffect(() => {
    initializeTheme()
    loadSettings()
  }, [initializeTheme, loadSettings])

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/services" element={<Dashboard />} />
        <Route path="/services/:serviceId" element={<ServiceDetail />} />
        <Route path="/testing" element={<ApiTesting />} />
        <Route path="/knowledge" element={<Knowledge />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App