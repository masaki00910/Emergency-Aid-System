'use client'

import IncidentMap from '@/components/map/IncidentMap'
import AlertSummary from '@/components/dashboard/AlertSummary'
import { API } from '@/lib/api'
import { useState, useEffect } from 'react'
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'

// Time ago helper function
function timeAgo(ts: string | number) {
  const timestamp = typeof ts === 'string' ? new Date(ts).getTime() : ts
  const diff = Math.max(1, Math.round((Date.now() - timestamp) / 60000))
  if (diff < 60) return `${diff}分前`
  const h = Math.round(diff / 60)
  return `${h}時間前`
}

export default function DashboardPage() {
  const [counts, setCounts] = useState({ active: 0, total: 0 })
  const [focusIncidentId, setFocusIncidentId] = useState<string>()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [incidentsData, alertsData] = await Promise.all([
          API.getIncidents(),
          API.getAlerts(true), // active alerts only
        ])

        // Filter for 24 hours only
        const now = Date.now()
        const twentyFourHoursAgo = now - (24 * 60 * 60 * 1000)

        // Filter alerts for last 24 hours AND active status
        const recentActiveAlerts = alertsData.filter(alert => {
          const alertTime = alert.startedAt
          return alertTime >= twentyFourHoursAgo
        })

        setIncidents(incidentsData)
        setAlerts(recentActiveAlerts)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Fallback to empty arrays or show error state
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="p-4 sm:p-6 space-y-8 min-h-screen">
        <header className="flex items-center justify-between mb-2 animate-fade-in">
          <h1 className="text-4xl font-bold gradient-text animate-float">災害情報ダッシュボード</h1>
          {loading && (
            <div className="text-sm text-zinc-600">
              読み込み中...
            </div>
          )}
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-8 space-y-8">
            <div className="rounded-2xl glass-effect card-hover p-6 shadow-lg animate-slide-up animate-stagger-1 pulse-glow">
              <IncidentMap
                incidents={incidents}
                onCountsChange={setCounts}
                onSelect={setFocusIncidentId}
                focusIncidentId={focusIncidentId}
                />
            </div>
            <div className="card-hover animate-slide-up animate-stagger-2">
              <AlertSummary active={alerts.length} today={incidents.length} />
            </div>

          </div>

          <div className="xl:col-span-4 animate-slide-up animate-stagger-3">
            <div className="rounded-3xl glass-effect shadow-2xl text-zinc-900 overflow-hidden card-hover border-0">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100 px-6 py-4">
                <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent flex items-center gap-2">
                  📍 最近のインシデント
                </h2>
              </div>

              <div className="p-6 max-h-96 overflow-y-auto">
                {loading ? (
                  <div className="text-center py-8 text-slate-600">
                    <div className="inline-flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600"></div>
                      読み込み中...
                    </div>
                  </div>
                ) : incidents.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <div className="text-4xl mb-3">🌅</div>
                    <div className="text-lg font-medium mb-2">インシデントなし</div>
                    <div className="text-sm">平穏な状況です</div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {incidents.slice(0, 10).map(incident => (
                      <div
                        key={incident.id}
                        onClick={() => setFocusIncidentId(incident.id)}
                        className={`p-4 rounded-xl glass-effect cursor-pointer transition-all duration-300 ${
                          focusIncidentId === incident.id
                            ? 'ring-2 ring-blue-500 shadow-lg'
                            : 'hover:shadow-md'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-3 h-3 rounded-full bg-gradient-to-r from-orange-400 to-red-500 mt-2 flex-shrink-0"></div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-slate-900 line-clamp-2 mb-1">
                              {incident.title}
                            </h3>
                            <p className="text-sm text-slate-600 mb-2">
                              {incident.location?.admin}
                            </p>
                            <div className="text-xs text-slate-500">
                              {timeAgo(incident.timestamp)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl glass-effect shadow-2xl text-zinc-900 overflow-hidden card-hover border-0 animate-slide-up animate-stagger-4">
          <div className="bg-gradient-to-r from-red-50 to-orange-50 border-b border-red-100 px-8 py-6">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent flex items-center gap-3 animate-float-delayed">
              🚨 アラート
            </h2>
          </div>
          
          <div className="p-8">
            {loading ? (
              <div className="text-center py-8 text-slate-600">
                <div className="inline-flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600"></div>
                  読み込み中...
                </div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <div className="text-4xl mb-3">📭</div>
                <div className="text-lg font-medium mb-2">現在有効なアラートはありません</div>
                <div className="text-sm">システムが正常に動作しています</div>
              </div>
            ) : (
              <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {alerts.map(a => {
                  // Get hazard info for consistent styling
                  const hazardMapping: Record<string, {name: string, icon: string}> = {
                    'earthquake': {name: '地震', icon: '🌍'},
                    'tsunami': {name: '津波', icon: '🌊'}, 
                    'flood': {name: '洪水', icon: '💧'},
                    'typhoon': {name: '台風', icon: '🌀'},
                    'landslide': {name: '土砂災害', icon: '⛰️'},
                    'volcano': {name: '火山', icon: '🌋'},
                    'wildfire': {name: '山火事', icon: '🔥'},
                    'other': {name: 'その他', icon: '⚠️'}
                  }
                  const hazardInfo = hazardMapping[a.hazard] || hazardMapping['other']
                  
                  return (
                    <li key={a.id} className="rounded-2xl glass-effect p-6 card-hover shadow-lg border-0">
                      <div className="flex items-center gap-2 text-sm text-slate-600 mb-3">
                        <span className="text-lg">{hazardInfo.icon}</span>
                        <span className="font-medium">{a.area}</span>
                      </div>
                      
                      <div className="font-semibold text-slate-900 text-base leading-snug mb-3">
                        {a.title}
                      </div>
                      
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-slate-100 to-slate-200 px-3 py-1 text-xs font-medium text-slate-700 shadow-sm">
                          🏷️ {hazardInfo.name}
                        </span>
                        <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium shadow-sm ${
                          a.level === 'emergency' 
                            ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800' 
                            : a.level === 'warning'
                            ? 'bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800'
                            : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
                        }`}>
                          📊 深刻度：{a.level === 'emergency' ? '高' : a.level === 'warning' ? '中' : '低'}
                        </span>
                      </div>
                      
                      <div className="text-xs text-slate-500 flex items-center gap-1">
                        🕒 {timeAgo(a.startedAt)}
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </div>
    </div>
  )
}
