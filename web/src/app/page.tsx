'use client'

import IncidentMap from '@/components/map/IncidentMap'
import { useIncidents } from '@/hooks/useIncidents'

export default function DashboardPage() {
 const { incidents, loading, error } = useIncidents()

 return (
  <section className="space-y-4">
   <header className="flex items-center justify-between">
    <h1 className="text-2xl font-semibold">災害情報ダッシュボード</h1>
    <div className="text-sm text-gray-600">リアルタイム更新</div>
   </header>

   {error && (
    <div role="alert" className="rounded-md border p-3 text-red-600">
     {error}
    </div>
   )}

   <IncidentMap incidents={incidents} />

   {loading && (
    <p className="text-sm text-gray-500">最新の災害情報を読み込み中…</p>
   )}

   <ul className="divide-y border rounded-lg">
    {incidents.map(i => (
     <li key={i.id} className="p-3">
      <div className="font-medium">{i.title}</div>
      <div className="text-sm text-gray-500">
       {i.severity ?? 'low'} ・ {i.lat},{i.lng}
      </div>
     </li>
    ))}
    {incidents.length === 0 && !loading && (
     <li className="p-3 text-gray-500 text-sm">現在表示できる災害情報はありません</li>
    )}
   </ul>
  </section>
 )
}
