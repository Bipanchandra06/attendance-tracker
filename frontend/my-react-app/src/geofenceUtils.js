/**
 * Device fingerprinting utility for lightweight device tracking.
 * Generates a device ID based on browser metadata.
 */
export function generateDeviceFingerprint() {
  const navigator = window.navigator
  const screen = window.screen
  
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    !!window.sessionStorage,
    !!window.localStorage,
  ]
  
  // Simple hash function (not cryptographic, just for generating unique ID)
  const str = components.join('|')
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  
  return Math.abs(hash).toString(36)
}

/**
 * Request geolocation from the browser.
 * @returns {Promise} Resolves with {latitude, longitude} or rejects
 */
export function getGeolocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser.'))
      return
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: Number(position.coords.latitude.toFixed(6)),
          longitude: Number(position.coords.longitude.toFixed(6)),
        })
      },
      (error) => {
        let message = 'Geolocation permission denied.'
        if (error.code === 1) message = 'Permission denied. Please enable location access in your browser settings.'
        else if (error.code === 2) message = 'Location unavailable. Check your internet connection.'
        else if (error.code === 3) message = 'Location request timed out.'
        reject(new Error(message))
      },
      { timeout: 20000, enableHighAccuracy: true, maximumAge: 0 }
    )
  })
}

/**
 * Request geolocation with a timeout and accuracy requirement.
 * @param {number} timeout Timeout in milliseconds
 * @returns {Promise}
 */
export function getGeolocationWithHighAccuracy(timeout = 15000) {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser.'))
      return
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: Number(position.coords.latitude.toFixed(6)),
          longitude: Number(position.coords.longitude.toFixed(6)),
          accuracy: position.coords.accuracy,
        })
      },
      (error) => {
        let message = 'Geolocation permission denied.'
        if (error.code === 1) message = 'Permission denied. Please enable location access in your browser settings.'
        else if (error.code === 2) message = 'Location unavailable. Check your internet connection.'
        else if (error.code === 3) message = 'Location request timed out.'
        reject(new Error(message))
      },
      { timeout, enableHighAccuracy: true }
    )
  })
}

/**
 * Calculate distance between two coordinates using haversine formula.
 * Returns distance in meters.
 */
export function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371000 // Earth radius in meters
  
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}
