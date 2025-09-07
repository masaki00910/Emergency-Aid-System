import type { FeedItem } from '@/types/feed'

function timeAgo(ts: number) {
  const diff = Math.max(1, Math.round((Date.now() - ts) / 60000))
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
    return b.publishedAt - a.publishedAt
  })

  return (
    <div className="rounded-xl border bg-white shadow-sm text-zinc-900 p-0">
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur-sm px-4 py-3 border-b">
        <h2 className="text-xl font-semibold">最新フィード</h2>
      </div>
      <ul className="px-4 py-3 space-y-3 max-h-[72vh] overflow-y-auto">
        {sorted.map(f => (
          <li
            key={f.id}
            className={`rounded-lg border p-3 transition-all duration-300 ${
              f.id === highlightId ? 'bg-amber-50' : 'bg-white'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm text-zinc-600 mb-1">
                  {f.source.toUpperCase()} ・ {timeAgo(f.publishedAt)}
                </div>
                <a className="font-medium hover:underline" href={f.url} target="_blank" rel="noreferrer">
                  {f.title}
                </a>
                {f.summary && <p className="text-sm mt-1">{f.summary}</p>}
                {f.labels && f.labels.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {f.labels.map(l => (
                      <span key={l} className="inline-block rounded-full border px-2 py-0.5 text-xs bg-zinc-50 text-zinc-700">
                        {l}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {f.isAlertCandidate && (
                <span className="text-xs rounded-full bg-amber-100 text-amber-800 px-2 py-0.5">要確認</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
