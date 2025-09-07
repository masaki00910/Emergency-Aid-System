export type Incident = {
 id: string
 title: string
 lat: number
 lng: number
 severity?: 'low' | 'medium' | 'high'
 reportedAt?: number  // timestamp(ms)
}
