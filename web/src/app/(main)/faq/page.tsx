'use client'

import { useState, useEffect } from 'react'
import { API } from '@/lib/api'
import type { AIFAQResponse } from '@/types/ai-faq'
import { categoryLabels, hazardLabels } from '@/types/ai-faq'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'

interface FAQItem {
  id: string
  question: string
  answer: string
  category: 'system' | 'disaster' | 'usage' | 'technical'
}

const faqData: FAQItem[] = [
  {
    id: '1',
    question: 'WINDシステムとは何ですか？',
    answer: 'WINDは、「What I Need to Do（私がすべきこと）」の略で、AI技術を活用した災害対応支援システムです。リアルタイムで災害情報を収集・分析し、迅速な災害対応をサポートします。気象庁、NHK、SNSなどの情報源から自動的にデータを取得し、重要な情報を優先表示します。',
    category: 'system'
  },
  {
    id: '2',
    question: 'どのような災害情報が表示されますか？',
    answer: '地震、台風、豪雨、洪水、土砂災害などの自然災害に関する情報を表示します。気象警報・注意報、避難情報、交通機関の運行状況、被害状況なども含まれます。',
    category: 'disaster'
  },
  {
    id: '3',
    question: '情報の更新頻度はどの程度ですか？',
    answer: '情報は基本的にリアルタイムで更新されます。気象庁の警報は発表と同時に、NHKニュースは配信後数分以内に、SNS情報は継続的に監視・分析されています。',
    category: 'system'
  },
  {
    id: '4',
    question: 'アラート通知はどのように機能しますか？',
    answer: 'システムが重要な災害情報を検知すると、自動的にアラートが生成されます。緊急度に応じて色分けされ、ダッシュボードやアラートページで確認できます。プッシュ通知機能も提供しています。',
    category: 'usage'
  },
  {
    id: '5',
    question: '地図上のピンの色の意味は何ですか？',
    answer: '赤色のピンは現在進行中の災害、グレー色のピンは過去の災害を表します。ピンをクリックすると詳細情報が表示され、関連するフィード情報もハイライトされます。',
    category: 'usage'
  },
  {
    id: '6',
    question: 'スマートフォンでも利用できますか？',
    answer: 'はい、レスポンシブデザインにより、スマートフォンやタブレットでも快適に利用できます。主要な機能はすべてモバイル端末でも使用可能です。',
    category: 'technical'
  },
  {
    id: '7',
    question: 'データの信頼性はどの程度ですか？',
    answer: '公的機関（気象庁、自治体など）からの情報を最優先とし、報道機関、SNSの情報は信頼度を分析してから表示しています。不確実な情報には「要確認」マークが付与されます。',
    category: 'system'
  },
  {
    id: '8',
    question: '過去の災害データも確認できますか？',
    answer: 'はい、過去の災害データもアーカイブされており、地図やタイムラインで確認できます。災害の傾向分析や対策検討にも活用できます。',
    category: 'usage'
  },
  {
    id: '9',
    question: 'システムに不具合が発生した場合は？',
    answer: 'システムに問題が発生した場合は、エラーメッセージが表示されます。一時的な問題の場合は時間をおいて再度お試しください。継続的な問題の場合は管理者にお問い合わせください。',
    category: 'technical'
  },
  {
    id: '10',
    question: 'オフラインでも利用できますか？',
    answer: '基本機能の一部はオフラインでも利用可能ですが、リアルタイム情報の取得には インターネット接続が必要です。PWA機能により、一度読み込んだデータは一時的に保存されます。',
    category: 'technical'
  }
]

const categories = {
  system: { label: 'システム概要', color: 'bg-blue-100 text-blue-800' },
  disaster: { label: '災害情報', color: 'bg-red-100 text-red-800' },
  usage: { label: '使用方法', color: 'bg-green-100 text-green-800' },
  technical: { label: '技術的事項', color: 'bg-purple-100 text-purple-800' }
}

