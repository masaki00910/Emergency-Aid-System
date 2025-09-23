'use client'

import { useState } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import MobileHeader from '@/components/layout/MobileHeader'
import ErrorBoundary from '@/components/ui/ErrorBoundary'
import { LocationProvider } from '@/contexts/LocationContext'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <LocationProvider>
      <div className="flex h-screen bg-zinc-50">
        {/* デスクトップサイドバー */}
        <Sidebar />

        {/* モバイルサイドバーオーバーレイ */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <div className="absolute inset-0 bg-black/50" />
            <div className="relative w-56 h-full bg-zinc-900">
              <Sidebar />
            </div>
          </div>
        )}

        {/* メインコンテンツエリア */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* モバイルヘッダー */}
          <MobileHeader onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

          {/* メインコンテンツ */}
          <main className="flex-1 overflow-auto">
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </LocationProvider>
  )
}