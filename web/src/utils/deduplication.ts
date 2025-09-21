import type { FeedItem } from '@/types/feed'
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'

/**
 * 類似度キー生成（タイトル正規化）
 * 日本語記号削除、空白削除、小文字化で重複判定用キーを生成
 */
export function generateSimilarityKey(title: string): string {
  return title
    .replace(/[「」。、！？・]/g, '') // 日本語記号削除
    .replace(/\s+/g, '') // 空白削除
    .replace(/[.,!?-]/g, '') // 英語記号削除
    .toLowerCase()
    .substring(0, 30) // 最初の30文字で判定
}

/**
 * フィードの重複削除
 * タイトルの類似度で判定し、最新のものを残す
 */
export function deduplicateFeeds(feeds: FeedItem[]): FeedItem[] {
  const seen = new Map<string, FeedItem>()
  
  // publishedAtで降順ソート（最新が先）
  const sortedFeeds = [...feeds].sort((a, b) => {
    const aTime = typeof a.publishedAt === 'number' ? a.publishedAt : new Date(a.publishedAt).getTime()
    const bTime = typeof b.publishedAt === 'number' ? b.publishedAt : new Date(b.publishedAt).getTime()
    return bTime - aTime
  })
  
  for (const feed of sortedFeeds) {
    const key = generateSimilarityKey(feed.title)
    const existing = seen.get(key)
    
    // 重複がない、または既存より新しい場合は更新
    if (!existing || feed.publishedAt > existing.publishedAt) {
      seen.set(key, feed)
    }
  }
  
  // 最新順で返す
  return Array.from(seen.values())
    .sort((a, b) => {
      const aTime = typeof a.publishedAt === 'number' ? a.publishedAt : new Date(a.publishedAt).getTime()
      const bTime = typeof b.publishedAt === 'number' ? b.publishedAt : new Date(b.publishedAt).getTime()
      return bTime - aTime
    })
}

/**
 * インシデントの重複削除
 * タイトルの類似度で判定し、最新のものを残す
 */
export function deduplicateIncidents(incidents: Incident[]): Incident[] {
  const seen = new Map<string, Incident>()
  
  // reported_atで降順ソート（最新が先）
  const sortedIncidents = [...incidents].sort((a, b) => {
    const aTime = new Date(a.reported_at).getTime()
    const bTime = new Date(b.reported_at).getTime()
    return bTime - aTime
  })
  
  for (const incident of sortedIncidents) {
    const key = generateSimilarityKey(incident.title)
    const existing = seen.get(key)
    
    // 重複がない、または既存より新しい場合は更新
    if (!existing || new Date(incident.reported_at).getTime() > new Date(existing.reported_at).getTime()) {
      seen.set(key, incident)
    }
  }
  
  // 最新順で返す
  return Array.from(seen.values())
    .sort((a, b) => {
      const aTime = new Date(a.reported_at).getTime()
      const bTime = new Date(b.reported_at).getTime()
      return bTime - aTime
    })
}

/**
 * アラートの重複削除
 * タイトルの類似度で判定し、最新のものを残す
 */
export function deduplicateAlerts(alerts: Alert[]): Alert[] {
  const seen = new Map<string, Alert>()
  
  // startedAtで降順ソート（最新が先）
  const sortedAlerts = [...alerts].sort((a, b) => b.startedAt - a.startedAt)
  
  for (const alert of sortedAlerts) {
    const key = generateSimilarityKey(alert.title)
    const existing = seen.get(key)
    
    // 重複がない、または既存より新しい場合は更新
    if (!existing || alert.startedAt > existing.startedAt) {
      seen.set(key, alert)
    }
  }
  
  // 最新順で返す
  return Array.from(seen.values())
    .sort((a, b) => b.startedAt - a.startedAt)
}