export default function FAQPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const [aiFAQs, setAIFAQs] = useState<AIFAQResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadAIFAQs = async () => {
      try {
        setLoading(true)
        setError(null)
        const faqs = await API.getActiveFAQs()
        setAIFAQs(faqs)
      } catch (err) {
        setError('AI FAQ の読み込みに失敗しました')
        console.error('Error loading AI FAQs:', err)
      } finally {
        setLoading(false)
      }
    }

    loadAIFAQs()
  }, [])

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedItems(newExpanded)
  }

  const filteredFAQs = faqData.filter(faq => {
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory
    const matchesSearch = searchQuery === '' ||
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesCategory && matchesSearch
  })

  if (loading) {
    return (
      <div className="bg-zinc-50 text-zinc-900 p-4 sm:p-6 min-h-full">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">よくある質問</h1>
            <p className="text-zinc-600">WINDシステムに関してよくお寄せいただく質問と回答をまとめました。</p>
          </div>
          <LoadingSpinner size="lg" text="FAQを読み込み中..." />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-zinc-50 text-zinc-900 p-4 sm:p-6 min-h-full">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">よくある質問</h1>
          <p className="text-zinc-600">WINDシステムに関してよくお寄せいただく質問と回答をまとめました。</p>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorMessage
              message={error}
              onRetry={() => {
                setError(null)
                window.location.reload()
              }}
            />
          </div>
        )}

        {/* 現在アクティブなAlert関連のAI FAQ */}
        {aiFAQs.length > 0 && (
          <div className="mb-12">
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2 text-red-600">🚨 現在の状況関連行動指針</h2>
              <p className="text-zinc-600">現在発令されている警報に対するAI生成行動指針です。</p>
            </div>

            {aiFAQs.map(alertFAQ => (
              <div key={alertFAQ.alertId} className="mb-8">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm font-medium">
                      {hazardLabels[alertFAQ.hazardType as keyof typeof hazardLabels]}
                    </span>
                    <span className="text-red-600 font-medium">{alertFAQ.area}</span>
                  </div>
                  <h3 className="text-lg font-bold text-red-800">{alertFAQ.alertTitle}</h3>
                </div>

                <div className="space-y-3">
                  {alertFAQ.faqs
                    .sort((a, b) => a.priority - b.priority)
                    .map(faq => (
                      <div key={faq.id} className="bg-white rounded-lg border border-red-200 overflow-hidden">
                        <button
                          onClick={() => toggleExpanded(faq.id)}
                          className="w-full px-6 py-4 text-left hover:bg-red-50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                                  {categoryLabels[faq.category]}
                                </span>
                                <span className="text-xs text-zinc-500">
                                  AI生成 • {new Date(faq.generatedAt).toLocaleString()}
                                </span>
                              </div>
                              <h4 className="text-lg font-medium text-zinc-900">
                                {faq.question}
                              </h4>
                            </div>
                            <div className="flex-shrink-0 mt-1">
                              <svg
                                className={`w-5 h-5 text-zinc-400 transition-transform ${
                                  expandedItems.has(faq.id) ? 'rotate-180' : ''
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

                        {expandedItems.has(faq.id) && (
                          <div className="px-6 pb-4 border-t border-red-100 bg-red-50">
                            <div className="pt-4 text-zinc-700 leading-relaxed">
                              {faq.answer}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* システム一般FAQ */}
        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">システム関連FAQ</h2>
            <p className="text-zinc-600">WINDシステムの一般的な質問と回答です。</p>
          </div>

        {/* 検索とフィルター */}
        <div className="mb-8 space-y-4">
          {/* 検索バー */}
          <div>
            <input
              type="text"
              placeholder="質問を検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
          </div>

          {/* カテゴリフィルター */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === 'all'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
              }`}
            >
              すべて
            </button>
            {Object.entries(categories).map(([key, cat]) => (
              <button
                key={key}
                onClick={() => setSelectedCategory(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === key
                    ? 'bg-zinc-900 text-white'
                    : 'bg-white border border-zinc-300 text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* FAQ一覧 */}
        <div className="space-y-4">
          {filteredFAQs.length > 0 ? (
            filteredFAQs.map(faq => (
              <div key={faq.id} className="bg-white rounded-lg border border-zinc-200 overflow-hidden">
                <button
                  onClick={() => toggleExpanded(faq.id)}
                  className="w-full px-6 py-4 text-left hover:bg-zinc-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${categories[faq.category].color}`}>
                          {categories[faq.category].label}
                        </span>
                      </div>
                      <h3 className="text-lg font-medium text-zinc-900">
                        {faq.question}
                      </h3>
                    </div>
                    <div className="flex-shrink-0 mt-1">
                      <svg
                        className={`w-5 h-5 text-zinc-400 transition-transform ${
                          expandedItems.has(faq.id) ? 'rotate-180' : ''
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

                {expandedItems.has(faq.id) && (
                  <div className="px-6 pb-4 border-t border-zinc-100">
                    <div className="pt-4 text-zinc-700 leading-relaxed">
                      {faq.answer}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="bg-white rounded-lg border p-8 text-center">
              <div className="text-zinc-400 text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-zinc-900 mb-2">
                該当する質問が見つかりません
              </h3>
              <p className="text-zinc-600">
                検索条件を変更するか、カテゴリを「すべて」に設定してお試しください
              </p>
            </div>
          )}
        </div>

        {/* お問い合わせ */}
        <div className="mt-12 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-6 border border-blue-200">
          <h2 className="text-xl font-semibold text-zinc-900 mb-2">
            他にご質問がございますか？
          </h2>
          <p className="text-zinc-700 mb-4">
            上記で解決しない問題や、システムに関するその他のご質問がございましたら、お気軽にお問い合わせください。
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              お問い合わせ
            </button>
            <button className="px-6 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
              システムガイド
            </button>
          </div>
          </div>
        </div>
      </div>
    </div>
  )
}