// API統合サービス - Firebase/REST API統合
import { initializeApp } from 'firebase/app'
import { getFirestore, collection, getDocs, doc, getDoc, query, where, orderBy, limit } from 'firebase/firestore'
import type { Incident as IncidentType, Location } from '@/types/incident'
import type { Alert as AlertType } from '@/types/alert'
import type { FeedItem as FeedType } from '@/types/feed'

// Dashboard용 간소화된 타입 (기존 코드 호환성)
export interface Incident {
  id: string
  title: string
  area?: string
  lat: number
  lng: number
  hazard?: string
  severity?: string
  reportedAt: string
  description?: string
}

export interface Alert {
  id: string
  title: string
  area: string
  hazard: string
  severity: string
  startedAt: string
  description?: string
  active: boolean
}

export interface FeedItem {
  id: string
  type: string
  title: string
  content?: string
  timestamp: string
  source: string
  incidentId?: string
}

// 타입 변환 함수들
function convertIncident(incident: IncidentType): Incident {
  return {
    id: incident.id,
    title: incident.title,
    area: incident.location?.admin,
    lat: incident.location?.lat || 0,
    lng: incident.location?.lng || 0,
    hazard: incident.type,
    severity: incident.severity,
    reportedAt: incident.reported_at,
    description: incident.description
  }
}

function convertAlert(alert: AlertType): Alert {
  return {
    id: alert.id,
    title: alert.title,
    area: alert.area,
    hazard: alert.hazard,
    severity: alert.level,
    startedAt: typeof alert.startedAt === 'number' ? new Date(alert.startedAt).toISOString() : alert.startedAt.toString(),
    description: alert.description,
    active: true // API에서 활성 알림만 반환한다고 가정
  }
}

function convertFeed(feed: FeedType): FeedItem {
  return {
    id: feed.id,
    type: feed.category || 'info',
    title: feed.title,
    content: feed.content || feed.summary,
    timestamp: typeof feed.publishedAt === 'number' ? new Date(feed.publishedAt).toISOString() : feed.publishedAt,
    source: feed.source,
    incidentId: feed.incidentId
  }
}

// Firebase設定
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

// Firebase/REST API選択フラグ
const USE_FIREBASE = process.env.NEXT_PUBLIC_USE_FIREBASE === 'true'
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8082'

// Firebase初期化
let db: any = null
if (USE_FIREBASE && firebaseConfig.projectId) {
  try {
    const app = initializeApp(firebaseConfig)
    db = getFirestore(app)
  } catch (error) {
    console.warn('Firebase initialization failed, falling back to REST API:', error)
  }
}

// Mock data for development/fallback
const mockIncidents: Incident[] = [
  {
    id: '1',
    title: '地震発生 - 震度4',
    area: '東京都新宿区',
    lat: 35.6938,
    lng: 139.7036,
    hazard: '地震',
    severity: '中',
    reportedAt: new Date().toISOString(),
    description: 'マグニチュード5.2の地震が発生しました。'
  },
  {
    id: '2',
    title: '大雨警報',
    area: '神奈川県横浜市',
    lat: 35.4437,
    lng: 139.6380,
    hazard: '大雨',
    severity: '高',
    reportedAt: new Date(Date.now() - 3600000).toISOString(),
    description: '時間雨量50mmを超える大雨が予想されます。'
  }
]

const mockAlerts: Alert[] = [
  {
    id: '1',
    title: '地震発生 - 震度4',
    area: '東京都新宿区',
    hazard: '地震',
    severity: '中',
    startedAt: new Date().toISOString(),
    description: 'マグニチュード5.2の地震が発生しました。',
    active: false  // non-Active alert
  },
  {
    id: '2',
    title: '大雨警報',
    area: '神奈川県横浜市',
    hazard: '大雨',
    severity: '高',
    startedAt: new Date(Date.now() - 3600000).toISOString(),
    description: '時間雨量50mmを超える大雨が予想されます。',
    active: true   // Active alert
  }
]

