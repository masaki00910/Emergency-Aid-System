export type Incident = {
  id: string
  title: string
  lat: number
  lng: number
  severity?: 'low' | 'medium' | 'high'
  reportedAt?: number
  isActive?: boolean
  hazard?: 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'other'
  area?: string
  description?: string
}
