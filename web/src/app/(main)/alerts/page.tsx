'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { API } from '@/lib/api'
import type { Alert } from '@/types/alert'
import type { Incident } from '@/types/incident'
import type { FeedItem } from '@/types/feed'

type AlertLevel = 'Active' | 'non-Active' | 'all'
type AlertTag = 'flood' | 'earthquake' | 'landslide' | 'typhoon' | 'tsunami' | 'other' | 'all'

export default function AlertsPage() {
  const [selectedLevel, setSelectedLevel] = useState<AlertLevel>('all')
  const [selectedTag, setSelectedTag] = useState<AlertTag>('all')
  const [selectedRegion, setSelectedRegion] = useState<string>('全国')
  const [searchQuery, setSearchQuery] = useState('')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [feeds, setFeeds] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [alertsData, incidentsData, feedsData] = await Promise.all([
          API.getAlerts(true), // active alerts only - same as dashboard
          API.getIncidents(),
          API.getFeeds(50)
        ])
        
        // Filter for 24 hours only - same as dashboard
        const now = Date.now()
        const twentyFourHoursAgo = now - (24 * 60 * 60 * 1000)

        // Filter alerts for last 24 hours AND active status - same as dashboard
        const recentActiveAlerts = alertsData.filter(alert => {
          const alertTime = alert.startedAt
          return alertTime >= twentyFourHoursAgo
        })
        
        // Filter feeds for last 24 hours - same as dashboard
        const recentFeeds = feedsData.filter(feed => {
          const feedTime = typeof feed.publishedAt === 'string' 
            ? new Date(feed.publishedAt).getTime() 
            : feed.publishedAt
          return feedTime >= twentyFourHoursAgo
        })

        setAlerts(recentActiveAlerts)
        setIncidents(incidentsData)
        // Store feeds for Events Today count
        setFeeds(recentFeeds)
      } catch (error) {
        console.error('Failed to fetch alerts data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Region mapping for Japanese prefectures
  const getRegionFromArea = (area: string): string => {
    const regionMap: Record<string, string[]> = {
      '北海道': ['北海道'],
      '東北': ['青森', '岩手', '宮城', '秋田', '山形', '福島'],
      '関東': ['茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川'],
      '中部': ['新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜', '静岡', '愛知'],
      '近畿': ['三重', '滋賀', '京都', '大阪', '兵庫', '奈良', '和歌山'],
      '中国': ['鳥取', '島根', '岡山', '広島', '山口'],
      '四国': ['徳島', '香川', '愛媛', '高知'],
      '九州': ['福岡', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '沖縄']
    }

    for (const [region, prefectures] of Object.entries(regionMap)) {
      if (prefectures.some(pref => area.includes(pref))) {
        return region
      }
    }
    return '全国'
  }

  // Use incidents as the primary source since alerts are derived from incidents
  const allAlerts = incidents.map(incident => {
    // Use same hazard mapping as cards for consistent active determination
    const hazardMapping = {
      'earthquake': {name: '地震', icon: '🌍'},
      'tsunami': {name: '津波', icon: '🌊'}, 
      'flood': {name: '洪水', icon: '💧'},
      'typhoon': {name: '台風', icon: '🌀'},
      'landslide': {name: '土砂災害', icon: '⛰️'},
      'volcano': {name: '火山', icon: '🌋'},
      'wildfire': {name: '山火事', icon: '🔥'},
      'other': {name: 'その他', icon: '⚠️'}
    }
    const hazardInfo = hazardMapping[incident.type] || hazardMapping['other']
    
    // Use EXACT same active condition as card display
    const isActive = incident.status === 'active' || incident.is_active === true
    const active = isActive && incident.severity !== 'low' && hazardInfo.name !== 'その他' && hazardInfo.name !== ''
    
    return {
      id: incident.id,
      title: incident.title,
      area: incident.location?.admin || '不明',
      hazard: incident.type,
      severity: incident.severity,
      startedAt: incident.reported_at ? new Date(incident.reported_at).getTime() : Date.now(),
      description: incident.description,
      region: getRegionFromArea(incident.location?.admin || ''),
      active: active
    }
  })

  // フィルタリング
  const filteredAlerts = allAlerts.filter(alert => {
    const levelMatch = selectedLevel === 'all' ||
      (selectedLevel === 'Active' && alert.active === true) ||
      (selectedLevel === 'non-Active' && alert.active === false)

    const tagMatch = selectedTag === 'all' || alert.hazard === selectedTag

    const regionMatch = selectedRegion === '全国' || alert.region === selectedRegion

    const searchMatch = searchQuery === '' ||
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alert.area && alert.area.toLowerCase().includes(searchQuery.toLowerCase()))

    return levelMatch && tagMatch && regionMatch && searchMatch
  })

  // Use same count logic as dashboard
  const activeCount = alerts.length // alerts are already filtered for 24h and active status
  const todayCount = feeds.length // feeds are already filtered for 24h

  const getSeverityColor = (severity?: string) => {
    switch(severity) {
      case 'high': return 'border-red-500 bg-red-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      default: return 'border-gray-300 bg-gray-50'
    }
  }

  const getHazardIcon = (hazard?: string) => {
    switch(hazard) {
      case '大雨': return '🌧️'
      case '地震': return '🔴'
      case '台風': return '🌀'
      case '土砂災害': return '⛰️'
      case '津波': return '🌊'
      default: return '⚠️'
    }
  }

  const getTagColor = (tag: string) => {
    switch(tag) {
      case 'flood': return 'bg-blue-100 text-blue-800'
      case 'earthquake': return 'bg-red-100 text-red-800'
      case 'typhoon': return 'bg-purple-100 text-purple-800'
      case 'landslide': return 'bg-yellow-100 text-yellow-800'
      case 'tsunami': return 'bg-cyan-100 text-cyan-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  const getHazardDisplayName = (hazard: string) => {
    switch(hazard) {
      case 'flood': return '大雨'
      case 'earthquake': return '地震'
      case 'typhoon': return '台風'
      case 'landslide': return '土砂災害'
      case 'tsunami': return '津波'
      default: return 'その他'
    }
  }

  return (
    <div className="p-4 sm:p-6 space-y-8 min-h-screen">
        <header className="animate-fade-in">
          <h1 className="text-4xl font-bold gradient-text animate-float mb-6">アラートサマリ</h1>
          
          {/* フィルター */}
          <div className="flex flex-wrap gap-4 mb-8 animate-slide-up animate-stagger-1">
            <div className="flex items-center gap-3">
              <input
                type="date"
                placeholder="Start date"
                className="px-4 py-3 glass-effect rounded-xl border-0 shadow-md focus:ring-2 focus:ring-purple-500"
                value={dateRange.start}
                onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              />
              <span className="text-slate-600 font-medium">-</span>
              <input
                type="date"
                placeholder="End date"
                className="px-4 py-3 glass-effect rounded-xl border-0 shadow-md focus:ring-2 focus:ring-purple-500"
                value={dateRange.end}
                onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              />
            </div>

            <select
              className="px-6 py-3 glass-effect rounded-xl border-0 shadow-md focus:ring-2 focus:ring-purple-500 font-medium"
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value as AlertTag)}
            >
              <option value="all">Tag</option>
              <option value="flood">大雨</option>
              <option value="earthquake">地震</option>
              <option value="landslide">土砂災害</option>
              <option value="typhoon">台風</option>
              <option value="tsunami">津波</option>
              <option value="other">その他</option>
            </select>

            <input
              type="text"
              placeholder="Search..."
              className="px-6 py-3 glass-effect rounded-xl border-0 shadow-md focus:ring-2 focus:ring-purple-500 flex-1 min-w-[200px] text-lg"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </header>

        {/* サマリーカード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 animate-slide-up animate-stagger-2">
          <div className="rounded-3xl glass-effect p-8 text-center shadow-2xl card-hover border-0">
            <div className="w-16 h-16 bg-gradient-to-br from-red-400 to-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl">
              <span className="text-2xl">🚨</span>
            </div>
            <div className="text-5xl font-black bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent mb-2">
              {loading ? '...' : activeCount}
            </div>
            <div className="text-xl font-bold gradient-text">Active Alerts</div>
          </div>
          <div className="rounded-3xl glass-effect p-8 text-center shadow-2xl card-hover border-0">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl">
              <span className="text-2xl">📊</span>
            </div>
            <div className="text-5xl font-black bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent mb-2">
              {loading ? '...' : todayCount}
            </div>
            <div className="text-xl font-bold gradient-text">Events Today</div>
          </div>
        </div>

        {/* アラートフィルター */}
        <div className="glass-effect rounded-2xl p-2 mb-8 shadow-lg animate-slide-up animate-stagger-3">
          <div className="flex gap-2">
            <button
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                selectedLevel === 'all' ? 'btn-gradient text-white shadow-lg' : 'text-slate-600 hover:bg-slate-100/50'
              }`}
              onClick={() => setSelectedLevel('all')}
            >
              🔍 すべて
            </button>
            <button
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                selectedLevel === 'Active' ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg' : 'text-slate-600 hover:bg-slate-100/50'
              }`}
              onClick={() => setSelectedLevel('Active')}
            >
              🚨 Activeのみ
            </button>
            <button
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all duration-300 ${
                selectedLevel === 'non-Active' ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg' : 'text-slate-600 hover:bg-slate-100/50'
              }`}
              onClick={() => setSelectedLevel('non-Active')}
            >
              🔵 non-Activeのみ
            </button>
          </div>
        </div>

        {/* 地域・エリア */}
        <div className="mb-8 animate-slide-up animate-stagger-4">
          <label className="block text-lg font-bold gradient-text mb-3">🗾 地域・エリア</label>
          <select
            className="w-full px-6 py-4 glass-effect rounded-2xl border-0 shadow-lg focus:ring-2 focus:ring-purple-500 text-lg font-medium"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
          >
            <option value="全国">全国</option>
            <option value="北海道">北海道</option>
            <option value="東北">東北</option>
            <option value="関東">関東</option>
            <option value="中部">中部</option>
            <option value="近畿">近畿</option>
            <option value="中国">中国</option>
            <option value="四国">四国</option>
            <option value="九州">九州</option>
          </select>
        </div>

        {/* アラート一覧 */}
        <div className="space-y-6">
          {loading ? (
            <div className="text-center py-16 text-slate-600">
              <div className="inline-flex items-center gap-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-600"></div>
                <span className="text-lg">読み込み中...</span>
              </div>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <div className="text-6xl mb-4">🌅</div>
              <div className="text-xl font-medium mb-2">該当するアラートはありません</div>
              <div className="text-sm">条件を変更して再度お試しください</div>
            </div>
          ) : (
            filteredAlerts.map((alert, index) => (
            <Link key={alert.id} href={`/alerts/${alert.id}`}>
              <div
                className={`rounded-3xl glass-effect p-6 shadow-xl card-hover border-0 cursor-pointer animate-slide-up ${
                  index === 0 ? 'animate-stagger-1' : index === 1 ? 'animate-stagger-2' : index === 2 ? 'animate-stagger-3' : 'animate-stagger-4'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Get hazard info for consistent styling - same as dashboard */}
                  {(() => {
                    const hazardMapping = {
                      'earthquake': {name: '地震', icon: '🌍'},
                      'tsunami': {name: '津波', icon: '🌊'}, 
                      'flood': {name: '洪水', icon: '💧'},
                      'typhoon': {name: '台風', icon: '🌀'},
                      'landslide': {name: '土砂災害', icon: '⛰️'},
                      'volcano': {name: '火山', icon: '🌋'},
                      'wildfire': {name: '山火事', icon: '🔥'},
                      'other': {name: 'その他', icon: '⚠️'}
                    }
                    const hazardInfo = hazardMapping[alert.hazard] || hazardMapping['other']
                    
                    return (
                      <div className="flex-1">
                        <div className="flex items-center gap-2 text-sm text-slate-600 mb-3">
                          <span className="text-lg">{hazardInfo.icon}</span>
                          <span className="font-medium">{alert.area}</span>
                        </div>
                        
                        <div className="font-semibold text-slate-900 text-base leading-snug mb-3">
                          {alert.title}
                        </div>
                        
                        <div className="flex flex-wrap gap-2 mb-3">
                          <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-slate-100 to-slate-200 px-3 py-1 text-xs font-medium text-slate-700 shadow-sm">
                            🏷️ {hazardInfo.name}
                          </span>
                          <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium shadow-sm ${
                            alert.severity === 'high' 
                              ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800' 
                              : alert.severity === 'medium'
                              ? 'bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800'
                              : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
                          }`}>
                            📊 深刻度：{alert.severity === 'high' ? '高' : alert.severity === 'medium' ? '中' : '低'}
                          </span>
                          {alert.active && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-red-500 to-red-600 px-3 py-1 text-xs font-medium text-white shadow-md">
                              🚨 アクティブ
                            </span>
                          )}
                        </div>
                        
                        <div className="text-xs text-slate-500 flex items-center gap-1">
                          🕒 {(() => {
                            const timestamp = alert.startedAt
                            const diff = Math.max(1, Math.round((Date.now() - timestamp) / 60000))
                            if (diff < 60) return `${diff}分前`
                            const h = Math.round(diff / 60)
                            return `${h}時間前`
                          })()}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            </Link>
            ))
          )}
        </div>

        {/* FAQ */}
        <div className="rounded-3xl glass-effect shadow-2xl p-8 mt-12 border-0 animate-slide-up animate-stagger-4">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-xl">❓</span>
            </div>
            <h2 className="text-2xl font-bold gradient-text">よくある質問</h2>
          </div>
          <div className="space-y-4">
            <details className="glass-effect rounded-xl p-4 cursor-pointer group">
              <summary className="font-semibold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">なぜ災害への準備が必要？</summary>
              <p className="mt-3 text-slate-600 leading-relaxed pl-4 border-l-4 border-blue-200">
                急な自然災害は避難を遅らせ、人命や財産に深刻な被害をもたらす可能性があります。事前の準備により、被害を最小限に抑えることができます。
              </p>
            </details>
            <details className="glass-effect rounded-xl p-4 cursor-pointer group">
              <summary className="font-semibold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">大雨時の備えの注意点は？</summary>
              <p className="mt-3 text-slate-600 leading-relaxed pl-4 border-l-4 border-blue-200">
                最新の気象情報を確認し、避難場所への経路を確認しておくことが重要です。また、非常用持ち出し袋の準備も欠かせません。
              </p>
            </details>
            <details className="glass-effect rounded-xl p-4 cursor-pointer group">
              <summary className="font-semibold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">土砂災害への備え方は？</summary>
              <p className="mt-3 text-slate-600 leading-relaxed pl-4 border-l-4 border-blue-200">
                斜面や崖の近くに住んでいる場合は、早めの避難を心がけ、避難場所を事前に確認しておきましょう。雨量や地盤の状況に常に注意を払うことが大切です。
              </p>
            </details>
          </div>
        </div>
    </div>
  )
}