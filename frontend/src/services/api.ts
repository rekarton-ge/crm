import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Перехватчик для добавления токена к каждому запросу
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Перехватчик для обработки ответов
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Обработка случая, когда токен просрочен
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Здесь будет логика обновления токена
        // const refreshToken = localStorage.getItem('refresh_token')
        // const response = await axios.post('/token/refresh/', { refresh: refreshToken })
        // localStorage.setItem('access_token', response.data.access)

        return apiClient(originalRequest)
      } catch (refreshError) {
        // Выход из системы если не удалось обновить токен
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)