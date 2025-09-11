import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Disaster Response System',
  description: 'リアルタイム災害情報ダッシュボード',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="min-h-dvh bg-zinc-100 text-zinc-900 antialiased">{children}</body>
    </html>
  )
}
