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
 * Get approximate location name based on coordinates for Japan
 * Returns prefecture and city/ward name
 */
export const reverseGeocode = async (location: Location): Promise<string | null> => {
  try {
    const { lat, lng } = location;
    
    // Major Japanese cities and regions with approximate coordinates
    const locations = [
      { name: '北海道札幌市', lat: 43.0642, lng: 141.3469, range: 0.5 },
      { name: '北海道函館市', lat: 41.7688, lng: 140.7290, range: 0.3 },
      { name: '北海道旭川市', lat: 43.7708, lng: 142.3650, range: 0.3 },
      { name: '青森県青森市', lat: 40.8244, lng: 140.7400, range: 0.3 },
      { name: '青森県八戸市', lat: 40.5124, lng: 141.4885, range: 0.3 },
      { name: '青森県田子町', lat: 40.3417, lng: 141.1467, range: 0.1 },
      { name: '岩手県盛岡市', lat: 39.7036, lng: 141.1527, range: 0.3 },
      { name: '宮城県仙台市', lat: 38.2682, lng: 140.8694, range: 0.3 },
      { name: '秋田県秋田市', lat: 39.7186, lng: 140.1024, range: 0.3 },
      { name: '山形県山形市', lat: 38.2406, lng: 140.3636, range: 0.3 },
      { name: '福島県福島市', lat: 37.7608, lng: 140.4748, range: 0.3 },
      { name: '茨城県水戸市', lat: 36.3418, lng: 140.4468, range: 0.3 },
      { name: '栃木県宇都宮市', lat: 36.5657, lng: 139.8836, range: 0.3 },
      { name: '群馬県前橋市', lat: 36.3906, lng: 139.0604, range: 0.3 },
      { name: '埼玉県さいたま市', lat: 35.8617, lng: 139.6455, range: 0.3 },
      { name: '千葉県千葉市', lat: 35.6074, lng: 140.1065, range: 0.3 },
      { name: '東京都千代田区', lat: 35.6938, lng: 139.7534, range: 0.1 },
      { name: '東京都新宿区', lat: 35.6938, lng: 139.7036, range: 0.1 },
      { name: '東京都渋谷区', lat: 35.6640, lng: 139.6982, range: 0.1 },
      { name: '東京都港区', lat: 35.6585, lng: 139.7514, range: 0.1 },
      { name: '東京都世田谷区', lat: 35.6464, lng: 139.6530, range: 0.1 },
      { name: '東京都練馬区', lat: 35.7358, lng: 139.6516, range: 0.1 },
      { name: '東京都八王子市', lat: 35.6666, lng: 139.3160, range: 0.2 },
      { name: '神奈川県横浜市', lat: 35.4437, lng: 139.6380, range: 0.3 },
      { name: '神奈川県川崎市', lat: 35.5308, lng: 139.7029, range: 0.2 },
      { name: '新潟県新潟市', lat: 37.9161, lng: 139.0364, range: 0.3 },
      { name: '富山県富山市', lat: 36.6953, lng: 137.2113, range: 0.3 },
      { name: '石川県金沢市', lat: 36.5946, lng: 136.6256, range: 0.3 },
      { name: '福井県福井市', lat: 36.0652, lng: 136.2219, range: 0.3 },
      { name: '山梨県甲府市', lat: 35.6640, lng: 138.5684, range: 0.3 },
      { name: '長野県長野市', lat: 36.6513, lng: 138.1810, range: 0.3 },
      { name: '岐阜県岐阜市', lat: 35.3912, lng: 136.7223, range: 0.3 },
      { name: '静岡県静岡市', lat: 34.9756, lng: 138.3828, range: 0.3 },
      { name: '愛知県名古屋市', lat: 35.1802, lng: 136.9065, range: 0.3 },
      { name: '三重県津市', lat: 34.7303, lng: 136.5086, range: 0.3 },
      { name: '滋賀県大津市', lat: 35.0045, lng: 135.8686, range: 0.3 },
      { name: '京都府京都市', lat: 35.0116, lng: 135.7681, range: 0.3 },
      { name: '大阪府大阪市', lat: 34.6937, lng: 135.5023, range: 0.3 },
      { name: '兵庫県神戸市', lat: 34.6901, lng: 135.1955, range: 0.3 },
      { name: '奈良県奈良市', lat: 34.6851, lng: 135.8329, range: 0.3 },
      { name: '和歌山県和歌山市', lat: 34.2260, lng: 135.1675, range: 0.3 },
      { name: '鳥取県鳥取市', lat: 35.5039, lng: 134.2383, range: 0.3 },
      { name: '島根県松江市', lat: 35.4723, lng: 133.0505, range: 0.3 },
      { name: '岡山県岡山市', lat: 34.6617, lng: 133.9350, range: 0.3 },
      { name: '広島県広島市', lat: 34.3966, lng: 132.4596, range: 0.3 },
      { name: '山口県山口市', lat: 34.1785, lng: 131.4737, range: 0.3 },
      { name: '徳島県徳島市', lat: 34.0658, lng: 134.5593, range: 0.3 },
      { name: '香川県高松市', lat: 34.3401, lng: 134.0434, range: 0.3 },
      { name: '愛媛県松山市', lat: 33.8416, lng: 132.7657, range: 0.3 },
      { name: '高知県高知市', lat: 33.5597, lng: 133.5311, range: 0.3 },
      { name: '福岡県福岡市', lat: 33.5904, lng: 130.4017, range: 0.3 },
      { name: '福岡県北九州市', lat: 33.8835, lng: 130.8752, range: 0.3 },
      { name: '佐賀県佐賀市', lat: 33.2495, lng: 130.2988, range: 0.3 },
      { name: '長崎県長崎市', lat: 32.7448, lng: 129.8737, range: 0.3 },
      { name: '熊本県熊本市', lat: 32.7898, lng: 130.7417, range: 0.3 },
      { name: '大分県大分市', lat: 33.2382, lng: 131.6126, range: 0.3 },
      { name: '宮崎県宮崎市', lat: 31.9109, lng: 131.4239, range: 0.3 },
      { name: '鹿児島県鹿児島市', lat: 31.5966, lng: 130.5571, range: 0.3 },
      { name: '沖縄県那覇市', lat: 26.2124, lng: 127.6809, range: 0.3 },
    ];
    
    // Find the closest matching location
    let closestLocation = null;
    let minDistance = Infinity;
    
    for (const loc of locations) {
      const distance = Math.sqrt(
        Math.pow(lat - loc.lat, 2) + Math.pow(lng - loc.lng, 2)
      );
      
      if (distance < minDistance && distance <= loc.range) {
        minDistance = distance;
        closestLocation = loc.name;
      }
    }
    
    // If we found a close match, return it
    if (closestLocation) {
      return closestLocation;
    }
    
    // Otherwise, try to determine the general region based on rough boundaries
    if (lat >= 41.3 && lat <= 45.6 && lng >= 139.5 && lng <= 145.8) {
      return '北海道';
    } else if (lat >= 39.5 && lat <= 41.3 && lng >= 139.5 && lng <= 142) {
      return '青森県';
    } else if (lat >= 38.8 && lat <= 40.5 && lng >= 140.5 && lng <= 142) {
      return '岩手県';
    } else if (lat >= 37.8 && lat <= 39.0 && lng >= 140.2 && lng <= 141.7) {
      return '宮城県';
    } else if (lat >= 38.8 && lat <= 40.5 && lng >= 139.5 && lng <= 140.8) {
      return '秋田県';
    } else if (lat >= 37.8 && lat <= 39.0 && lng >= 139.5 && lng <= 140.5) {
      return '山形県';
    } else if (lat >= 37.0 && lat <= 37.8 && lng >= 139.2 && lng <= 141.0) {
      return '福島県';
    } else if (lat >= 35.8 && lat <= 36.9 && lng >= 140.0 && lng <= 140.9) {
      return '茨城県';
    } else if (lat >= 36.2 && lat <= 37.1 && lng >= 139.3 && lng <= 140.3) {
      return '栃木県';
    } else if (lat >= 35.9 && lat <= 36.9 && lng >= 138.4 && lng <= 139.9) {
      return '群馬県';
    } else if (lat >= 35.5 && lat <= 36.3 && lng >= 138.7 && lng <= 140.0) {
      return '埼玉県';
    } else if (lat >= 35.0 && lat <= 36.1 && lng >= 139.7 && lng <= 140.9) {
      return '千葉県';
    } else if (lat >= 35.5 && lat <= 35.9 && lng >= 139.0 && lng <= 139.9) {
      return '東京都';
    } else if (lat >= 35.1 && lat <= 35.7 && lng >= 138.9 && lng <= 139.8) {
      return '神奈川県';
    } else if (lat >= 34.0 && lat <= 36.0 && lng >= 136.0 && lng <= 138.0) {
      return '中部地方';
    } else if (lat >= 33.0 && lat <= 36.0 && lng >= 133.0 && lng <= 137.0) {
      return '近畿地方';
    } else if (lat >= 33.0 && lat <= 36.0 && lng >= 130.0 && lng <= 134.0) {
      return '中国地方';
    } else if (lat >= 33.0 && lat <= 34.5 && lng >= 132.0 && lng <= 135.0) {
      return '四国地方';
    } else if (lat >= 31.0 && lat <= 34.0 && lng >= 129.0 && lng <= 132.0) {
      return '九州地方';
    } else if (lat >= 24.0 && lat <= 28.0 && lng >= 122.0 && lng <= 130.0) {
      return '沖縄県';
    }
    
    // Fallback to showing coordinates if no match found
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