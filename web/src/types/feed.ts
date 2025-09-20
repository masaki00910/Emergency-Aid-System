export type FeedSource = 'nhk' | 'jma' | 'tenki' | 'x' | 'news' | 'other'

export type FeedItem = {
  id: string
  incidentId?: string
  source: string
  title: string
  content?: string
  summary?: string
  url?: string
  publishedAt: string | number
  labels?: string[]
  area?: string
  hazard?: string
  category?: string
  severity?: string
  isAlertCandidate?: boolean
  isVerified?: boolean
}
