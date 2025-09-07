import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'
import type { FeedItem } from '@/types/feed'

export const mockIncidents: Incident[] = [
  { id: 'i1', title: '強い地震（震度5弱）', lat: 35.68, lng: 139.76, severity: 'high', reportedAt: Date.now() - 15 * 60_000 },
  { id: 'i2', title: '大雨による冠水',     lat: 35.61, lng: 139.70, severity: 'medium', reportedAt: Date.now() - 50 * 60_000 },
  { id: 'i3', title: '土砂災害の恐れ',     lat: 35.73, lng: 139.80, severity: 'medium', reportedAt: Date.now() - 120 * 60_000 },
]

export const mockAlerts: Alert[] = [
  { id: 'a1', title: '地震注意報（関東）', level: 'warning', hazard: 'earthquake', area: '関東', startedAt: Date.now() - 15 * 60_000 },
  { id: 'a2', title: '大雨警報（東京23区）', level: 'watch',   hazard: 'flood',      area: '東京23区', startedAt: Date.now() - 45 * 60_000 },
]

export const mockFeeds: FeedItem[] = [
  {
    id: 'f1',
    source: 'jma',
    title: '【地震情報】関東南部で震度5弱',
    summary: '交通機関に影響の可能性。余震に注意してください。',
    url: 'https://www.jma.go.jp/',
    publishedAt: Date.now() - 10 * 60_000,
    labels: ['警報', '地震'],
    area: '関東',
    hazard: 'earthquake',
    isAlertCandidate: true,
  },
  {
    id: 'f2',
    source: 'nhk',
    title: '大雨の影響で一部路線で遅延',
    url: 'https://www.nhk.or.jp/',
    publishedAt: Date.now() - 60 * 60_000,
    labels: ['注意報', '大雨'],
    area: '東京',
    hazard: 'flood',
    isAlertCandidate: true,
  },
  {
    id: 'f3',
    source: 'tenki',
    title: '土砂災害警戒情報',
    url: 'https://tenki.jp/',
    publishedAt: Date.now() - 3 * 60 * 60_000,
    labels: ['警戒', '土砂'],
    area: '多摩',
    hazard: 'landslide',
  },
]
