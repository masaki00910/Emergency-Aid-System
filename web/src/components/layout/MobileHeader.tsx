'use client'

import { usePathname } from 'next/navigation'

interface MobileHeaderProps {
  onToggleSidebar: () => void
}

const pageLabels: Record<string, string> = {
  '/dashboard': 'ダッシュボード',
  '/alerts': 'アラート',
  '/faq': 'よくある質問'
}

export default function MobileHeader({ onToggleSidebar }: MobileHeaderProps) {
  const pathname = usePathname()
  const currentPageLabel = pageLabels[pathname] || 'ページ'

  return (
    <header className="md:hidden bg-white border-b border-zinc-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg hover:bg-zinc-100 transition-colors"
            aria-label="メニューを開く"
          >
            <svg className="w-6 h-6 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 via-cyan-400 to-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Aigis</h1>
              <p className="text-sm text-zinc-600">{currentPageLabel}</p>
            </div>
          </div>
        </div>

        {/* 通知アイコン */}
        <button className="p-2 rounded-lg hover:bg-zinc-100 transition-colors relative">
          <svg className="w-6 h-6 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM10.5 7.5L16 13l-5.5 5.5V15H8l2.5-2.5z" />
          </svg>
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            3
          </span>
        </button>
      </div>
    </header>
  )
}