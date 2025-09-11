'use client'

import { useEffect, useState } from 'react'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../utils/firebase'
import type { Incident } from '../types/incident'

export function useIncidents() {
 const [incidents, setIncidents] = useState<Incident[]>([])
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState<string | null>(null)

 useEffect(() => {
  const q = collection(db, 'incidents')
  const unsub = onSnapshot(
   q,
   snap => {
    const next = snap.docs.map(d => {
     const data = d.data() as any
     return {
      id: d.id,
      title: data.title ?? 'Untitled',
      lat: data.lat,
      lng: data.lng,
      severity: data.severity ?? 'low',
      reportedAt: data.reportedAt ?? Date.now(),
     } as Incident
    })
    setIncidents(next)
    setLoading(false)
   },
   err => {
    setError(err.message)
    setLoading(false)
   }
  )
  return () => unsub()
 }, [])

 return { incidents, loading, error }
}
