'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import type { Incident } from '@/types/incident'

type Props = {
  incidents: Incident[]
  center?: google.maps.LatLngLiteral
  zoom?: number
  onCountsChange?: (counts: { active: number; total: number }) => void
  onSelect?: (incident: Incident) => void
}

export default function IncidentMap({ incidents, center, zoom = 7, onCountsChange, onSelect }: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapObj = useRef<google.maps.Map | null>(null)
  const markers = useRef<{ marker: google.maps.Marker; isActive: boolean; incident: Incident }[]>([])
  const [mapReady, setMapReady] = useState(false)
  const infoRef = useRef<google.maps.InfoWindow | null>(null)

  const mapCenter = useMemo(
    () => center ?? ({ lat: 35.681236, lng: 139.767125 }),
    [center]
  )

  function markerIcon(isActive: boolean): google.maps.Symbol {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 6,
      fillColor: isActive ? '#ef4444' : '#3b82f6',
      fillOpacity: 1,
      strokeColor: '#ffffff',
      strokeOpacity: 1,
      strokeWeight: 2,
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
    const loader = new Loader({
      apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
      version: 'weekly',
    })
    let mounted = true
    loader.load().then(() => {
      if (!mounted || !mapRef.current) return
      mapObj.current = new google.maps.Map(mapRef.current, {
        center: mapCenter, zoom,
        mapTypeControl: false, fullscreenControl: false, streetViewControl: false,
      })
      mapObj.current.addListener('idle', recalcCountsInViewport)
      infoRef.current = new google.maps.InfoWindow()
      setMapReady(true)
    })
    return () => {
      mounted = false
      markers.current.forEach(m => m.marker.setMap(null))
      markers.current = []
    }
  }, [mapCenter, zoom])

  useEffect(() => {
    if (!mapReady || !mapObj.current) return
    markers.current.forEach(m => m.marker.setMap(null))
    markers.current = []

    incidents.forEach(i => {
      const active = i.status === 'active'
      const m = new google.maps.Marker({
        position: { lat: i.location.lat, lng: i.location.lng },
        map: mapObj.current!,
        title: i.title,
        icon: markerIcon(active),
      })
      m.addListener('click', () => {
        onSelect?.(i)
        if (!infoRef.current) return
        infoRef.current.setContent(
            `<div style="min-width:280px;color:#000;line-height:1.4;">
                <div style="font-weight:700;font-size:14px;margin-bottom:8px;">
                ${i.title}
                </div>
                ${i.location?.admin ?? '—'}${i.location?.admin ? '<br/>' : ''}
                種別: ${i.type ?? '—'} / 重要度: ${i.severity ?? '—'}<br/>
                状態: ${i.status === 'active' ? '<span style="color:#ef4444;font-weight:bold;">Active</span>' : '<span style="color:#6b7280;">Monitoring</span>'}<br/>
                ${i.reported_at ? new Date(i.reported_at).toLocaleString() : ''}
                ${i.affected_population ? '<br/>影響人口: <b>' + i.affected_population.toLocaleString() + '人</b>' : ''}
                ${i.risk_assessment && i.risk_assessment !== 'unknown' ? '<br/>リスク評価: <b>' + i.risk_assessment + '</b>' : ''}
                ${i.bulletins_count ? '<br/>公報: ' + i.bulletins_count + '件' : ''}
                ${i.related_news_count ? '<br/>関連ニュース: ' + i.related_news_count + '件' : ''}
            </div>`
            )
        infoRef.current.open({ map: mapObj.current!, anchor: m })
        })
      markers.current.push({ marker: m, isActive: active, incident: i })
    })

    recalcCountsInViewport()
  }, [mapReady, incidents])

  return (
    <div className="w-full h-[60vh] rounded-xl border border-gray-200 overflow-hidden">
      <div ref={mapRef} className="w-full h-full" aria-label="Incident Map" />
    </div>
  )
}
