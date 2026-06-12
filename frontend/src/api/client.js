const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API error ${res.status}: ${err}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Locations
  getLocations: () => request('/locations'),
  createLocation: (data) => request('/locations', { method: 'POST', body: JSON.stringify(data) }),
  deleteLocation: (id) => request(`/locations/${id}`, { method: 'DELETE' }),

  // Targets
  searchTargets: (params) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/targets?${qs}`)
  },
  getTarget: (id) => request(`/targets/${id}`),

  // Ephemeris
  getAltitudeCurve: (targetId, locationId, date) =>
    request(`/ephemeris/altitude-curve?target_id=${targetId}&location_id=${locationId}&date=${date}`),
  getTwilight: (locationId, date) =>
    request(`/ephemeris/twilight?location_id=${locationId}&date=${date}`),
  getMoon: (locationId, date) =>
    request(`/ephemeris/moon?location_id=${locationId}&date=${date}`),
  getPosition: (targetId, locationId) =>
    request(`/ephemeris/position?target_id=${targetId}&location_id=${locationId}`),
  getVisibleTargets: (locationId, datetimeUtc) => {
    let url = `/ephemeris/visible-targets?location_id=${locationId}`
    if (datetimeUtc) url += `&datetime_utc=${encodeURIComponent(datetimeUtc)}`
    return request(url)
  },

  // Planning
  getObservationWindow: (targetId, locationId, date) =>
    request(`/planning/observation-window?target_id=${targetId}&location_id=${locationId}&date=${date}`),
  getCalendar: (targetId, locationId, year, month) =>
    request(`/planning/calendar?target_id=${targetId}&location_id=${locationId}&year=${year}&month=${month}`),
  getTonight: (locationId, date) =>
    request(`/planning/tonight?location_id=${locationId}&date=${date}`),

  // Equipment
  getFov: (focalLength, sensorWidth, sensorHeight) =>
    request(`/equipment/fov?focal_length_mm=${focalLength}&sensor_width_mm=${sensorWidth}&sensor_height_mm=${sensorHeight}`),
  getProfiles: () => request('/equipment/profiles'),
  createProfile: (data) => request('/equipment/profiles', { method: 'POST', body: JSON.stringify(data) }),
}
