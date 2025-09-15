'use client'

import { useState, useEffect } from 'react'
import FeedList from '@/components/feeds/FeedList'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import EmptyState from '@/components/ui/EmptyState'
import type { FeedItem } from '@/types/feed'
import type { Alert } from '@/types/alert'
import { API } from '@/lib/api'

export default function FeedsPage() {
  const [feeds, setFeeds] = useState<FeedItem[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [selectedAlert, setSelectedAlert] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')

  const loadFeeds = async () => {
    try {
      setLoading(true)
      setError(null)
      const [feedsData, alertsData] = await Promise.all([
        API.getFeeds(),
        API.getAlerts(true) // アクティブなアラートのみ取得
      ])
      setFeeds(feedsData)
      setAlerts(alertsData)
    } catch (err) {
      setError('フィードおよびアラート情報の読み込みに失敗しました')
      console.error('Error loading feeds and alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFeeds()
  }, [])

  const filteredFeeds = feeds.filter(feed => {
    const matchesSearch = searchQuery === '' ||
      feed.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feed.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feed.labels?.some(label => label.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesFilter = filter === 'all' ||
      (filter === 'alerts' && feed.isAlertCandidate) ||
      (filter === 'media' && ['nhk', 'news'].includes(feed.source)) ||
      (filter === 'official' && ['jma', 'tenki'].includes(feed.source)) ||
      (filter === 'social' && ['x', 'sns'].includes(feed.source))

    const matchesAlert = selectedAlert === '' ||
      (selectedAlert === 'no-alert' && !feed.incidentId) ||
      alerts.some(alert => alert.id === selectedAlert &&
        feeds.some(f => f.incidentId && f.id === feed.id))

    return matchesSearch && matchesFilter && matchesAlert
  })

  // Alert別にフィードをグループ化
  const feedsByAlert = alerts.reduce((acc, alert) => {
    const alertFeeds = feeds.filter(feed =>
      feed.labels?.some(label =>
        label.toLowerCase().includes(alert.hazard.toLowerCase()) ||
        label.toLowerCase().includes(alert.area.toLowerCase())
      ) ||
      feed.area?.toLowerCase().includes(alert.area.toLowerCase()) ||
      feed.hazard?.toLowerCase().includes(alert.hazard.toLowerCase())
    )
    if (alertFeeds.length > 0) {
      acc[alert.id] = { alert, feeds: alertFeeds }
    }
    return acc
  }, {} as Record<string, { alert: Alert, feeds: FeedItem[] }>)

  if (loading) {
    return (
      <div className="bg-zinc-50 text-zinc-900 p-4 sm:p-6 min-h-full">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">フィード</h1>
            <p className="text-zinc-600 mt-1">災害関連情報フィード</p>
          </div>
          <LoadingSpinner size="lg" text="フィードを読み込み中..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-zinc-50 text-zinc-900 p-4 sm:p-6 min-h-full">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">フィード</h1>
            <p className="text-zinc-600 mt-1">災害関連情報フィード</p>
          </div>
          <ErrorMessage
            message={error}
            onRetry={() => {
              setError(null)
              loadFeeds()
            }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-zinc-50 text-zinc-900 p-4 sm:p-6 min-h-full">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">フィード</h1>
          <p className="text-zinc-600 mt-1">災害関連情報フィード</p>
        </div>

        {/* フィルターとサーチ */}
        <div className="mb-6 space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* 検索バー */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="フィードを検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* ソースフィルター */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                すべてのソース
              </button>
              <button
                onClick={() => setFilter('alerts')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'alerts'
                    ? 'bg-amber-600 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                要確認
              </button>
              <button
                onClick={() => setFilter('official')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'official'
                    ? 'bg-green-600 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                公式機関
              </button>
              <button
                onClick={() => setFilter('media')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'media'
                    ? 'bg-red-600 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                報道機関
              </button>
              <button
                onClick={() => setFilter('social')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'social'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                ソーシャルメディア
              </button>
            </div>
          </div>

          {/* アラート別フィルター */}
          {alerts.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-2">
                特定の警報関連フィードを表示:
              </label>
              <select
                value={selectedAlert}
                onChange={(e) => setSelectedAlert(e.target.value)}
                className="px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">すべてのフィード</option>
                <option value="no-alert">警報と無関係なフィード</option>
                {alerts.map(alert => (
                  <option key={alert.id} value={alert.id}>
                    {alert.title} ({alert.area})
                  </option>
                ))}
              </select>
            </div>
          )}
          </div>
        </div>

        {/* 統計 */}
        <div className="mb-6 grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-bold text-blue-600">{feeds.length}</div>
            <div className="text-sm text-zinc-600">総フィード数</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-bold text-amber-600">
              {feeds.filter(f => f.isAlertCandidate).length}
            </div>
            <div className="text-sm text-zinc-600">要確認</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-bold text-green-600">
              {feeds.filter(f => ['jma', 'tenki'].includes(f.source)).length}
            </div>
            <div className="text-sm text-zinc-600">公式機関</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-bold text-red-600">
              {feeds.filter(f => ['nhk', 'news'].includes(f.source)).length}
            </div>
            <div className="text-sm text-zinc-600">報道機関</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-2xl font-bold text-purple-600">
              {feeds.filter(f => ['x', 'sns'].includes(f.source)).length}
            </div>
            <div className="text-sm text-zinc-600">ソーシャルメディア</div>
          </div>
        </div>

        {/* アラート別フィード表示 */}
        {Object.keys(feedsByAlert).length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-4 text-red-600">🚨 現在の警報関連フィード</h2>
            <div className="space-y-6">
              {Object.values(feedsByAlert).map(({ alert, feeds: alertFeeds }) => (
                <div key={alert.id} className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="mb-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm font-medium">
                        {alert.hazard}
                      </span>
                      <span className="text-red-600 font-medium">{alert.area}</span>
                    </div>
                    <h3 className="text-lg font-bold text-red-800">{alert.title}</h3>
                    <p className="text-sm text-red-700">関連フィード: {alertFeeds.length}件</p>
                  </div>
                  <div className="grid gap-2">
                    {alertFeeds.slice(0, 3).map(feed => (
                      <div key={feed.id} className="bg-white rounded p-3 border border-red-200">
                        <div className="text-sm text-zinc-600 mb-1">
                          {feed.source.toUpperCase()} ・ {new Date(feed.publishedAt).toLocaleString()}
                        </div>
                        <a className="font-medium hover:underline text-red-700" href={feed.url} target="_blank" rel="noreferrer">
                          {feed.title}
                        </a>
                      </div>
                    ))}
                    {alertFeeds.length > 3 && (
                      <div className="text-sm text-red-600 text-center">
                        他 {alertFeeds.length - 3} 件のフィード
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* フィードリスト */}
        <div className="grid gap-6">
          {filteredFeeds.length > 0 ? (
            <FeedList items={filteredFeeds} />
          ) : (
            <div className="bg-white rounded-lg border">
              <EmptyState
                icon="📢"
                title="フィードが見つかりません"
                description="検索条件を変更してお試しください"
                action={{
                  label: "フィルターをリセット",
                  onClick: () => {
                    setFilter('all')
                    setSelectedAlert('')
                    setSearchQuery('')
                  }
                }}
              />
            </div>
          )}
        </div>
      </div>
  )
}