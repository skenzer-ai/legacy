import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          
          {/* Page content */}
          <main className="flex-1 overflow-y-auto">
            <div className="container-wide py-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}