const mockFeeds: FeedItem[] = [
  {
    id: '1',
    type: 'incident',
    title: '地震情報',
    content: '震度4の地震が発生しました。',
    timestamp: new Date().toISOString(),
    source: 'システム',
    incidentId: '1'
  },
  {
    id: '2',
    type: 'alert',
    title: '大雨警報発表',
    content: '神奈川県に大雨警報が発表されました。',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    source: '気象庁'
  }
]

// Firebase API functions
const FirebaseAPI = {
  async getIncidents(since?: number): Promise<Incident[]> {
    if (!db) throw new Error('Firebase not initialized')
    
    let q = query(collection(db, 'incidents'), orderBy('reported_at', 'desc'))
    if (since) {
      q = query(q, where('reported_at', '>=', new Date(since).toISOString()))
    }
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => {
      const data = { id: doc.id, ...doc.data() } as IncidentType
      return convertIncident(data)
    })
  },

  async getIncident(id: string): Promise<Incident | null> {
    if (!db) throw new Error('Firebase not initialized')
    
    const docRef = doc(db, 'incidents', id)
    const docSnap = await getDoc(docRef)
    
    if (!docSnap.exists()) return null
    
    const data = { id: docSnap.id, ...docSnap.data() } as IncidentType
    return convertIncident(data)
  },

  async getAlerts(activeOnly?: boolean): Promise<Alert[]> {
    if (!db) throw new Error('Firebase not initialized')
    
    let q = query(collection(db, 'alerts'), orderBy('startedAt', 'desc'))
    if (activeOnly) {
      // Note: Firebase schema might not have 'active' field, so we filter by current time
      const now = Date.now()
      q = query(q, where('startedAt', '<=', now))
    }
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => {
      const data = { id: doc.id, ...doc.data() } as AlertType
      return convertAlert(data)
    })
  },

  async getAlert(id: string): Promise<Alert | null> {
    if (!db) throw new Error('Firebase not initialized')
    
    const docRef = doc(db, 'alerts', id)
    const docSnap = await getDoc(docRef)
    
    if (!docSnap.exists()) return null
    
    const data = { id: docSnap.id, ...docSnap.data() } as AlertType
    return convertAlert(data)
  },

  async getFeeds(limitCount?: number): Promise<FeedItem[]> {
    if (!db) throw new Error('Firebase not initialized')
    
    let q = query(collection(db, 'feeds'), orderBy('publishedAt', 'desc'))
    if (limitCount) {
      q = query(q, limit(limitCount))
    }
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => {
      const data = { id: doc.id, ...doc.data() } as FeedType
      return convertFeed(data)
    })
  },

  async getFeedsByIncident(incidentId: string, limitCount?: number): Promise<FeedItem[]> {
    if (!db) throw new Error('Firebase not initialized')
    
    let q = query(
      collection(db, 'feeds'),
      where('incidentId', '==', incidentId),
      orderBy('publishedAt', 'desc')
    )
    if (limitCount) {
      q = query(q, limit(limitCount))
    }
    
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => {
      const data = { id: doc.id, ...doc.data() } as FeedType
      return convertFeed(data)
    })
  }
}

// REST API functions
const RestAPI = {
  async getIncidents(since?: number): Promise<Incident[]> {
    const url = new URL(`${API_BASE_URL}/api/public/disasters`)
    if (since) url.searchParams.set('since', since.toString())
    
    const response = await fetch(url.toString())
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const data = await response.json()
    // API 서버 응답 형식: { disasters: [...], total: number }
    const disasters = data.disasters || data
    return Array.isArray(disasters) ? disasters.map((item: any) => convertApiIncident(item)) : []
  },

  async getIncident(id: string): Promise<Incident | null> {
    const response = await fetch(`${API_BASE_URL}/api/public/disasters/${id}`)
    if (response.status === 404) return null
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    
    const data = await response.json()
    return convertApiIncident(data)
  },

  async getAlerts(activeOnly?: boolean): Promise<Alert[]> {
    // API 서버에 알림 엔드포인트가 없는 경우 임시로 빈 배열 반환
    console.warn('Alert endpoint not available in API server, returning empty array')
    return []
  },

  async getAlert(id: string): Promise<Alert | null> {
    console.warn('Alert endpoint not available in API server')
    return null
  },

  async getFeeds(limitCount?: number): Promise<FeedItem[]> {
    // API 서버에 피드 엔드포인트가 없는 경우 임시로 빈 배열 반환
    console.warn('Feed endpoint not available in API server, returning empty array')
    return []
  },

  async getFeedsByIncident(incidentId: string, limitCount?: number): Promise<FeedItem[]> {
    console.warn('Feed endpoint not available in API server')
    return []
  }
}

