// Evidence (証拠情報)
export type Evidence = {
  url: string
  title?: string
  source: string
  timestamp: string
  hash: string
}

// Agent Analysis (AI分析結果)
export type AgentAnalysis = {
  risk_level: 'low' | 'medium' | 'high'
  affected_population: number
  response_priority: 'low' | 'medium' | 'high' | 'urgent'
  estimated_damage: string
}

// Location (位置情報)
export type Location = {
  lat: number
  lng: number
  admin: string
}

// Incident (災害情報) - Firestore構造準拠 + Enhanced Fields
export type Incident = {
  id: string
  event_id?: string
  title: string
  description: string
  type: 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'snow' | 'other'
  severity: 'low' | 'medium' | 'high'
  location: Location
  reported_at: string
  detected_at?: string
  confidence: number
  source: string[]
  evidence: Evidence[]
  summary?: string
  agent_analysis?: AgentAnalysis
  status: 'active' | 'monitoring' | 'resolved' | 'investigating'
  tags?: string[]
  is_active?: boolean
  last_updated?: string
  
  // 🔥 Enhanced Fields - Priority Medium Implementation
  bulletins_count?: number
  latest_bulletin_id?: string
  last_bulletin_at?: string
  affected_population?: number
  risk_assessment?: string
  related_news_count?: number
  orchestration_started_at?: string
  has_analysis?: boolean
  has_collected_info?: boolean
}

// API Response
export type DisasterApiResponse = {
  disasters: Incident[]
  total: number
  available_total?: number
  timestamp: string
  source: string
}
