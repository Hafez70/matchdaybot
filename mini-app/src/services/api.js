/**
 * API Service for MatchDay Mini App
 * With Telegram Auth support
 */
import axios from 'axios'

// API Base URL - In production, this should be your deployed API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.matchdayfc.ir'

// Store initData for auth
let telegramInitData = null

/**
 * Set Telegram init data for authentication
 * @param {string} initData - Raw init data from Telegram WebApp
 */
export function setTelegramInitData(initData) {
  telegramInitData = initData
  console.log('🔐 Auth: Telegram init data set')
  console.log('🔐 Auth: initData length:', initData?.length || 0)
  console.log('🔐 Auth: initData preview:', initData?.substring(0, 100) || 'null')
}

/**
 * Get stored init data
 */
export function getTelegramInitData() {
  return telegramInitData
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add auth headers
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    console.log(`🔑 telegramInitData available: ${!!telegramInitData}`)
    
    // Add Telegram auth headers if available
    if (telegramInitData) {
      // Standard Authorization header
      config.headers.Authorization = `tma ${telegramInitData}`
      // Custom header for Apache proxy (Authorization gets stripped)
      config.headers['X-Telegram-Init-Data'] = telegramInitData
      console.log(`🔑 Auth headers set (length: ${telegramInitData.length})`)
    } else {
      console.warn(`⚠️ No telegramInitData available for auth!`)
    }
    
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
    
    // Handle auth errors
    if (error.response?.status === 401) {
      console.error('🔒 Authentication failed:', error.response.data?.detail)
    }
    
    return Promise.reject(error)
  }
)

export const api = {
  /**
   * Get current authenticated user
   */
  async getMe() {
    const response = await apiClient.get('/api/me')
    return response.data
  },

  /**
   * Get user info by telegram ID
   */
  async getUserInfo(telegramId) {
    const response = await apiClient.get(`/api/user/${telegramId}`)
    return response.data
  },

  /**
   * Get authenticated user's leagues (secure)
   */
  async getMyLeagues() {
    const response = await apiClient.get('/api/me/leagues')
    return response.data
  },

  /**
   * Get user's leagues (legacy - by telegram id)
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
