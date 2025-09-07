'use client'

import Sidebar from '@/components/layout/Sidebar'
import IncidentMap from '@/components/map/IncidentMap'
import AlertSummary from '@/components/dashboard/AlertSummary'
import FeedList from '@/components/feeds/FeedList'

import { mockIncidents, mockAlerts, mockFeeds } from '@/mocks/data'

export default function DashboardPage() {
  const incidents = mockIncidents
  const alerts = mockAlerts
  const feeds = mockFeeds

  return (
    <div className="md:flex">
      <Sidebar />

      <section className="flex-1 p-4 sm:p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">災害情報ダッシュボード</h1>
          <div className="text-sm text-zinc-600">リアルタイム更新</div>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* 메인(지도 + 카드) */}
          <div className="xl:col-span-8 space-y-6">
            {/* 지도 */}
            <div className="rounded-xl border bg-white p-3">
              <IncidentMap incidents={incidents} />
            </div>

            {/* 요약 카드 */}
            <AlertSummary active={alerts.length} today={incidents.length} />
          </div>

          {/* 우측 피드 */}
          <div className="xl:col-span-4">
            <FeedList items={feeds} />
          </div>
        </div>

        {/* 알림 리스트(간단) */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <h2 className="text-xl font-semibold mb-3">アラート</h2>
          <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {alerts.map(a => (
              <li key={a.id} className="rounded-lg border p-3">
                <div className="text-sm text-zinc-500">{a.area}</div>
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
