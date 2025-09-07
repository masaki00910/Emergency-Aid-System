'use client'

import { useEffect, useMemo, useRef } from 'react'
import { Loader } from '@googlemaps/js-api-loader'
import type { Incident } from '@/types/incident'

type Props = {
  incidents: Incident[]
  center?: google.maps.LatLngLiteral
  zoom?: number
}

export default function IncidentMap({ incidents, center, zoom = 7 }: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapObj = useRef<google.maps.Map | null>(null)
  const markers = useRef<google.maps.Marker[]>([])

  const mapCenter = useMemo(
    () => center ?? ({ lat: 35.681236, lng: 139.767125 }),
    [center]
  )

  useEffect(() => {
    const loader = new Loader({
      apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
      version: 'weekly',
    })

    let mounted = true
    loader.load().then(() => {
      if (!mounted || !mapRef.current) return
      mapObj.current = new google.maps.Map(mapRef.current, {
        center: mapCenter,
        zoom,
        mapTypeControl: false,
        fullscreenControl: false,
        streetViewControl: false,
      })
    })

    return () => {
      mounted = false
      markers.current.forEach(m => m.setMap(null))
    }
  }, [mapCenter, zoom])

  useEffect(() => {
    if (!mapObj.current) return

    markers.current.forEach(m => m.setMap(null))
    markers.current = []

    incidents.forEach(i => {
      const m = new google.maps.Marker({
        position: { lat: i.lat, lng: i.lng },
        map: mapObj.current!, 
        title: i.title,
      })
      const info = new google.maps.InfoWindow({
        content: `<div style="min-width:180px">
          <strong>${i.title}</strong><br/>
          severity: ${i.severity ?? 'low'}<br/>
          ${i.reportedAt ? new Date(i.reportedAt).toLocaleString() : ''}
        </div>`,
      })
      m.addListener('click', () => info.open({ map: mapObj.current!, anchor: m }))
      markers.current.push(m)
    })
  }, [incidents])

  return (
    <div className="w-full h-[60vh] rounded-xl border border-gray-200 overflow-hidden">
      <div ref={mapRef} className="w-full h-full" aria-label="Incident Map" />
    </div>
  )
}
