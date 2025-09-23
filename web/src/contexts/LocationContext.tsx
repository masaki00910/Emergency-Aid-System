'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Location, GeolocationResult, getUserLocation, DEFAULT_LOCATION, isValidLocation } from '@/lib/geocoding'

interface LocationContextType {
  userLocation: Location | null
  isLoading: boolean
  error: string | null
  accuracy: number | null
  hasPermission: boolean
  requestLocation: () => Promise<void>
  clearError: () => void
}

const LocationContext = createContext<LocationContextType | undefined>(undefined)

interface LocationProviderProps {
  children: ReactNode
}

export function LocationProvider({ children }: LocationProviderProps) {
  const [userLocation, setUserLocation] = useState<Location | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [accuracy, setAccuracy] = useState<number | null>(null)
  const [hasPermission, setHasPermission] = useState(false)

  const clearError = () => setError(null)

  const requestLocation = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result: GeolocationResult = await getUserLocation()

      if (isValidLocation(result.location)) {
        setUserLocation(result.location)
        setAccuracy(result.accuracy)
        setHasPermission(true)

        // Store in localStorage for future sessions
        localStorage.setItem('userLocation', JSON.stringify(result.location))
        localStorage.setItem('locationTimestamp', Date.now().toString())
      } else {
        throw new Error('Invalid location coordinates received')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown location error'
      setError(errorMessage)
      setHasPermission(false)

      // Fall back to default location (Tokyo)
      setUserLocation(DEFAULT_LOCATION)
      console.warn('Using default location due to geolocation error:', errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Check for stored location first
    const storedLocation = localStorage.getItem('userLocation')
    const storedTimestamp = localStorage.getItem('locationTimestamp')

    if (storedLocation && storedTimestamp) {
      const timestamp = parseInt(storedTimestamp, 10)
      const now = Date.now()
      const fiveMinutes = 5 * 60 * 1000

      // Use stored location if it's less than 5 minutes old
      if (now - timestamp < fiveMinutes) {
        try {
          const location = JSON.parse(storedLocation)
          if (isValidLocation(location)) {
            setUserLocation(location)
            setHasPermission(true)
            return
          }
        } catch (error) {
          console.warn('Failed to parse stored location:', error)
        }
      }
    }

    // Request fresh location
    requestLocation()
  }, [])

  const value: LocationContextType = {
    userLocation,
    isLoading,
    error,
    accuracy,
    hasPermission,
    requestLocation,
    clearError,
  }

  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  )
}

export function useLocation(): LocationContextType {
  const context = useContext(LocationContext)
  if (context === undefined) {
    throw new Error('useLocation must be used within a LocationProvider')
  }
  return context
}

// Hook for getting user location with distance sorting
export function useLocationSorting() {
  const { userLocation } = useLocation()

  const sortByDistance = <T extends { location?: { lat: number; lng: number } }>(
    items: T[]
  ): T[] => {
    if (!userLocation) return items

    return items
      .map(item => ({
        ...item,
        distance: item.location ? calculateDistance(userLocation, item.location) : Infinity
      }))
      .sort((a, b) => (a as any).distance - (b as any).distance)
  }

  return { userLocation, sortByDistance }
}

// Helper function for distance calculation (moved here for convenience)
const calculateDistance = (loc1: Location, loc2: Location): number => {
  const R = 6371 // Earth's radius in kilometers
  const dLat = toRadians(loc2.lat - loc1.lat)
  const dLng = toRadians(loc2.lng - loc1.lng)

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(loc1.lat)) * Math.cos(toRadians(loc2.lat)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

const toRadians = (degrees: number): number => {
  return degrees * (Math.PI / 180)
}