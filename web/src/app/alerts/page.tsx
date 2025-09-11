'use client'

import { useState } from 'react'
import Link from 'next/link'
import Sidebar from '@/components/layout/Sidebar'
import { mockAlerts, mockIncidents } from '@/mocks/data'

type AlertLevel = 'Active' | 'non-Active' | 'all'
type AlertTag = 'flood' | 'earthquake' | 'landslide' | 'typhoon' | 'tsunami' | 'other' | 'all'

export default function AlertsPage() {
  const [selectedLevel, setSelectedLevel] = useState<AlertLevel>('all')
  const [selectedTag, setSelectedTag] = useState<AlertTag>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })

  // Combine alerts and incidents for display
  const allAlerts = [
    ...mockAlerts.map(alert => ({ ...alert, severity: alert.level === 'warning' ? 'high' : alert.level === 'watch' ? 'medium' : 'low' })),
    ...mockIncidents.map(incident => ({ 
      ...incident, 
      level: incident.severity === 'high' ? 'warning' : incident.severity === 'medium' ? 'watch' : 'info',
      startedAt: incident.reportedAt 
    }))
  ]

  // フィルタリング
  const filteredAlerts = allAlerts.filter(alert => {
    const levelMatch = selectedLevel === 'all' || 
      (selectedLevel === 'Active' && alert.severity === 'high') ||
      (selectedLevel === 'non-Active' && alert.severity !== 'high')
    
    const tagMatch = selectedTag === 'all' || alert.hazard === selectedTag
    
    const searchMatch = searchQuery === '' || 
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alert.area && alert.area.toLowerCase().includes(searchQuery.toLowerCase()))
    
    return levelMatch && tagMatch && searchMatch
  })

  const activeCount = allAlerts.filter(a => a.severity === 'high').length
  const todayCount = allAlerts.filter(a => {
    if (!a.startedAt) return false
    const today = new Date().toDateString()
    return new Date(a.startedAt).toDateString() === today
  }).length

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
    <div className="md:flex">
      <Sidebar />
      <section className="flex-1 p-4 sm:p-6 space-y-6">
        <header>
          <h1 className="text-2xl font-bold mb-6">サマリ</h1>
          
          {/* フィルター */}
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex items-center gap-2">
              <input
                type="date"
                placeholder="Start date"
                className="px-3 py-2 border rounded-lg"
                value={dateRange.start}
                onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              />
              <span>-</span>
              <input
                type="date"
                placeholder="End date"
                className="px-3 py-2 border rounded-lg"
                value={dateRange.end}
                onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              />
            </div>
            
            <select
              className="px-4 py-2 border rounded-lg"
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
              className="px-4 py-2 border rounded-lg flex-1 min-w-[200px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </header>

        {/* サマリーカード */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border p-6 text-center">
            <div className="text-5xl font-bold mb-2">{activeCount}</div>
            <div className="text-lg">Active Alerts</div>
          </div>
          <div className="bg-white rounded-xl border p-6 text-center">
            <div className="text-5xl font-bold mb-2">{todayCount}</div>
            <div className="text-lg">Events Today</div>
          </div>
        </div>

        {/* アラートフィルター */}
        <div className="bg-gray-100 rounded-lg p-1 mb-6">
          <div className="flex gap-1">
            <button
              className={`flex-1 px-4 py-2 rounded-md transition-all ${
                selectedLevel === 'all' ? 'bg-white shadow' : ''
              }`}
              onClick={() => setSelectedLevel('all')}
            >
              ✓ すべて
            </button>
            <button
              className={`flex-1 px-4 py-2 rounded-md transition-all ${
                selectedLevel === 'Active' ? 'bg-white shadow' : ''
              }`}
              onClick={() => setSelectedLevel('Active')}
            >
              □ Activeのみ
            </button>
            <button
              className={`flex-1 px-4 py-2 rounded-md transition-all ${
                selectedLevel === 'non-Active' ? 'bg-white shadow' : ''
              }`}
              onClick={() => setSelectedLevel('non-Active')}
            >
              □ non-Activeのみ
            </button>
          </div>
        </div>

        {/* 地域・エリア */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">地域・エリア</label>
          <select className="w-full px-4 py-2 border rounded-lg bg-white">
            <option>全国</option>
            <option>北海道</option>
            <option>東北</option>
            <option>関東</option>
            <option>中部</option>
            <option>近畿</option>
            <option>中国</option>
            <option>四国</option>
            <option>九州</option>
          </select>
        </div>

        {/* アラート一覧 */}
        <div className="space-y-4">
          {filteredAlerts.map((alert, index) => (
            <Link key={alert.id} href={`/alerts/${alert.id}`}>
              <div
                className={`rounded-xl border-2 p-4 cursor-pointer hover:shadow-lg transition-shadow ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl">{getHazardIcon(alert.hazard)}</div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        alert.severity === 'high' ? 'bg-red-500 text-white' : 'bg-gray-400 text-white'
                      }`}>
                        {alert.severity === 'high' ? 'Active' : 'non-Active'}
                      </span>
                      <div className="flex gap-1">
                        {alert.hazard && (
                          <span className={`px-2 py-1 rounded text-xs ${getTagColor(alert.hazard)}`}>
                            {getHazardDisplayName(alert.hazard)}
                          </span>
                        )}
                        {['特別警報', '警報', '注意報'].map((tag, i) => {
                          if (Math.random() > 0.6) {
                            return (
                              <span key={i} className="px-2 py-1 rounded text-xs bg-orange-100 text-orange-800">
                                {tag}
                              </span>
                            )
                          }
                          return null
                        })}
                      </div>
                    </div>
                    
                    <div className="font-semibold text-lg mb-1">{alert.title}</div>
                    
                    <div className="text-sm text-gray-600 mb-2">
                      <div>{alert.area}県・{alert.area}地域・{alert.area}市</div>
                      <div>詳細を見る →</div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-500">
                        ソース：{['気象庁', 'NHK', '消防庁'][index % 3]} | 
                        アラート発生：{alert.startedAt ? new Date(alert.startedAt).toLocaleString('ja-JP') : '-'} | 
                        最終更新：{alert.startedAt ? new Date(alert.startedAt).toLocaleString('ja-JP') : '-'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* FAQ */}
        <div className="bg-white rounded-xl border p-6 mt-8">
          <h2 className="text-xl font-bold mb-4">FAQ</h2>
          <div className="space-y-3">
            <details className="border-b pb-3">
              <summary className="cursor-pointer font-medium">なぜ災害への準備が必要？</summary>
              <p className="mt-2 text-sm text-gray-600">
                急な自然災害は避難を遅らせ、人命や財産に深刻な被害をもたらす可能性があります。
              </p>
            </details>
            <details className="border-b pb-3">
              <summary className="cursor-pointer font-medium">大雨時の備えの注意点は？</summary>
              <p className="mt-2 text-sm text-gray-600">
                最新の気象情報を確認し、避難場所への経路を確認しておくことが重要です。
              </p>
            </details>
            <details className="border-b pb-3">
              <summary className="cursor-pointer font-medium">土砂災害への備え方は？</summary>
              <p className="mt-2 text-sm text-gray-600">
                斜面や崖の近くに住んでいる場合は、早めの避難を心がけ、避難場所を事前に確認しておきましょう。
              </p>
            </details>
          </div>
        </div>
      </section>
    </div>
  )
}