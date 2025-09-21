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
  onFeedClick,
}: {
  items: FeedItem[]
  highlightId?: string
  onFeedClick?: (feedId: string) => void
}) {
  const sorted = [...items].sort((a, b) => {
    if (a.id === highlightId) return -1
    if (b.id === highlightId) return 1
    const aTime = typeof a.publishedAt === 'string' ? new Date(a.publishedAt).getTime() : a.publishedAt
    const bTime = typeof b.publishedAt === 'string' ? new Date(b.publishedAt).getTime() : b.publishedAt
    return bTime - aTime
  })

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-lg text-zinc-900 overflow-hidden">
      <div className="sticky top-0 z-10 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 px-6 py-4">
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          📡 最新フィード
        </h2>
      </div>
      <ul className="px-6 py-4 space-y-4 max-h-[72vh] overflow-y-auto">
        {sorted.map(f => (
          <li
            key={f.id}
            onClick={() => onFeedClick?.(f.id)}
            className={`rounded-xl border border-slate-200 p-4 transition-all duration-300 hover:shadow-md cursor-pointer ${
              f.id === highlightId 
                ? 'bg-gradient-to-r from-amber-50 to-amber-100 border-amber-300 shadow-md' 
                : 'bg-white hover:bg-slate-50'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                  <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                    📰 {f.source.toUpperCase()}
                  </span>
                  <span>・</span>
                  <span className="text-xs">{timeAgo(f.publishedAt)}</span>
                </div>
                <div className="font-semibold text-slate-900 text-base leading-snug mb-2">
                  {f.title}
                </div>
                {f.content && <p className="text-sm text-slate-600 leading-relaxed mt-2">{f.content}</p>}
                <div className="mt-3 flex flex-wrap gap-2">
                  {f.category && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-slate-100 to-slate-200 px-3 py-1 text-xs font-medium text-slate-700 shadow-sm">
                      🏷️ {f.category}
                    </span>
                  )}
                  {f.severity && (
                    <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium shadow-sm ${
                      f.severity === 'high' 
                        ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800' 
                        : f.severity === 'medium'
                        ? 'bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800'
                        : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
                    }`}>
                      📊 深刻度：{f.severity === 'high' ? '高' : f.severity === 'medium' ? '中' : '低'}
                    </span>
                  )}
                  {/* 🔥 Enhanced Fields Display - Modern Design */}
                  {f.status === 'active' && f.severity !== 'low' && f.category !== 'その他' && f.category !== '' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-red-500 to-red-600 px-3 py-1 text-xs font-medium text-white shadow-md">
                      🚨 アクティブ
                    </span>
                  )}
                  {f.risk_assessment && f.risk_assessment !== 'unknown' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-purple-100 to-purple-200 px-3 py-1 text-xs font-medium text-purple-800 shadow-sm">
                      ⚠️ {f.risk_assessment}リスク
                    </span>
                  )}
                  {f.has_analysis && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-indigo-100 to-indigo-200 px-3 py-1 text-xs font-medium text-indigo-800 shadow-sm">
                      🔍 分析済
                    </span>
                  )}
                  {f.has_collected_info && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-teal-100 to-teal-200 px-3 py-1 text-xs font-medium text-teal-800 shadow-sm">
                      📊 情報収集済
                    </span>
                  )}
                </div>
              </div>
              {f.isVerified && (
                <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-600 px-3 py-1 text-xs font-medium text-white shadow-md">
                  ✅ 検証済
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