// API 서버 응답을 프론트엔드 형식으로 변환
function convertApiIncident(apiData: any): Incident {
  return {
    id: apiData.id || apiData.event_id || Math.random().toString(),
    title: apiData.title || 'No title',
    area: apiData.location?.admin || apiData.area,
    lat: apiData.location?.lat || 0,
    lng: apiData.location?.lng || 0,
    hazard: apiData.type || apiData.hazard,
    severity: apiData.severity,
    reportedAt: apiData.reported_at || apiData.reportedAt || new Date().toISOString(),
    description: apiData.description || apiData.summary
  }
}

// Fallback to mock data for development
const MockAPI = {
  async getIncidents(since?: number): Promise<Incident[]> {
    console.warn('Using mock data for incidents')
    return mockIncidents.filter(incident => 
      !since || new Date(incident.reportedAt).getTime() >= since
    )
  },

  async getIncident(id: string): Promise<Incident | null> {
    console.warn('Using mock data for incident')
    return mockIncidents.find(incident => incident.id === id) || null
  },

  async getAlerts(activeOnly?: boolean): Promise<Alert[]> {
    console.warn('Using mock data for alerts')
    return mockAlerts.filter(alert => !activeOnly || alert.active)
  },

  async getAlert(id: string): Promise<Alert | null> {
    console.warn('Using mock data for alert')
    return mockAlerts.find(alert => alert.id === id) || null
  },

  async getFeeds(limitCount?: number): Promise<FeedItem[]> {
    console.warn('Using mock data for feeds')
    const feeds = [...mockFeeds]
    return limitCount ? feeds.slice(0, limitCount) : feeds
  },

  async getFeedsByIncident(incidentId: string, limitCount?: number): Promise<FeedItem[]> {
    console.warn('Using mock data for feeds by incident')
    const feeds = mockFeeds.filter(feed => feed.incidentId === incidentId)
    return limitCount ? feeds.slice(0, limitCount) : feeds
  }
}

// API selection with fallback chain
function createAPIWithFallback() {
  return {
    async getIncidents(since?: number): Promise<Incident[]> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getIncidents(since)
        } else {
          return await RestAPI.getIncidents(since)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getIncidents(since)
      }
    },

    async getIncident(id: string): Promise<Incident | null> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getIncident(id)
        } else {
          return await RestAPI.getIncident(id)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getIncident(id)
      }
    },

    async getAlerts(activeOnly?: boolean): Promise<Alert[]> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getAlerts(activeOnly)
        } else {
          return await RestAPI.getAlerts(activeOnly)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getAlerts(activeOnly)
      }
    },

    async getAlert(id: string): Promise<Alert | null> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getAlert(id)
        } else {
          return await RestAPI.getAlert(id)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getAlert(id)
      }
    },

    async getFeeds(limitCount?: number): Promise<FeedItem[]> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getFeeds(limitCount)
        } else {
          return await RestAPI.getFeeds(limitCount)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getFeeds(limitCount)
      }
    },

    async getFeedsByIncident(incidentId: string, limitCount?: number): Promise<FeedItem[]> {
      try {
        if (USE_FIREBASE && db) {
          return await FirebaseAPI.getFeedsByIncident(incidentId, limitCount)
        } else {
          return await RestAPI.getFeedsByIncident(incidentId, limitCount)
        }
      } catch (error) {
        console.warn('API call failed, using mock data:', error)
        return await MockAPI.getFeedsByIncident(incidentId, limitCount)
      }
    }
  }
}

export const API = createAPIWithFallback()