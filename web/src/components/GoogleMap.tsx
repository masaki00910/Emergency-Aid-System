'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader } from '@googlemaps/js-api-loader'

interface MapIncident {
  id: string
  lat: number
  lng: number
  title: string
  isActive: boolean
}

interface Props {
  lat: number
  lng: number
  incidents: MapIncident[]
  zoom?: number
}

export default function GoogleMap({ lat, lng, incidents, zoom = 12 }: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapObj = useRef<google.maps.Map | null>(null)
  const [mapReady, setMapReady] = useState(false)

  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    
    if (!apiKey) {
      console.error('Google Maps API key is missing. Please check NEXT_PUBLIC_GOOGLE_MAPS_API_KEY environment variable.')
      if (mapRef.current) {
        mapRef.current.innerHTML = `
          <div class="w-full h-full flex items-center justify-center bg-red-50 text-red-600 border border-red-200">
            <div class="text-center">
              <div class="text-4xl mb-2">❌</div>
              <div>Google Maps APIキーがありません</div>
              <div class="text-sm mt-1">環境変数を確認してください</div>
            </div>
          </div>
        `
      }
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
        
        mapObj.current = new google.maps.Map(mapRef.current, {
          center: { lat, lng },
          zoom,
          mapTypeControl: false,
          fullscreenControl: false,
          streetViewControl: false,
        })
        
        setMapReady(true)
        console.log('Google Maps loaded successfully')
      })
      .catch((error) => {
        console.error('Google Maps failed to load:', error)
        console.error('Error type:', error.name)
        console.error('Error message:', error.message)
        
        // Enhanced fallback UI with error details
        if (mapRef.current) {
          mapRef.current.innerHTML = `
            <div class="w-full h-full flex items-center justify-center bg-gray-100 text-gray-500">
              <div class="text-center">
                <div class="text-4xl mb-2">📍</div>
                <div>地図を読み込めませんでした</div>
                <div class="text-sm mt-1">位置: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                <div class="text-xs mt-2 text-gray-400">API接続エラー: ${error.message}</div>
              </div>
            </div>
          `
        }
      })

    return () => {
      mounted = false
    }
  }, [lat, lng, zoom])

  useEffect(() => {
    if (!mapReady || !mapObj.current) return

    // Add markers for incidents
    incidents.forEach(incident => {
      const marker = new google.maps.Marker({
        position: { lat: incident.lat, lng: incident.lng },
        map: mapObj.current!,
        title: incident.title,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: incident.isActive ? '#ef4444' : '#3b82f6',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeOpacity: 1,
          strokeWeight: 2,
        }
      })

      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #000; line-height: 1.4;">
            <div style="font-weight: bold; margin-bottom: 4px;">${incident.title}</div>
            <div style="font-size: 12px; color: #666;">
              状態: ${incident.isActive ? '<span style="color: red;">Active</span>' : 'Inactive'}
            </div>
          </div>
        `
      })

      marker.addListener('click', () => {
        infoWindow.open(mapObj.current!, marker)
      })
    })
  }, [mapReady, incidents])

  return <div ref={mapRef} className="w-full h-full rounded" />
}