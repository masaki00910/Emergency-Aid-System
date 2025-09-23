// Geocoding utility functions for user location and distance calculations

export interface Location {
  lat: number;
  lng: number;
}

export interface GeolocationResult {
  location: Location;
  accuracy: number;
  address?: string;
}

/**
 * Get user's current location using browser geolocation API
 */
export const getUserLocation = (): Promise<GeolocationResult> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          location: {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          },
          accuracy: position.coords.accuracy,
        });
      },
      (error) => {
        let message = 'Unknown geolocation error';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message = 'User denied the request for Geolocation';
            break;
          case error.POSITION_UNAVAILABLE:
            message = 'Location information is unavailable';
            break;
          case error.TIMEOUT:
            message = 'The request to get user location timed out';
            break;
        }
        reject(new Error(message));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    );
  });
};

/**
 * Calculate distance between two locations using Haversine formula
 * @param loc1 First location
 * @param loc2 Second location
 * @returns Distance in kilometers
 */
export const calculateDistance = (loc1: Location, loc2: Location): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRadians(loc2.lat - loc1.lat);
  const dLng = toRadians(loc2.lng - loc1.lng);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(loc1.lat)) * Math.cos(toRadians(loc2.lat)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;

  return Math.round(distance * 100) / 100; // Round to 2 decimal places
};

/**
 * Convert degrees to radians
 */
const toRadians = (degrees: number): number => {
  return degrees * (Math.PI / 180);
};

/**
 * Sort items by distance from user location
 */
export const sortByDistance = <T extends { location?: { lat: number; lng: number } }>(
  items: T[],
  userLocation: Location
): T[] => {
  return items
    .map(item => ({
      ...item,
      distance: item.location ? calculateDistance(userLocation, item.location) : Infinity
    }))
    .sort((a, b) => a.distance - b.distance);
};

/**
 * Get reverse geocoding (address from coordinates) using Google Geocoding API
 * Note: Requires Google Maps API key to be configured
 */
export const reverseGeocode = async (location: Location): Promise<string | null> => {
  // For now, return a simple format. In production, you would use Google Geocoding API
  // Example: https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${API_KEY}

  try {
    // Fallback to approximate address format for Japan
    const { lat, lng } = location;
    return `緯度: ${lat.toFixed(4)}, 経度: ${lng.toFixed(4)}`;
  } catch (error) {
    console.error('Reverse geocoding failed:', error);
    return null;
  }
};

/**
 * Default location for Japan (Tokyo) if geolocation fails
 */
export const DEFAULT_LOCATION: Location = {
  lat: 35.6762,
  lng: 139.6503, // Tokyo coordinates
};

/**
 * Check if a location is valid
 */
export const isValidLocation = (location: any): location is Location => {
  return (
    location &&
    typeof location.lat === 'number' &&
    typeof location.lng === 'number' &&
    !isNaN(location.lat) &&
    !isNaN(location.lng) &&
    location.lat >= -90 &&
    location.lat <= 90 &&
    location.lng >= -180 &&
    location.lng <= 180
  );
};

/**
 * Format distance for display
 */
export const formatDistance = (distance: number): string => {
  if (distance < 1) {
    return `${Math.round(distance * 1000)}m`;
  } else if (distance < 10) {
    return `${distance.toFixed(1)}km`;
  } else {
    return `${Math.round(distance)}km`;
  }
};