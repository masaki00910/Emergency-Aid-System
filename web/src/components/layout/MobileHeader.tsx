'use client'

import { usePathname } from 'next/navigation'

interface MobileHeaderProps {
  onToggleSidebar: () => void
}

const pageLabels: Record<string, string> = {
  '/dashboard': 'ダッシュボード',
  '/alerts': 'アラート',
  '/feeds': 'フィード',
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
          <div>
            <h1 className="text-lg font-semibold text-zinc-900">守り雲</h1>
            <p className="text-sm text-zinc-600">{currentPageLabel}</p>
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