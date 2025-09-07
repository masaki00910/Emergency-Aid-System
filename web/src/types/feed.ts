export type FeedSource = 'nhk' | 'jma' | 'tenki' | 'x' | 'news' | 'other'

export type FeedItem = {
  id: string
  source: FeedSource
  title: string
  summary?: string
  url: string
  publishedAt: number     
  labels?: string[]      
  area?: string
  hazard?: string
  isAlertCandidate?: boolean 
}
