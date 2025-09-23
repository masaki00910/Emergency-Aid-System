'use client'

import IncidentMap from '@/components/map/IncidentMap'
import AlertSummary from '@/components/dashboard/AlertSummary'
import FeedList from '@/components/feeds/FeedList'
import { API } from '@/lib/api'
import { useState, useEffect } from 'react'
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'
import type { FeedItem } from '@/types/feed'

// Time ago function (same as FeedList)
function timeAgo(ts: string | number) {
  const timestamp = typeof ts === 'string' ? new Date(ts).getTime() : ts
  const diff = Math.max(1, Math.round((Date.now() - timestamp) / 60000))
  if (diff < 60) return `${diff}分前`
  const h = Math.round(diff / 60)
  return `${h}時間前`
}

export default function DashboardPage() {
  const [counts, setCounts] = useState({ active: 0, total: 0 })
  const [highlightFeedId, setHighlightFeedId] = useState<string>()
  const [focusIncidentId, setFocusIncidentId] = useState<string>()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [feeds, setFeeds] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [incidentsData, alertsData, feedsData] = await Promise.all([
          API.getIncidents(),
          API.getAlerts(true), // active alerts only
          API.getFeeds(50)
        ])

        // Filter for 24 hours only
        const now = Date.now()
        const twentyFourHoursAgo = now - (24 * 60 * 60 * 1000)

        // Filter feeds for last 24 hours
        const recentFeeds = feedsData.filter(feed => {
          const feedTime = typeof feed.publishedAt === 'string' 
            ? new Date(feed.publishedAt).getTime() 
            : feed.publishedAt
          return feedTime >= twentyFourHoursAgo
        })

        // Filter alerts for last 24 hours AND active status
        const recentActiveAlerts = alertsData.filter(alert => {
          const alertTime = alert.startedAt
          return alertTime >= twentyFourHoursAgo
        })

        setIncidents(incidentsData)
        setAlerts(recentActiveAlerts)
        setFeeds(recentFeeds)
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
    <div className="p-4 sm:p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">災害情報ダッシュボード</h1>
          {loading && (
            <div className="text-sm text-zinc-600">
              読み込み中...
            </div>
          )}
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-8 space-y-6">
            <div className="rounded-xl border bg-white p-3">
              <IncidentMap
                incidents={incidents}
                onCountsChange={setCounts}
                onSelect={(i) => {
                    if (!i) return
                    const related = feeds.find(f => f.incidentId === i.id)
                    setHighlightFeedId(related?.id)
                }}
                focusIncidentId={focusIncidentId}
                />
            </div>
            <AlertSummary active={alerts.length} today={feeds.length} />

          </div>

          <div className="xl:col-span-4">
            <FeedList 
              items={feeds} 
              highlightId={highlightFeedId} 
              onFeedClick={(feedId) => {
                const feed = feeds.find(f => f.id === feedId)
                console.log('=== Feed Click Debug ===')
                console.log('Clicked feed ID:', feedId)
                console.log('Found feed:', feed)
                console.log('Feed incidentId:', feed?.incidentId)
                console.log('All incidents IDs:', incidents.map(i => i.id))
                console.log('All feeds with incidentId:', feeds.map(f => ({ id: f.id, incidentId: f.incidentId, title: f.title.substring(0, 30) })))
                
                // Strategy 1: Direct incidentId match
                if (feed && feed.incidentId) {
                  console.log('✅ Strategy 1: Using direct incidentId:', feed.incidentId)
                  const foundIncident = incidents.find(i => i.id === feed.incidentId)
                  console.log('Corresponding incident found:', !!foundIncident, foundIncident?.title?.substring(0, 30))
                  if (foundIncident) {
                    setFocusIncidentId(feed.incidentId)
                    setHighlightFeedId(feedId)
                    console.log('=== Success with Strategy 1 ===')
                    return
                  }
                }
                
                // Strategy 2: Same ID (feed.id === incident.id)
                console.log('❌ Strategy 1 failed, trying Strategy 2: Same ID')
                let matchingIncident = incidents.find(incident => incident.id === feedId)
                if (matchingIncident) {
                  console.log('✅ Strategy 2: Found incident with same ID')
                  setFocusIncidentId(matchingIncident.id)
                  setHighlightFeedId(feedId)
                  console.log('=== Success with Strategy 2 ===')
                  return
                }
                
                // Strategy 3: Exact title match
                if (feed?.title) {
                  console.log('❌ Strategy 2 failed, trying Strategy 3: Exact title match')
                  matchingIncident = incidents.find(incident => incident.title === feed.title)
                  if (matchingIncident) {
                    console.log('✅ Strategy 3: Found incident with exact title match')
                    setFocusIncidentId(matchingIncident.id)
                    setHighlightFeedId(feedId)
                    console.log('=== Success with Strategy 3 ===')
                    return
                  }
                }
                
                // Strategy 4: Partial title match
                if (feed?.title) {
                  console.log('❌ Strategy 3 failed, trying Strategy 4: Partial title match')
                  matchingIncident = incidents.find(incident => 
                    incident.title.includes(feed.title.substring(0, 20)) || 
                    feed.title.includes(incident.title.substring(0, 20))
                  )
                  if (matchingIncident) {
                    console.log('✅ Strategy 4: Found incident with partial title match')
                    setFocusIncidentId(matchingIncident.id)
                    setHighlightFeedId(feedId)
                    console.log('=== Success with Strategy 4 ===')
                    return
                  }
                }
                
                // Strategy 5: Area-based matching
                if (feed?.area) {
                  console.log('❌ Strategy 4 failed, trying Strategy 5: Area-based matching')
                  matchingIncident = incidents.find(incident => 
                    incident.location?.admin === feed.area ||
                    incident.location?.admin?.includes(feed.area) ||
                    feed.area.includes(incident.location?.admin || '')
                  )
                  if (matchingIncident) {
                    console.log('✅ Strategy 5: Found incident with area match')
                    setFocusIncidentId(matchingIncident.id)
                    setHighlightFeedId(feedId)
                    console.log('=== Success with Strategy 5 ===')
                    return
                  }
                }
                
                console.log('❌ All strategies failed - no matching incident found')
                console.log('=== End Debug ===')
              }}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-lg text-zinc-900 overflow-hidden">
          <div className="bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 px-6 py-4">
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              🚨 アラート
            </h2>
          </div>
          
          <div className="p-6">
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
                    <li key={a.id} className="rounded-xl border border-slate-200 p-4 bg-white hover:bg-slate-50 hover:shadow-md transition-all duration-300">
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
