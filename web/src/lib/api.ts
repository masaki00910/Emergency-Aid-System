import { db } from '../utils/firebase'
import { collection, getDocs, query, orderBy, where, limit, doc, getDoc } from 'firebase/firestore'
import type { Incident } from '@/types/incident'
import type { Alert } from '@/types/alert'
import type { FeedItem } from '@/types/feed'
import type { AIFAQResponse, AIGeneratedFAQ } from '@/types/ai-faq'

// Re-export types for convenience
export type { Incident, Alert, FeedItem, AIFAQResponse, AIGeneratedFAQ }

export class ApiService {
  // Incidents API
  static async getIncidents(since?: number): Promise<Incident[]> {
    try {
      // Firebaseが利用できない場合はMockデータを使用
      if (!db) {
        let incidents = mockIncidents
        if (since) {
          incidents = incidents.filter(incident => incident.reported_at && new Date(incident.reported_at).getTime() >= since)
        }
        return incidents.sort((a, b) => {
          const aTime = a.reported_at ? new Date(a.reported_at).getTime() : 0
          const bTime = b.reported_at ? new Date(b.reported_at).getTime() : 0
          return bTime - aTime
        })
      }

      const incidentsRef = collection(db, 'incidents')
      let q = query(incidentsRef, orderBy('reported_at', 'desc'))

      if (since) {
        q = query(incidentsRef, where('reported_at', '>=', since), orderBy('reported_at', 'desc'))
      }

      const snapshot = await getDocs(q)
      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Incident))
    } catch (error) {
      console.error('Error fetching incidents, falling back to mock data:', error)
      let incidents = mockIncidents
      if (since) {
        incidents = incidents.filter(incident => incident.reported_at && new Date(incident.reported_at).getTime() >= since)
      }
      return incidents.sort((a, b) => {
        const aTime = a.reported_at ? new Date(a.reported_at).getTime() : 0
        const bTime = b.reported_at ? new Date(b.reported_at).getTime() : 0
        return bTime - aTime
      })
    }
  }

  static async getIncident(id: string): Promise<Incident | null> {
    try {
      const docRef = doc(db, 'incidents', id)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        return { id: docSnap.id, ...docSnap.data() } as Incident
      }
      return null
    } catch (error) {
      console.error('Error fetching incident:', error)
      throw error
    }
  }

  // Alerts API
  static async getAlerts(activeOnly: boolean = false): Promise<Alert[]> {
    try {
      // Firebaseが利用できない場合はMockデータを使用
      if (!db) {
        let alerts = mockAlerts
        // activeOnlyは簡易的に最近のアラートのみ返す
        if (activeOnly) {
          const oneHourAgo = Date.now() - 60 * 60 * 1000
          alerts = alerts.filter(alert => alert.startedAt > oneHourAgo)
        }
        return alerts.sort((a, b) => b.startedAt - a.startedAt)
      }

      const alertsRef = collection(db, 'alerts')
      let q = query(alertsRef, orderBy('startedAt', 'desc'))

      if (activeOnly) {
        // アクティブなアラートのみ取得するロジック（必要に応じてバックエンドでisActiveフィールド追加が必要）
        q = query(alertsRef, orderBy('startedAt', 'desc'))
      }

      const snapshot = await getDocs(q)
      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Alert))
    } catch (error) {
      console.error('Error fetching alerts, falling back to mock data:', error)
      let alerts = mockAlerts
      if (activeOnly) {
        const oneHourAgo = Date.now() - 60 * 60 * 1000
        alerts = alerts.filter(alert => alert.startedAt > oneHourAgo)
      }
      return alerts.sort((a, b) => b.startedAt - a.startedAt)
    }
  }

  static async getAlert(id: string): Promise<Alert | null> {
    try {
      // Firebaseが利用できない場合はMockデータを使用
      if (!db) {
        return mockAlerts.find(alert => alert.id === id) || null
      }

      const docRef = doc(db, 'alerts', id)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        return { id: docSnap.id, ...docSnap.data() } as Alert
      }
      return null
    } catch (error) {
      console.error('Error fetching alert, falling back to mock data:', error)
      return mockAlerts.find(alert => alert.id === id) || null
    }
  }

  // Feeds API
  static async getFeeds(limitCount: number = 50): Promise<FeedItem[]> {
    try {
      // Firebaseが利用できない場合はMockデータを使用
      if (!db) {
        return mockFeeds
          .sort((a, b) => b.publishedAt - a.publishedAt)
          .slice(0, limitCount)
      }

      const feedsRef = collection(db, 'feeds')
      const q = query(feedsRef, orderBy('publishedAt', 'desc'), limit(limitCount))

      const snapshot = await getDocs(q)
      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as FeedItem))
    } catch (error) {
      console.error('Error fetching feeds, falling back to mock data:', error)
      return mockFeeds
        .sort((a, b) => b.publishedAt - a.publishedAt)
        .slice(0, limitCount)
    }
  }

  static async getFeedsByIncident(incidentId: string, limitCount: number = 50): Promise<FeedItem[]> {
    try {
      const feedsRef = collection(db, 'feeds')
      const q = query(
        feedsRef,
        where('incidentId', '==', incidentId),
        orderBy('publishedAt', 'desc'),
        limit(limitCount)
      )

      const snapshot = await getDocs(q)
      return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as FeedItem))
    } catch (error) {
      console.error('Error fetching feeds by incident:', error)
      throw error
    }
  }

  // AI FAQ API - Real implementation using backend FAQ service
  static async getAIFAQByAlert(alertId: string): Promise<AIFAQResponse | null> {
    try {
      const response = await fetch(`/api/faq/${alertId}`)
      if (!response.ok) {
        console.error('Failed to fetch FAQ from backend API')
        return null
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching AI FAQ:', error)
      return null
    }
  }

  static async getActiveFAQs(): Promise<AIFAQResponse[]> {
    try {
      const response = await fetch('/api/faq/active')
      if (!response.ok) {
        console.error('Failed to fetch active FAQs')
        return []
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching active FAQs:', error)
      return []
    }
  }


  static async getFAQsByIncident(incidentId: string): Promise<AIGeneratedFAQ[]> {
    try {
      const faqResponse = await this.getAIFAQByAlert(incidentId)
      return faqResponse?.faqs || []
    } catch (error) {
      console.error('Error fetching FAQs for incident:', error)
      return []
    }
  }

  static async askFAQQuestion(incidentId: string, question: string): Promise<string> {
    try {
      const response = await fetch(`/api/faq/${incidentId}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error('Failed to get answer from FAQ API')
      }

      const data = await response.json()
      return data.answer || 'No answer received'
    } catch (error) {
      console.error('Error asking FAQ question:', error)
      throw error
    }
  }
}

// REST API Service for localhost:8082 integration
export class RestApiService {
  private static baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8082'

  // Transform API disaster data to Incident format
  private static transformDisasterToIncident(disaster: any): Incident {
    return {
      id: disaster.id,
      title: disaster.title,
      description: disaster.description,
      type: disaster.type as 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'snow' | 'other',
      severity: disaster.severity as 'low' | 'medium' | 'high',
      location: disaster.location,
      reported_at: disaster.reported_at,
      confidence: disaster.confidence,
      source: disaster.source || [],
      evidence: disaster.evidence || [],
      status: disaster.status as 'active' | 'monitoring' | 'resolved' | 'investigating',
      bulletins_count: disaster.bulletins_count,
      latest_bulletin_id: disaster.latest_bulletin_id,
      last_bulletin_at: disaster.last_bulletin_at,
      affected_population: disaster.affected_population,
      risk_assessment: disaster.risk_assessment,
      related_news_count: disaster.related_news_count,
      orchestration_started_at: disaster.orchestration_started_at,
      has_analysis: disaster.has_analysis,
      has_collected_info: disaster.has_collected_info
    }
  }

  // Transform disaster data to Alert format
  private static transformDisasterToAlert(disaster: any): Alert {
    return {
      id: disaster.id,
      title: disaster.title,
      level: disaster.severity === 'high' ? 'warning' as const : disaster.severity === 'medium' ? 'watch' as const : 'info' as const,
      hazard: disaster.type as 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'other',
      area: disaster.location?.admin || '不明',
      startedAt: new Date(disaster.reported_at).getTime(),
      updatedAt: disaster.last_bulletin_at ? new Date(disaster.last_bulletin_at).getTime() : undefined,
      summary: disaster.description,
      description: disaster.description
    }
  }

  // Helper function to deduplicate incidents based on title + description
  private static deduplicateIncidents(incidents: Incident[]): Incident[] {
    const seen = new Map<string, Incident>()

    for (const incident of incidents) {
      // Create a unique key from title + description (or URL if available)
      const key = `${incident.title}-${incident.description}`.toLowerCase().trim()

      if (!seen.has(key)) {
        seen.set(key, incident)
      } else {
        // Keep the more recent one
        const existing = seen.get(key)!
        const existingTime = existing.reported_at ? new Date(existing.reported_at).getTime() : 0
        const currentTime = incident.reported_at ? new Date(incident.reported_at).getTime() : 0

        if (currentTime > existingTime) {
          seen.set(key, incident)
        }
      }
    }

    return Array.from(seen.values())
  }

  static async getIncidents(since?: number): Promise<Incident[]> {
    try {
      const response = await fetch(`/api/disasters`)
      if (!response.ok) {
        console.error('Failed to fetch disasters from API')
        return []
      }
      const data = await response.json()
      const incidents = data.disasters.map(this.transformDisasterToIncident)

      // Deduplicate incidents to remove articles with same title+description
      const dedupedIncidents = this.deduplicateIncidents(incidents)

      if (since) {
        return dedupedIncidents.filter(incident =>
          incident.reported_at && new Date(incident.reported_at).getTime() >= since
        )
      }

      return dedupedIncidents.sort((a, b) => {
        const aTime = a.reported_at ? new Date(a.reported_at).getTime() : 0
        const bTime = b.reported_at ? new Date(b.reported_at).getTime() : 0
        return bTime - aTime
      })
    } catch (error) {
      console.error('Error fetching incidents:', error)
      return []
    }
  }

  static async getIncident(id: string): Promise<Incident | null> {
    try {
      const response = await fetch(`/api/disasters/${id}`)
      if (!response.ok) return null
      const disaster = await response.json()
      return this.transformDisasterToIncident(disaster)
    } catch (error) {
      console.error('Error fetching incident:', error)
      return null
    }
  }

  // Helper function to deduplicate alerts based on title + description
  private static deduplicateAlerts(alerts: Alert[]): Alert[] {
    const seen = new Map<string, Alert>()

    for (const alert of alerts) {
      // Create a unique key from title + description/summary
      const key = `${alert.title}-${alert.description || alert.summary || ''}`.toLowerCase().trim()

      if (!seen.has(key)) {
        seen.set(key, alert)
      } else {
        // Keep the more recent one
        const existing = seen.get(key)!
        const existingTime = existing.startedAt
        const currentTime = alert.startedAt

        if (currentTime > existingTime) {
          seen.set(key, alert)
        }
      }
    }

    return Array.from(seen.values())
  }

  // Helper function to deduplicate feeds based on title + url combination
  private static deduplicateFeeds(feeds: FeedItem[]): FeedItem[] {
    const seen = new Map<string, FeedItem>()

    for (const feed of feeds) {
      // Create a unique key from title + url
      const key = `${feed.title}-${feed.url || ''}`.toLowerCase().trim()

      if (!seen.has(key)) {
        seen.set(key, feed)
      } else {
        // Keep the more recent one
        const existing = seen.get(key)!
        const existingTime = existing.publishedAt
        const currentTime = feed.publishedAt

        if (currentTime > existingTime) {
          seen.set(key, feed)
        }
      }
    }

    return Array.from(seen.values())
  }

  static async getAlerts(activeOnly: boolean = false): Promise<Alert[]> {
    try {
      const response = await fetch(`/api/disasters`)
      if (!response.ok) {
        console.error('Failed to fetch disasters for alerts')
        return []
      }
      const data = await response.json()
      let alerts = data.disasters.map(this.transformDisasterToAlert)

      // Deduplicate alerts to remove duplicates with same title+description
      alerts = this.deduplicateAlerts(alerts)

      if (activeOnly) {
        alerts = alerts.filter(alert => {
          // Consider disasters from last 24 hours as "active"
          const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000
          return alert.startedAt > oneDayAgo
        })
      }

      return alerts.sort((a, b) => b.startedAt - a.startedAt)
    } catch (error) {
      console.error('Error fetching alerts:', error)
      return []
    }
  }

  static async getAlert(id: string): Promise<Alert | null> {
    try {
      const response = await fetch(`/api/disasters/${id}`)
      if (!response.ok) return null
      const disaster = await response.json()
      return this.transformDisasterToAlert(disaster)
    } catch (error) {
      console.error('Error fetching alert:', error)
      return null
    }
  }

  static async getFeeds(limitCount: number = 50): Promise<FeedItem[]> {
    try {
      // Since there's no feed endpoint, create feeds from disaster evidence
      const response = await fetch(`/api/disasters`)
      if (!response.ok) {
        console.error('Failed to fetch disasters for feeds')
        return []
      }
      const data = await response.json()

      const feeds: FeedItem[] = []
      data.disasters.forEach((disaster: any) => {
        if (disaster.evidence && Array.isArray(disaster.evidence)) {
          disaster.evidence.forEach((evidence: any, index: number) => {
            feeds.push({
              id: `${disaster.id}-evidence-${index}`,
              incidentId: disaster.id,
              source: evidence.source || 'unknown',
              title: evidence.title || disaster.title,
              content: evidence.description || disaster.description,
              summary: disaster.description,
              url: evidence.url || '',
              publishedAt: evidence.timestamp ? new Date(evidence.timestamp).getTime() : new Date(disaster.reported_at).getTime(),
              labels: [disaster.type, disaster.severity],
              area: disaster.location?.admin || '不明',
              hazard: disaster.type,
              category: disaster.type,
              severity: disaster.severity,
              isAlertCandidate: disaster.severity === 'high',
              isVerified: evidence.verified || false
            })
          })
        }
      })

      // Deduplicate feeds based on title + url combination
      const dedupedFeeds = this.deduplicateFeeds(feeds)

      return dedupedFeeds
        .sort((a, b) => b.publishedAt - a.publishedAt)
        .slice(0, limitCount)
    } catch (error) {
      console.error('Error fetching feeds:', error)
      return []
    }
  }

  static async getFeedsByIncident(incidentId: string, limitCount: number = 50): Promise<FeedItem[]> {
    try {
      const allFeeds = await this.getFeeds(1000) // Get all feeds first
      return allFeeds
        .filter(feed => feed.incidentId === incidentId)
        .slice(0, limitCount)
    } catch (error) {
      console.error('Error fetching feeds by incident:', error)
      return []
    }
  }

  // AI FAQ API - Real implementation using backend FAQ service
  static async getAIFAQByAlert(alertId: string): Promise<AIFAQResponse | null> {
    try {
      const response = await fetch(`/api/faq/${alertId}`)
      if (!response.ok) {
        console.error('Failed to fetch FAQ from backend API')
        return null
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching AI FAQ:', error)
      return null
    }
  }

  static async getActiveFAQs(): Promise<AIFAQResponse[]> {
    try {
      const response = await fetch('/api/faq/active')
      if (!response.ok) {
        console.error('Failed to fetch active FAQs')
        return []
      }
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching active FAQs:', error)
      return []
    }
  }

  static async getFAQsByIncident(incidentId: string): Promise<AIGeneratedFAQ[]> {
    try {
      const faqResponse = await this.getAIFAQByAlert(incidentId)
      return faqResponse?.faqs || []
    } catch (error) {
      console.error('Error fetching FAQs for incident:', error)
      return []
    }
  }

  static async askFAQQuestion(incidentId: string, question: string): Promise<string> {
    try {
      const response = await fetch(`/api/faq/${incidentId}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error('Failed to get answer from FAQ API')
      }

      const data = await response.json()
      return data.answer || 'No answer received'
    } catch (error) {
      console.error('Error asking FAQ question:', error)
      throw error
    }
  }
}

// Export the preferred API service
export const API = process.env.NEXT_PUBLIC_USE_FIREBASE === 'true' ? ApiService : RestApiService