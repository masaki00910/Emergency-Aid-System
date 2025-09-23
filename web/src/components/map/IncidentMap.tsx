'use client'

import { useEffect, useMemo, useRef, useState, memo } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import type { Incident } from '@/types/incident'

declare global {
  interface Window {
    google: any
  }
}

type Props = {
  incidents: Incident[]
  center?: { lat: number; lng: number }
  zoom?: number
  onCountsChange?: (counts: { active: number; total: number }) => void
  onSelect?: (incident: Incident) => void
  focusIncidentId?: string
}

function IncidentMap({ incidents, center, zoom = 7, onCountsChange, onSelect, focusIncidentId }: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapObj = useRef<any>(null)
  const markers = useRef<{ marker: any; isActive: boolean; incident: Incident }[]>([])
  const [mapReady, setMapReady] = useState(false)
  const infoRef = useRef<any>(null)

  const mapCenter = useMemo(
    () => center ?? ({ lat: 35.681236, lng: 139.767125 }),
    [center]
  )

  function markerIcon(isActive: boolean): any {
    return {
      path: 0, // google.maps.SymbolPath.CIRCLE
      scale: 8,
      fillColor: isActive ? '#dc2626' : '#2563eb', // Modern red for active, modern blue for inactive
      fillOpacity: 0.9,
      strokeColor: '#ffffff',
      strokeOpacity: 1,
      strokeWeight: 3,
    }
  }

  function recalcCountsInViewport() {
    if (!mapObj.current) return
    const b = mapObj.current.getBounds()
    if (!b) return
    let total = 0, active = 0
    for (const { marker, isActive } of markers.current) {
      const pos = marker.getPosition()
      if (pos && b.contains(pos)) { total++; if (isActive) active++ }
    }
    onCountsChange?.({ active, total })
  }

  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    
    if (!apiKey) {
      console.error('Google Maps API key is missing. Please check NEXT_PUBLIC_GOOGLE_MAPS_API_KEY environment variable.')
      return
    }

    const loader = new Loader({
      apiKey: apiKey,
      version: 'weekly',
      libraries: ['maps', 'marker']
    })
    
    let mounted = true
    
    loader.load()
      .then(() => {
        if (!mounted || !mapRef.current || !window.google?.maps) {
          console.warn('Google Maps: Component unmounted or API not available')
          return
        }
        
        mapObj.current = new window.google.maps.Map(mapRef.current, {
          center: mapCenter, 
          zoom,
          mapTypeControl: false, 
          fullscreenControl: false, 
          streetViewControl: false,
        })
        
        mapObj.current.addListener('idle', recalcCountsInViewport)
        infoRef.current = new window.google.maps.InfoWindow()
        setMapReady(true)
        console.log('Google Maps loaded successfully')
      })
      .catch((error) => {
        console.error('Google Maps failed to load:', error)
        console.error('Error type:', error.name)
        console.error('Error message:', error.message)
        console.error('Please check:')
        console.error('1. API key is valid and has access to Maps JavaScript API')
        console.error('2. Billing is enabled for your Google Cloud project')
        console.error('3. Maps JavaScript API is enabled in Google Cloud Console')
      })
    
    return () => {
      mounted = false
      markers.current.forEach(m => m.marker.setMap(null))
      markers.current = []
    }
  }, [mapCenter, zoom])

  useEffect(() => {
    if (!mapReady || !mapObj.current) {
      return
    }
    
    markers.current.forEach(m => m.marker.setMap(null))
    markers.current = []

    incidents.forEach(i => {
      // Skip incidents without valid location data
      if (!i.location || typeof i.location.lat !== 'number' || typeof i.location.lng !== 'number') {
        return
      }
      
      // Use same active conditions as feeds and alerts
      const hazardMapping: Record<string, {name: string, icon: string}> = {
        'earthquake': {name: '地震', icon: '🌍'},
        'tsunami': {name: '津波', icon: '🌊'}, 
        'flood': {name: '洪水', icon: '💧'},
        'typhoon': {name: '台風', icon: '🌀'},
        'landslide': {name: '土砂災害', icon: '⛰️'},
        'volcano': {name: '火山', icon: '🌋'},
        'wildfire': {name: '山火事', icon: '🔥'},
        'other': {name: 'その他', icon: '⚠️'}
      }
      const hazardInfo = hazardMapping[i.type] || hazardMapping['other']
      const active = Boolean(i.is_active && i.severity !== 'low' && hazardInfo.name !== 'その他' && hazardInfo.name !== '')
      
      const iconConfig = markerIcon(active)
      
      const m = new window.google.maps.Marker({
        position: { lat: i.location.lat, lng: i.location.lng },
        title: i.title,
        icon: iconConfig,
      })
      
      // Explicitly set the map after marker creation
      m.setMap(mapObj.current)
      
      
      m.addListener('click', () => {
        onSelect?.(i)
        if (!infoRef.current) return
        // Reuse hazardInfo from above
        const displayArea = !i.location?.admin || i.location.admin === '不明' || i.location.admin === 'unknown' ? '地域不明' : i.location.admin
        
        // Time ago function for consistent time display
        const timeAgo = (reportedAt: number) => {
          const diff = Math.max(1, Math.round((Date.now() - reportedAt) / 60000))
          if (diff < 60) return `${diff}分前`
          const h = Math.round(diff / 60)
          return `${h}時間前`
        }
        
        infoRef.current.setContent(
            `<div style="min-width:320px;max-width:360px;padding:0;color:#334155;line-height:1.5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;font-size:14px;color:#64748b;">
                    <span style="font-size:18px;">${hazardInfo.icon}</span>
                    <span style="font-weight:500;">${displayArea}</span>
                </div>
                
                <div style="font-weight:600;color:#1e293b;font-size:16px;line-height:1.4;margin-bottom:12px;">
                    ${i.title}
                </div>
                
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;">
                    <span style="display:inline-flex;align-items:center;gap:4px;background:linear-gradient(to right,#f1f5f9,#e2e8f0);border-radius:9999px;padding:4px 12px;font-size:12px;font-weight:500;color:#475569;">
                        🏷️ ${hazardInfo.name}
                    </span>
                    <span style="display:inline-flex;align-items:center;gap:4px;background:linear-gradient(to right,${
                      i.severity === 'high' ? '#fef2f2,#fee2e2);color:#dc2626' : 
                      i.severity === 'medium' ? '#fffbeb,#fef3c7);color:#d97706' : 
                      '#eff6ff,#dbeafe);color:#2563eb'
                    });border-radius:9999px;padding:4px 12px;font-size:12px;font-weight:500;">
                        📊 深刻度：${i.severity === 'high' ? '高' : i.severity === 'medium' ? '中' : '低'}
                    </span>
                    ${active ? `<span style="display:inline-flex;align-items:center;gap:4px;background:linear-gradient(to right,#ef4444,#dc2626);color:white;border-radius:9999px;padding:4px 12px;font-size:12px;font-weight:500;">🚨 アクティブ</span>` : ''}
                </div>
                
                <div style="font-size:12px;color:#6b7280;display:flex;align-items:center;gap:4px;">
                    🕒 ${i.reported_at ? timeAgo(new Date(i.reported_at).getTime()) : '時刻不明'}
                </div>
            </div>`
            )
        infoRef.current.open({ map: mapObj.current!, anchor: m })
        })
      markers.current.push({ marker: m, isActive: active, incident: i })
    })

    recalcCountsInViewport()
  }, [mapReady, incidents])

  // Focus on specific incident when focusIncidentId changes
  useEffect(() => {
    if (!mapReady || !mapObj.current || !focusIncidentId) return

    const targetMarker = markers.current.find(m => m.incident.id === focusIncidentId)
    
    if (targetMarker) {
      const position = targetMarker.marker.getPosition()
      if (position) {
        // Pan to marker and zoom in slightly
        mapObj.current.panTo(position)
        mapObj.current.setZoom(Math.max(10, mapObj.current.getZoom() || 7))
        
        // Trigger click on the marker to show info window
        setTimeout(() => {
          if (window.google?.maps) {
            window.google.maps.event.trigger(targetMarker.marker, 'click')
          }
        }, 300)
      }
    }
  }, [mapReady, focusIncidentId])

  return (
    <div className="w-full h-[60vh] rounded-xl border border-gray-200 overflow-hidden">
      <div ref={mapRef} className="w-full h-full" aria-label="Incident Map" />
    </div>
  )
}

// Memoize the component to prevent unnecessary re-renders
export default memo(IncidentMap, (prevProps, nextProps) => {
  // Deep comparison for incidents array
  if (prevProps.incidents.length !== nextProps.incidents.length) return false
  
  for (let i = 0; i < prevProps.incidents.length; i++) {
    if (prevProps.incidents[i].id !== nextProps.incidents[i].id) return false
    if (prevProps.incidents[i].is_active !== nextProps.incidents[i].is_active) return false
  }
  
  // Compare other props
  return (
    prevProps.center?.lat === nextProps.center?.lat &&
    prevProps.center?.lng === nextProps.center?.lng &&
    prevProps.zoom === nextProps.zoom &&
    prevProps.focusIncidentId === nextProps.focusIncidentId
  )
})
