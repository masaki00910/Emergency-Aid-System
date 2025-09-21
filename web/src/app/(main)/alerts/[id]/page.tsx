'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { API } from '@/lib/api'
import GoogleMap from '@/components/GoogleMap'
import type { Alert, Incident, FeedItem } from '@/lib/api'

interface TimelineEvent {
  id: string
  time: string
  title: string
  source: string
  isAlert?: boolean
}

export default function AlertDetailPage() {
  const params = useParams()
  const alertId = params.id as string
  
  const [alert, setAlert] = useState<Alert | null>(null)
  const [incident, setIncident] = useState<Incident | null>(null)
  const [relatedFeeds, setRelatedFeeds] = useState<FeedItem[]>([])
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAlertData = async () => {
      try {
        setLoading(true)

        // Fetch data directly as incident since all our data comes from disasters API
        let foundAlert: Alert | null = null

        try {
          const incidentData = await API.getIncident(alertId)
          if (incidentData) {
            setIncident(incidentData)
            // Convert incident to alert format for display
            foundAlert = {
              id: incidentData.id,
              title: incidentData.title,
              level: incidentData.severity === 'high' ? 'warning' as const : incidentData.severity === 'medium' ? 'watch' as const : 'info' as const,
              area: incidentData.location?.admin || 'Unknown Area',
              hazard: incidentData.type as 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'other',
              startedAt: new Date(incidentData.reported_at).getTime(),
              description: incidentData.description,
              summary: incidentData.description
            }
          }
        } catch (error) {
          console.error('Failed to fetch incident data:', error)
        }

        if (foundAlert) {
          setAlert(foundAlert)

          // Try to find related feeds
          try {
            const related = await API.getFeedsByIncident(alertId)
            setRelatedFeeds(related)

            // Generate timeline from feeds, evidence, and alert info
            const timelineEvents: TimelineEvent[] = [
              {
                id: 'alert-start',
                time: new Date(foundAlert.startedAt).toLocaleString('ja-JP'),
                title: `${foundAlert.title}の発生`,
                source: 'システム',
                isAlert: true
              },
              ...related.map(feed => ({
                id: feed.id,
                time: new Date(feed.publishedAt).toLocaleString('ja-JP'),
                title: feed.title,
                source: feed.source,
                isAlert: false
              })),
              ...(incident?.evidence?.map(evidence => ({
                id: `evidence-${evidence.hash}`,
                time: new Date(evidence.timestamp).toLocaleString('ja-JP'),
                title: evidence.title || 'ニュース報告',
                source: evidence.source,
                isAlert: false
              })) || [])
            ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())

            setTimeline(timelineEvents)
          } catch (error) {
            console.warn('Failed to fetch related feeds:', error)
            // Create minimal timeline with just the alert
            setTimeline([{
              id: 'alert-start',
              time: new Date(foundAlert.startedAt).toLocaleString('ja-JP'),
              title: `${foundAlert.title}の発生`,
              source: '気象庁API',
              isAlert: true
            }])
          }
        }
      } catch (error) {
        console.error('Failed to fetch alert data:', error)
      } finally {
        setLoading(false)
      }
    }

    if (alertId) {
      fetchAlertData()
    }
  }, [alertId])

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center">読み込み中...</div>
      </div>
    )
  }

  if (!alert) {
    return (
      <div className="p-6">
        <div className="text-center">アラートが見つかりません</div>
      </div>
    )
  }

  const getHazardIcon = (hazard: string) => {
    switch(hazard) {
      case 'flood': case '大雨': return '🌧️'
      case 'earthquake': case '地震': return '🔴'
      case 'typhoon': case '台風': return '🌀'
      case 'landslide': case '土砂災害': return '⛰️'
      case 'tsunami': case '津波': return '🌊'
      default: return '⚠️'
    }
  }

  const getTagColor = (tag: string) => {
    switch(tag) {
      case 'flood': case '大雨': return 'bg-blue-100 text-blue-800'
      case 'earthquake': case '地震': return 'bg-red-100 text-red-800'
      case 'typhoon': case '台風': return 'bg-purple-100 text-purple-800'
      case 'landslide': case '土砂災害': return 'bg-yellow-100 text-yellow-800'
      case 'tsunami': case '津波': return 'bg-cyan-100 text-cyan-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // Create incident for map display - using real location data if available
  const mapIncident = {
    id: alert.id,
    lat: incident?.location?.lat || 35.6762, // Use real coordinates or default to Tokyo
    lng: incident?.location?.lng || 139.6503,
    title: alert.title,
    isActive: alert.level === 'warning' || alert.level === 'emergency'
  }

  return (
    <div className="p-4 sm:p-6 space-y-6">
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-2xl font-bold mb-2">詳細</h1>
          
          {/* Alert Status Banner */}
          <div className={`border-l-4 p-4 mb-4 ${alert.level === 'warning' || alert.level === 'emergency' ? 'bg-red-50 border-red-500' : 'bg-gray-50 border-gray-400'}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 rounded text-sm font-semibold ${alert.level === 'warning' || alert.level === 'emergency' ? 'bg-red-500 text-white' : 'bg-gray-400 text-white'}`}>
                    {alert.level === 'warning' || alert.level === 'emergency' ? 'Active Alert' : 'non-Active Alert'}
                  </span>
                  <span className="text-2xl">{getHazardIcon(alert.hazard)}</span>
                </div>
                <div className="text-xl font-bold text-red-800">{alert.title}</div>
                <div className="text-sm text-red-600">
                  {new Date(alert.startedAt).toLocaleString('ja-JP')}
                </div>
              </div>
              <div className="text-right text-sm text-red-600">
                Alert ID: {alert.id}
              </div>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Map */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">位置情報</h3>
              <div className="h-64 bg-gray-100 rounded-lg overflow-hidden">
                <GoogleMap
                  lat={incident?.location?.lat || 35.6762}
                  lng={incident?.location?.lng || 139.6503}
                  incidents={[mapIncident]}
                />
              </div>
            </div>

            {/* Location Details */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">地域・エリア</h3>
              <div className="text-sm text-gray-600 leading-relaxed">
                {alert.area}
              </div>
            </div>

            {/* Tags */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">タグ</h3>
              <div className="flex flex-wrap gap-2">
                <span className={`px-3 py-1 rounded-full text-sm ${getTagColor(alert.hazard)}`}>
                  {alert.hazard === 'flood' ? '大雨' : 
                   alert.hazard === 'earthquake' ? '地震' :
                   alert.hazard === 'typhoon' ? '台風' :
                   alert.hazard === 'landslide' ? '土砂災害' :
                   alert.hazard === 'tsunami' ? '津波' : alert.hazard}
                </span>
                <span className="px-3 py-1 rounded-full text-sm bg-orange-100 text-orange-800">
                  警報
                </span>
                <span className="px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800">
                  レベル: {incident?.severity || alert.level}
                </span>
              </div>
            </div>

            {/* Alert Overview */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">アラート概要</h3>
              <div className="space-y-4 text-sm">
                <p>
                  {alert.description || `${alert.area}で${alert.hazard}に関するアラートが発表されています。`}
                </p>

                {incident && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-blue-800">詳細情報</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>信頼度: {Math.round((incident.confidence || 0) * 100)}%</div>
                      <div>ステータス: {incident.status}</div>
                      <div>情報源: {incident.source?.join(', ')}</div>
                      <div>位置: {incident.location?.lat?.toFixed(3)}, {incident.location?.lng?.toFixed(3)}</div>
                      {incident.affected_population !== undefined && (
                        <div>影響人口: {incident.affected_population.toLocaleString()}人</div>
                      )}
                      {incident.risk_assessment && incident.risk_assessment !== 'unknown' && (
                        <div>リスク評価: {incident.risk_assessment}</div>
                      )}
                    </div>
                  </div>
                )}

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">注意事項</h4>
                  <ul className="space-y-1 text-xs">
                    <li>• 最新の情報を確認してください</li>
                    <li>• 避難指示が出た場合は速やかに避難してください</li>
                    <li>• 危険な場所には近づかないでください</li>
                    <li>• 緊急時は119番または110番に連絡してください</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Timeline */}
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
              <h3 className="text-lg font-semibold mb-4">Timeline</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {timeline.map((event, index) => (
                  <div key={event.id} className="text-xs">
                    <div className="font-medium text-gray-700">{event.time}</div>
                    <div className={`mt-1 ${event.isAlert ? 'font-semibold text-red-700' : 'text-gray-600'}`}>
                      {event.title}
                      {event.isAlert && <span className="ml-2 text-red-500">📍</span>}
                    </div>
                    <div className="text-gray-500 mt-1">{event.source}</div>
                    {index < timeline.length - 1 && <div className="border-b border-yellow-200 mt-2"></div>}
                  </div>
                ))}
              </div>
            </div>

            {/* FAQ */}
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
              <h3 className="text-lg font-semibold mb-4">FAQ</h3>
              
              <div className="space-y-3">
                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    大雨の時の注意点は？
                  </summary>
                  <ul className="text-xs text-gray-600 space-y-1 pl-4">
                    <li>• 浸水や土砂災害に備えるため危険な場所は避ける</li>
                    <li>• 河川や用水路には近づかない</li>
                    <li>• 地下やアンダーパスの利用を避ける</li>
                    <li>• 車での移動は控える</li>
                  </ul>
                </details>

                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    避難するタイミングは？
                  </summary>
                  <div className="text-xs text-gray-600 pl-4">
                    避難勧告や避難指示が発表されたタイミング、または
                    危険を感じた時は躊躇せずに避難してください。
                  </div>
                </details>

                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    緊急時の連絡先は？
                  </summary>
                  <div className="text-xs text-gray-600 pl-4">
                    消防・救急: 119番<br />
                    警察: 110番<br />
                    市町村防災担当課へもご連絡ください
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>
    </div>
  )
}