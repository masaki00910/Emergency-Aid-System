'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { useParams } from 'next/navigation'
import { API } from '@/lib/api'
import IncidentMap from '@/components/map/IncidentMap'
import type { Alert } from '@/types/alert'
import type { Incident } from '@/types/incident'
import type { FeedItem } from '@/types/feed'
import type { AIFAQResponse } from '@/types/ai-faq'
import { categoryLabels } from '@/types/ai-faq'

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
  const [alertFAQ, setAlertFAQ] = useState<AIFAQResponse | null>(null)
  const [expandedFAQs, setExpandedFAQs] = useState<Set<string>>(new Set())
  const [chatQuestion, setChatQuestion] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [chatHistory, setChatHistory] = useState<Array<{question: string, answer: string, timestamp: number}>>([])
  const chatHistoryRef = useRef<HTMLDivElement>(null)

  // Separate FAQ state changes from map-related state to prevent cross-component updates
  const handleQuestionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Use separate function to avoid triggering other effects
    setChatQuestion(e.target.value)
  }

  // FAQ回答のフォーマット関数
  const formatFAQAnswer = (answer: string): string => {
    console.log('Original answer:', JSON.stringify(answer))
    
    let formatted = answer
      // 改行文字を統一
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      // 文の終わりの後に箇条書きがある場合、改行を追加
      .replace(/([。！？])\s*([・\-\*])/g, '$1\n\n$2')
      // 半角スペース + 箇条書き記号を改行に変換
      .replace(/\s+([・\-\*])/g, '\n$1')
      // 番号付きリストの前に改行を追加
      .replace(/([。！？])\s*(\d+\.)/g, '$1\n\n$2')
      // 連続する半角スペースを改行に変換（箇条書きが続く場合）
      .replace(/([・\-\*][^・\-\*\n]*)\s+([・\-\*])/g, '$1\n$2')
      // 連続する改行を統一（3つ以上は2つに）
      .replace(/\n{3,}/g, '\n\n')
      // 文頭と文末の不要な改行を削除
      .trim()

    console.log('Formatted answer:', JSON.stringify(formatted))
    return formatted
  }

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

          // Fetch contextual FAQs for this specific alert/incident
          try {
            const faq = await API.getFAQsByIncident(alertId)
            setAlertFAQ(faq)
          } catch (error) {
            console.warn('Failed to fetch FAQs for incident:', error)
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

  // Auto-scroll to bottom when chat history updates
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight
    }
  }, [chatHistory])

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

  const toggleFAQExpanded = (id: string) => {
    const newExpanded = new Set(expandedFAQs)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedFAQs(newExpanded)
  }

  const handleAskQuestion = async () => {
    if (!chatQuestion.trim() || !alertId || isAsking) return
    
    const currentQuestion = chatQuestion.trim()
    setIsAsking(true)
    setChatQuestion('') // Clear input field immediately
    
    try {
      const answer = await API.askFAQQuestion(alertId, currentQuestion)
      
      // Add to chat history
      setChatHistory(prev => [...prev, {
        question: currentQuestion,
        answer: answer,
        timestamp: Date.now()
      }])
    } catch (error) {
      console.error('Failed to get answer:', error)
      const errorAnswer = '申し訳ございませんが、回答の取得に失敗しました。しばらく時間をおいて再度お試しください。'
      
      // Add error response to chat history
      setChatHistory(prev => [...prev, {
        question: currentQuestion,
        answer: errorAnswer,
        timestamp: Date.now()
      }])
    } finally {
      setIsAsking(false)
    }
  }

  const handleQuestionKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAskQuestion()
    }
  }

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

  // Create incident for map display - simplified to avoid useMemo dependency issues
  const mapIncidents = incident ? [{
    ...incident,
    // Ensure location exists and has proper structure with valid lat/lng numbers
    location: (incident.location && 
               typeof incident.location.lat === 'number' && 
               typeof incident.location.lng === 'number') 
      ? incident.location 
      : {
          lat: 35.6762,
          lng: 139.6503,
          admin: alert?.area || '不明'
        },
    // Ensure all required properties exist
    severity: incident.severity || 'medium',
    is_active: incident.is_active ?? true,
    type: incident.type || 'other'
  }] : []

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
                {mapIncidents.length > 0 ? (
                  <IncidentMap
                    incidents={mapIncidents}
                    center={incident?.location ? { lat: incident.location.lat, lng: incident.location.lng } : undefined}
                    zoom={10}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <div className="text-2xl mb-2">📍</div>
                      <div>位置情報が利用できません</div>
                    </div>
                  </div>
                )}
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
                {(() => {
                  // Use same hazard mapping as other screens
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
                  const severity = incident?.severity || alert.level
                  const isActive = alert.level === 'warning' || alert.level === 'emergency'
                  
                  return (
                    <>
                      <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-slate-100 to-slate-200 px-3 py-1 text-xs font-medium text-slate-700 shadow-sm">
                        🏷️ {hazardInfo.name}
                      </span>
                      <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium shadow-sm ${
                        severity === 'high' || alert.level === 'emergency'
                          ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800' 
                          : severity === 'medium' || alert.level === 'warning'
                          ? 'bg-gradient-to-r from-amber-100 to-amber-200 text-amber-800'
                          : 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
                      }`}>
                        📊 深刻度：{severity === 'high' || alert.level === 'emergency' ? '高' : severity === 'medium' || alert.level === 'warning' ? '中' : '低'}
                      </span>
                      {isActive && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-red-500 to-red-600 px-3 py-1 text-xs font-medium text-white shadow-md">
                          🚨 アクティブ
                        </span>
                      )}
                    </>
                  )
                })()}
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

            {/* AI Generated FAQ */}
            {alertFAQ && (
              <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
                <h3 className="text-lg font-semibold mb-4 text-blue-800">What I need to do - 私がすべきこと -</h3>
                <p className="text-xs text-blue-600 mb-4">以下から私が今すべきことを確認できます</p>
                
                <div className="space-y-3">
                  {alertFAQ.faqs
                    .sort((a, b) => a.priority - b.priority)
                    .map(faq => (
                      <div key={faq.id} className="bg-white rounded-lg border border-blue-200 overflow-hidden">
                        <button
                          onClick={() => toggleFAQExpanded(faq.id)}
                          className="w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                                  {categoryLabels[faq.category]}
                                </span>
                              </div>
                              <h4 className="text-sm font-medium text-gray-900">
                                {faq.question}
                              </h4>
                            </div>
                            <div className="flex-shrink-0 mt-1">
                              <svg
                                className={`w-4 h-4 text-gray-400 transition-transform ${
                                  expandedFAQs.has(faq.id) ? 'rotate-180' : ''
                                }`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M19 9l-7 7-7-7"
                                />
                              </svg>
                            </div>
                          </div>
                        </button>

                        {expandedFAQs.has(faq.id) && (
                          <div className="px-4 pb-3 border-t border-blue-100 bg-blue-50">
                            <div className="pt-3 text-xs text-gray-700 leading-relaxed">
                              {faq.answer}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
                
                {/* Chat Interface */}
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <h4 className="text-sm font-medium text-blue-800 mb-3">この災害について質問する</h4>
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatQuestion}
                        onChange={handleQuestionChange}
                        onKeyPress={handleQuestionKeyPress}
                        placeholder="例: 避難のタイミングは？"
                        className="flex-1 px-3 py-2 text-sm border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isAsking}
                      />
                      <button
                        onClick={handleAskQuestion}
                        disabled={!chatQuestion.trim() || isAsking}
                        className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        {isAsking ? '...' : '質問'}
                      </button>
                    </div>
                    
                    {/* Chat History */}
                    {chatHistory.length > 0 && (
                      <div ref={chatHistoryRef} className="max-h-96 overflow-y-auto space-y-3 scroll-smooth">
                        {chatHistory.map((chat, index) => (
                          <div key={index} className="space-y-2">
                            {/* User Question */}
                            <div className="flex justify-end">
                              <div className="bg-blue-600 text-white rounded-lg px-3 py-2 max-w-md">
                                <div className="text-sm whitespace-pre-line">{chat.question}</div>
                              </div>
                            </div>
                            
                            {/* AI Answer */}
                            <div className="flex justify-start">
                              <div className="bg-white border border-blue-200 rounded-lg p-3 max-w-md">
                                <div className="flex items-start gap-2">
                                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <span className="text-blue-600 text-xs">AI</span>
                                  </div>
                                  <div className="flex-1 text-sm text-gray-700 leading-relaxed">
                                    <div dangerouslySetInnerHTML={{ 
                                      __html: formatFAQAnswer(chat.answer)
                                        .split('\n')
                                        .map(line => line.trim())
                                        .filter(line => line.length > 0)
                                        .join('<br/>')
                                    }} />
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Loading indicator while asking */}
                    {isAsking && (
                      <div className="flex justify-start">
                        <div className="bg-white border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-blue-600 text-xs">AI</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
    </div>
  )
}