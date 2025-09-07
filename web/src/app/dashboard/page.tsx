'use client'

import Sidebar from '@/components/layout/Sidebar'
import IncidentMap from '@/components/map/IncidentMap'
import AlertSummary from '@/components/dashboard/AlertSummary'
import FeedList from '@/components/feeds/FeedList'
import { mockIncidents, mockAlerts, mockFeeds } from '@/mocks/data'
import { useState } from 'react'
import type { Incident } from '@/types/incident'

export default function DashboardPage() {
  const [counts, setCounts] = useState({ active: 0, total: 0 })
  const [selected, setSelected] = useState<Incident | null>(null)
  const [highlightFeedId, setHighlightFeedId] = useState<string>()
  return (
    <div className="md:flex">
      <Sidebar />
      <section className="flex-1 p-4 sm:p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">災害情報ダッシュボード</h1>
          <div className="text-sm text-zinc-600">リアルタイム更新</div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-8 space-y-6">
            <div className="rounded-xl border bg-white p-3">
              <IncidentMap
                incidents={mockIncidents}
                onCountsChange={setCounts}
                onSelect={(i) => {
                    if (!i) return
                    setSelected(i)
                    const related = mockFeeds.find(f => f.incidentId === i.id)
                    setHighlightFeedId(related?.id)
                }}
                />
            </div>
            <AlertSummary active={counts.active} today={counts.total} />

            {selected && (
              <div className="rounded-xl border bg-white p-4 shadow-sm text-zinc-900">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm text-zinc-600">{selected.area ?? '—'}</div>
                    <div className="text-lg font-semibold">{selected.title}</div>
                    <div className="mt-1 text-sm">
                      種別: {selected.hazard ?? '—'} / 重要度: {selected.severity ?? '—'}
                    </div>
                    <div className="mt-1 text-xs text-zinc-600">
                      {selected.reportedAt ? new Date(selected.reportedAt).toLocaleString() : ''}
                      {' ・ '}
                      {selected.lat.toFixed(3)}, {selected.lng.toFixed(3)}
                    </div>
                    {selected.description && <p className="mt-2 text-sm">{selected.description}</p>}
                  </div>
                  <button
                    className="text-sm text-zinc-600 hover:text-zinc-900"
                    onClick={() => setSelected(null)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="xl:col-span-4">
            <FeedList items={mockFeeds} highlightId={highlightFeedId} />
          </div>
        </div>

        <div className="rounded-xl border bg-white p-4 shadow-sm text-zinc-900">
          <h2 className="text-xl font-semibold mb-3">アラート</h2>
          <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {mockAlerts.map(a => (
              <li key={a.id} className="rounded-lg border p-3">
                <div className="text-sm text-zinc-600">{a.area}</div>
                <div className="font-medium">{a.title}</div>
                <div className="mt-1 text-xs text-zinc-600">
                  {new Date(a.startedAt).toLocaleString()} ・ {a.hazard}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  )
}
