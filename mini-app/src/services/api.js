/**
 * API Service for MatchDay Mini App
 */
import axios from 'axios'

// API Base URL - In production, this should be your deployed API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error(`❌ API Error: ${error.config?.url}`, error.message)
    return Promise.reject(error)
  }
)

export const api = {
  /**
   * Get user's leagues
   */
  async getUserLeagues(telegramId) {
    const response = await apiClient.get(`/api/user/${telegramId}/leagues`)
    return response.data
  },

  /**
   * Get league information
   */
  async getLeagueInfo(leagueCode) {
    const response = await apiClient.get(`/api/league/${leagueCode}`)
    return response.data
  },

  /**
   * Get league leaderboard
   */
  async getLeaderboard(leagueCode, userId = null) {
    const params = userId ? { user_id: userId } : {}
    const response = await apiClient.get(`/api/league/${leagueCode}/leaderboard`, { params })
    return response.data
  },

  /**
   * Get recent matches
   */
  async getMatches(leagueCode, limit = 20, offset = 0) {
    const response = await apiClient.get(`/api/league/${leagueCode}/matches`, {
      params: { limit, offset }
    })
    return response.data
  },

  /**
   * Get league members
   */
  async getMembers(leagueCode) {
    const response = await apiClient.get(`/api/league/${leagueCode}/members`)
    return response.data
  },

  /**
   * Get player stats
   */
  async getPlayerStats(leagueCode, telegramId) {
    const response = await apiClient.get(`/api/league/${leagueCode}/player/${telegramId}`)
    return response.data
  }
}

export default api

