export type AlertLevel = 'info' | 'advisory' | 'watch' | 'warning' | 'emergency'
export type HazardType = 'earthquake' | 'typhoon' | 'flood' | 'landslide' | 'tsunami' | 'wildfire' | 'other'

export type Alert = {
  id: string           
  title: string       
  level: AlertLevel   
  hazard: HazardType   
  area: string        
  startedAt: number     
  updatedAt?: number    
}
