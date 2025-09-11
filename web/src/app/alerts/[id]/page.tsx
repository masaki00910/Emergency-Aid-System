'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { mockAlerts, mockIncidents, mockFeeds } from '@/mocks/data'
import GoogleMap from '@/components/GoogleMap'

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
  
  interface ExtendedAlert {
    id: string
    title: string
    level: string
    hazard: string
    area: string
    startedAt: number
    lat?: number
    lng?: number
    isActive?: boolean
  }
  
  const [alert, setAlert] = useState<ExtendedAlert | null>(null)
  const [relatedFeeds, setRelatedFeeds] = useState<typeof mockFeeds>([])
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])

  useEffect(() => {
    // Find alert by ID (search both alerts and incidents)
    let foundAlert: ExtendedAlert | undefined = mockAlerts.find(a => a.id === alertId) as ExtendedAlert | undefined
    const foundIncident = mockIncidents.find(i => i.id === alertId)
    
    if (!foundAlert && foundIncident) {
      // Convert incident to alert format for display
      foundAlert = {
        id: foundIncident.id,
        title: foundIncident.title,
        level: foundIncident.severity === 'high' ? 'warning' : 
               foundIncident.severity === 'medium' ? 'watch' : 'info',
        hazard: foundIncident.hazard || 'other',
        area: foundIncident.area || '',
        startedAt: foundIncident.reportedAt || Date.now(),
        lat: foundIncident.lat,
        lng: foundIncident.lng,
        isActive: foundIncident.isActive
      } as ExtendedAlert
    }
    
    if (foundAlert) {
      setAlert(foundAlert)
      
      // Find related feeds
      const related = mockFeeds.filter(feed => feed.incidentId === alertId)
      setRelatedFeeds(related)
      
      // Generate timeline from feeds and alert info
      const timelineEvents: TimelineEvent[] = [
        {
          id: 'alert-start',
          time: new Date(foundAlert.startedAt).toLocaleString('ja-JP'),
          title: `${foundAlert.title}の発生`,
          source: '気象庁API',
          isAlert: true
        },
        ...related.map(feed => ({
          id: feed.id,
          time: new Date(feed.publishedAt).toLocaleString('ja-JP'),
          title: feed.title,
          source: feed.source === 'jma' ? '気象庁' : 
                 feed.source === 'nhk' ? 'NHK' : 
                 feed.source === 'tenki' ? 'tenki.jp' : 
                 feed.source === 'x' ? 'X(Twitter)' : 'ニュース',
          isAlert: false
        }))
      ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
      
      setTimeline(timelineEvents)
    }
  }, [alertId])

  if (!alert) {
    return (
      <div className="md:flex">
        <Sidebar />
        <div className="flex-1 p-6">
          <div className="text-center">アラートが見つかりません</div>
        </div>
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

  return (
    <div className="md:flex">
      <Sidebar />
      
      <section className="flex-1 p-4 sm:p-6 space-y-6">
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-2xl font-bold mb-2">詳細</h1>
          
          {/* Alert Status Banner */}
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="bg-red-500 text-white px-2 py-1 rounded text-sm font-semibold">
                    Active Alert
                  </span>
                  <span className="text-2xl">{getHazardIcon(alert.hazard)}</span>
                </div>
                <div className="text-xl font-bold text-red-800">{alert.title}</div>
                <div className="text-sm text-red-600">
                  {new Date(alert.startedAt).toLocaleString('ja-JP')}
                </div>
              </div>
              <div className="text-right text-sm text-red-600">
                Alert ID: {alert.id.padStart(6, '0')}
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
                  lat={alert.lat || 35.6762}
                  lng={alert.lng || 139.6503}
                  incidents={alert.lat && alert.lng ? [{
                    id: alert.id,
                    lat: alert.lat,
                    lng: alert.lng,
                    title: alert.title,
                    isActive: alert.isActive !== false
                  }] : []}
                />
              </div>
            </div>

            {/* Location Details */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">地域・エリア</h3>
              <div className="text-sm text-gray-600 leading-relaxed">
                {alert.area}地区、{alert.area}北部、{alert.area}中央区、
                {alert.area}東大阪市、{alert.area}府内各市町、{alert.area}
                府南本市、…、{alert.area}府東中市、…、兵庫県
                神戸市、兵庫県明石市、兵庫県尼崎市、兵庫県西宮市
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
                  注意報に注意し、周辺や今後の状況を確認することをお勧めします。
                </span>
                <span className="px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800">
                  上記災害情報を参考に適切な予防措置をとり避難することを心がけてください。
                </span>
              </div>
            </div>

            {/* Alert Overview */}
            <div className="bg-white rounded-xl border p-6">
              <h3 className="text-lg font-semibold mb-4">アラート概要</h3>
              <div className="space-y-4 text-sm">
                <p>
                  2025年8月27日0時30分から28日06時まで
                  {alert.area}府各各市を中心に1時間あたり50～80mmの猛烈な雨が予想されています。
                  猛雨量は最大200mmに達する見込みで、土砂災害重点地域や中小河川での氾濫発生の危険性が
                  高まる可能性があります。
                </p>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">備考</h4>
                  <ul className="space-y-1 text-xs">
                    <li><span className="font-medium">a) 政府PDFのQCR →</span> 現実的にFAQみたいな回答作成をなぞそう</li>
                    <li><span className="font-medium">b) △州PDFのマニュアル →</span> 各連絡機関とのつながり</li>
                    <li><span className="font-medium">c) 災害とその対策</span>(運搬例、避難経路例、物資補給、ライフライン復旧、デマ対策、FAQ発行等)</li>
                    <li><span className="font-medium">→ Alert詳細においてある？</span> (おそらくの避難場所案内・文書接続・障害復旧など)</li>
                    <li><span className="font-medium">→ 対策のページを到達再現するのもできる</span>が、Alertに基本的にともなう？</li>
                    <li><span className="font-medium">サポートAgent:</span> 経済・心理状況の可視化</li>
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
                    <li>• 浸水や土砂災害にそなえるため危険な場所は避ける</li>
                    <li>• 河川や用水路には近づかない</li>
                    <li>• 地下や半ヤマザメ（アンダーパス）使用禁止</li>
                    <li>• クルマ要藏による水漂流危険場所の高</li>
                    <li>雨・緊急避難でバス以外への転載をする</li>
                  </ul>
                </details>

                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    「土砂災害警報」や「土砂災害危険」
                  </summary>
                  <div className="text-xs text-gray-600 pl-4">
                    常務で検討する内容は、神体の管理に関心
                    を準備し、道路によかっての協いの幅を考える
                  </div>
                </details>

                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    個人準備にある活用方法の場合。
                  </summary>
                  <div className="text-xs text-gray-600 pl-4">
                    「土砂意発報」や「上路避難指示」が発表した
                    タイミングを会場とし、スポーツ終了後に解除される
                    を推奨
                  </div>
                </details>

                <details className="text-sm">
                  <summary className="cursor-pointer font-medium text-blue-700 mb-2">
                    停電でも開放する目標ざされますが、雷対的エヤコン
                  </summary>
                  <div className="text-xs text-gray-600 pl-4">
                    台風の目線、配電に対づくつのことをする
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}