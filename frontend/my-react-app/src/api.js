const API_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000/api`

export const getTokens = () => JSON.parse(localStorage.getItem('attendance_tokens') || 'null')
export const saveTokens = (tokens) => localStorage.setItem('attendance_tokens', JSON.stringify(tokens))
export const clearTokens = () => localStorage.removeItem('attendance_tokens')

async function request(path, options = {}, retry = true) {
  const tokens = getTokens()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (tokens?.access) headers.Authorization = `Bearer ${tokens.access}`
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 401 && retry && tokens?.refresh) {
    const refresh = await fetch(`${API_URL}/token/refresh/`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh: tokens.refresh }),
    })
    if (refresh.ok) {
      const next = await refresh.json()
      saveTokens({ ...tokens, access: next.access })
      return request(path, options, false)
    }
    clearTokens()
  }
  const data = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(Object.values(data).flat().join(' ') || 'Request failed')
  return data
}

export const api = {
  request,
  login: (username, password) => request('/token/', { method: 'POST', body: JSON.stringify({ username, password }) }, false),
  register: (payload) => request('/register/', { method: 'POST', body: JSON.stringify(payload) }, false),
  verifyRegistration: (payload) => request('/register/verify/', { method: 'POST', body: JSON.stringify(payload) }, false),
  account: () => request('/account/'),
  updateAccount: (payload) => request('/account/', { method: 'PATCH', body: JSON.stringify(payload) }),
  changePassword: (payload) => request('/account/password/', { method: 'POST', body: JSON.stringify(payload) }),
  courses: () => request('/courses/'),
  createCourse: (payload) => request('/courses/', { method: 'POST', body: JSON.stringify(payload) }),
  updateCourse: (id, payload) => request(`/courses/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteCourse: (id) => request(`/courses/${id}/`, { method: 'DELETE' }),
  timetable: (day = '') => request(`/timetables/${day ? `?day=${day}` : ''}`),
  createTimetable: (payload) => request('/timetables/', { method: 'POST', body: JSON.stringify(payload) }),
  deleteTimetable: (id) => request(`/timetables/${id}/`, { method: 'DELETE' }),
  attendance: (query = '') => request(`/attendances/${query ? `?${query}` : ''}`),
  createAttendance: (payload) => request('/attendances/', { method: 'POST', body: JSON.stringify(payload) }),
  updateAttendance: (id, payload) => request(`/attendances/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteAttendance: (id) => request(`/attendances/${id}/`, { method: 'DELETE' }),
  summary: () => request('/attendance-summary/'),
}
