'use client'

import IncidentMap from '@/components/map/IncidentMap'
import AlertSummary from '@/components/dashboard/AlertSummary'
import { API } from '@/lib/api'
import { useState, useEffect } from 'react'
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'
import { useLocation } from '@/contexts/LocationContext'
import { formatDistance } from '@/lib/geocoding'

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
  const [rawIncidents, setRawIncidents] = useState<Incident[]>([]) // Raw data from API
  const [incidents, setIncidents] = useState<Incident[]>([]) // Sorted data for display
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  // Location context
  const { userLocation, isLoading: locationLoading, error: locationError } = useLocation()

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

        // Store raw data
        setRawIncidents(incidentsData)
        setAlerts(recentActiveAlerts)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Fallback to empty arrays or show error state
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, []) // Only run once on mount

  // Sort incidents when user location or raw data changes
  useEffect(() => {
    if (rawIncidents.length > 0) {
      if (userLocation) {
        const sortedIncidents = rawIncidents
          .map(incident => ({
            ...incident,
            distance: incident.location ?
              Math.sqrt(
                Math.pow(userLocation.lat - incident.location.lat, 2) +
                Math.pow(userLocation.lng - incident.location.lng, 2)
              ) * 111 : Infinity // rough km conversion
          }))
          .sort((a, b) => (a as any).distance - (b as any).distance)
        setIncidents(sortedIncidents)
      } else {
        setIncidents(rawIncidents)
      }
    }
  }, [userLocation, rawIncidents]) // Re-sort when location changes

  return (
    <div className="p-4 sm:p-6 space-y-8 min-h-screen">
        <header className="flex items-center justify-between mb-2 animate-fade-in">
          <div>
            <h1 className="text-4xl font-bold gradient-text animate-float">災害情報ダッシュボード</h1>
            {userLocation && (
              <p className="text-sm text-slate-600 mt-2">
                📍 現在位置: {userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}
                {locationError && <span className="text-orange-600 ml-2">⚠️ 位置情報取得に問題があります</span>}
              </p>
            )}
          </div>
          {(loading || locationLoading) && (
            <div className="text-sm text-zinc-600">
              読み込み中...
            </div>
          )}
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-8 space-y-8">
            <div className="rounded-2xl glass-effect card-hover p-6 shadow-lg animate-slide-up animate-stagger-1 pulse-glow">
              <IncidentMap
                incidents={rawIncidents}
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
                    {incidents.slice(0, 10).map((incident: any) => (
                      <div
                        key={incident.id}
                        onClick={() => {
                          setFocusIncidentId(incident.id)
                          // Find the incident in rawIncidents to ensure we have location data
                          const targetIncident = rawIncidents.find(i => i.id === incident.id)
                          if (targetIncident?.location) {
                            // This will trigger the map to focus on this incident
                            setFocusIncidentId(targetIncident.id)
                          }
                        }}
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
                            <div className="flex items-center justify-between mb-2">
                              <p className="text-sm text-slate-600">
                                {incident.location?.admin}
                              </p>
                              {userLocation && incident.distance !== undefined && (
                                <span className="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded-full">
                                  📍 {formatDistance(incident.distance)}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500">
                              {timeAgo(incident.reported_at)}
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

        {/* FAQ Reference Note */}
        <div className="mt-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
            <span>💡</span>
            <span>このシステムの使い方を知りたい場合はFAQを参照して下さい</span>
          </div>
        </div>
    </div>
  )
}
