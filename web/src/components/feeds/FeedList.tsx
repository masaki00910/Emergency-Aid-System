import type { FeedItem } from '@/types/feed'

function timeAgo(ts: string | number) {
  const timestamp = typeof ts === 'string' ? new Date(ts).getTime() : ts
  const diff = Math.max(1, Math.round((Date.now() - timestamp) / 60000))
  if (diff < 60) return `${diff}分前`
  const h = Math.round(diff / 60)
  return `${h}時間前`
}

export default function FeedList({
  items,
  highlightId,
}: {
  items: FeedItem[]
  highlightId?: string
}) {
  const sorted = [...items].sort((a, b) => {
    if (a.id === highlightId) return -1
    if (b.id === highlightId) return 1
    const aTime = typeof a.publishedAt === 'string' ? new Date(a.publishedAt).getTime() : a.publishedAt
    const bTime = typeof b.publishedAt === 'string' ? new Date(b.publishedAt).getTime() : b.publishedAt
    return bTime - aTime
  })

  return (
    <div className="rounded-xl border bg-white shadow-sm text-zinc-900 p-0">
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur-sm px-4 py-3 border-b">
        <h2 className="text-xl font-semibold">最新フィード</h2>
      </div>
      <ul className="px-4 py-3 space-y-3 max-h-[72vh] overflow-y-auto">
        {sorted.map(f => {
          const hasUrl = f.url && f.url.trim() !== ''
          const FeedContent = hasUrl ? 'a' : 'div'
          const feedProps = hasUrl ? {
            href: f.url,
            target: '_blank',
            rel: 'noopener noreferrer',
            className: `block rounded-lg border p-3 transition-all duration-300 hover:shadow-md hover:bg-gray-50 cursor-pointer ${
              f.id === highlightId ? 'bg-amber-50' : 'bg-white'
            }`
          } : {
            className: `rounded-lg border p-3 transition-all duration-300 ${
              f.id === highlightId ? 'bg-amber-50' : 'bg-white'
            }`
          }

          return (
            <li key={f.id}>
              <FeedContent {...feedProps}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm text-zinc-600 mb-1">
                      {f.source.toUpperCase()} ・ {timeAgo(f.publishedAt)}
                      {hasUrl && <span className="ml-2 text-blue-600">🔗</span>}
                    </div>
                    <div className={`font-medium ${hasUrl ? 'text-blue-600 hover:text-blue-800' : ''}`}>
                      {f.title}
                    </div>
                    {f.content && <p className="text-sm mt-1">{f.content}</p>}
                    <div className="mt-2 flex flex-wrap gap-1">
                      <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-zinc-50 text-zinc-700">
                        {f.category}
                      </span>
                      <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-blue-50 text-blue-700">
                        {f.severity}
                      </span>
                      {/* 🔥 Enhanced Fields Display */}
                      {(f as any).status === 'active' && (
                        <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-red-50 text-red-700">
                          アクティブ
                        </span>
                      )}
                      {(f as any).bulletins_count > 0 && (
                        <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-green-50 text-green-700">
                          公報{(f as any).bulletins_count}件
                        </span>
                      )}
                      {(f as any).affected_population > 0 && (
                        <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-orange-50 text-orange-700">
                          影響{((f as any).affected_population / 1000).toFixed(0)}k人
                        </span>
                      )}
                      {(f as any).risk_assessment && (f as any).risk_assessment !== 'unknown' && (
                        <span className="inline-block rounded-full border px-2 py-0.5 text-xs bg-purple-50 text-purple-700">
                          {(f as any).risk_assessment}リスク
                        </span>
                      )}
                    </div>
                  </div>
                  {f.isVerified && (
                    <span className="text-xs rounded-full bg-green-100 text-green-800 px-2 py-0.5">検証済</span>
                  )}
                </div>
              </FeedContent>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
