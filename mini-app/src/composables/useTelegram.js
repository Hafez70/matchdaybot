/**
 * Telegram WebApp Composable
 */
import { ref, computed, onMounted } from 'vue'
import { setTelegramInitData } from '../services/api'

export function useTelegram() {
  const webApp = ref(null)
  const user = ref(null)
  const initData = ref(null)
  const initDataRaw = ref(null) // Raw init data for server validation
  const leagueCode = ref(null)
  const isReady = ref(false)
  const isTelegram = ref(false) // Is running inside Telegram

  const userId = computed(() => user.value?.id || null)
  const userName = computed(() => user.value?.first_name || 'کاربر')
  const themeParams = computed(() => webApp.value?.themeParams || {})
  const colorScheme = computed(() => webApp.value?.colorScheme || 'dark')

  onMounted(() => {
    // Initialize Telegram WebApp
    // Check if we're REALLY inside Telegram (has initData with user)
    const telegramWebApp = window.Telegram?.WebApp
    const hasRealUser = telegramWebApp?.initDataUnsafe?.user?.id
    
    if (telegramWebApp && hasRealUser) {
      webApp.value = telegramWebApp
      isTelegram.value = true
      
      // Expand to full height
      webApp.value.expand()
      
      // Ready signal
      webApp.value.ready()
      
      // Get user info
      user.value = webApp.value.initDataUnsafe.user
      
      // Get init data (raw string for server auth)
      initDataRaw.value = webApp.value.initData
      initData.value = webApp.value.initDataUnsafe
      
      // Set init data in API service for authentication
      if (initDataRaw.value) {
        setTelegramInitData(initDataRaw.value)
        console.log('🔐 Auth: Init data sent to API service')
      }
      
      // Parse start_param for league code
      const startParam = webApp.value.initDataUnsafe?.start_param
      if (startParam) {
        leagueCode.value = startParam
      }
      
      // Also check URL params for development
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.has('league')) {
        leagueCode.value = urlParams.get('league')
      }
      
      isReady.value = true
      
      console.log('📱 Telegram WebApp initialized:', {
        user: user.value,
        leagueCode: leagueCode.value,
        colorScheme: colorScheme.value,
        hasInitData: !!initDataRaw.value
      })
    } else {
      // Development mode - mock data
      console.warn('⚠️ Telegram WebApp not available - using mock data')
      
      // Set isTelegram to true in dev mode so the app works normally
      isTelegram.value = true
      
      // Check URL for league param
      const urlParams = new URLSearchParams(window.location.search)
      const urlLeague = urlParams.get('league')
      if (urlLeague) {
        leagueCode.value = urlLeague
      }
      
      // Mock user for testing (matches DEV_USER_ID in config.env)
      user.value = {
        id: 93205092,
        first_name: 'Test User',
        last_name: 'Dev'
      }
      
      console.log('🧪 Dev mode user set:', user.value)
      
      // Note: In dev mode, we don't have real initData
      // API should have DEV_MODE=true to bypass auth
      
      isReady.value = true
    }
  })

  /**
   * Show main button
   */
  function showMainButton(text, callback) {
    if (webApp.value) {
      webApp.value.MainButton.text = text
      webApp.value.MainButton.onClick(callback)
      webApp.value.MainButton.show()
    }
  }

  /**
   * Hide main button
   */
  function hideMainButton() {
    if (webApp.value) {
      webApp.value.MainButton.hide()
    }
  }

  /**
   * Show back button
   */
  function showBackButton(callback) {
    if (webApp.value) {
      webApp.value.BackButton.onClick(callback)
      webApp.value.BackButton.show()
    }
  }

  /**
   * Hide back button
   */
  function hideBackButton() {
    if (webApp.value) {
      webApp.value.BackButton.hide()
    }
  }

  /**
   * Close WebApp
   */
  function close() {
    if (webApp.value) {
      webApp.value.close()
    }
  }

  /**
   * Show alert
   */
  function showAlert(message) {
    if (webApp.value) {
      webApp.value.showAlert(message)
    } else {
      alert(message)
    }
  }

  /**
   * Haptic feedback
   */
  function hapticFeedback(type = 'light') {
    if (webApp.value?.HapticFeedback) {
      switch (type) {
        case 'light':
          webApp.value.HapticFeedback.impactOccurred('light')
          break
        case 'medium':
          webApp.value.HapticFeedback.impactOccurred('medium')
          break
        case 'heavy':
          webApp.value.HapticFeedback.impactOccurred('heavy')
          break
        case 'success':
          webApp.value.HapticFeedback.notificationOccurred('success')
          break
        case 'error':
          webApp.value.HapticFeedback.notificationOccurred('error')
          break
      }
    }
  }

  /**
   * Open Telegram bot in Telegram app
   */
  function openTelegramBot() {
    const botUsername = import.meta.env.VITE_BOT_USERNAME || 'frontAssistantbot'
    window.location.href = `https://t.me/${botUsername}`
  }

  /**
   * Share URL via Telegram
   */
  function shareUrl(url, text = '') {
    if (webApp.value?.openTelegramLink) {
      const shareLink = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
      webApp.value.openTelegramLink(shareLink)
    } else {
      // Fallback for non-Telegram environment
      const shareLink = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
      window.open(shareLink, '_blank')
    }
  }

  return {
    webApp,
    user,
    userId,
    userName,
    initData,
    initDataRaw,
    leagueCode,
    isReady,
    isTelegram,
    themeParams,
    colorScheme,
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
    close,
    showAlert,
    hapticFeedback,
    openTelegramBot,
    shareUrl
  }
}

export default useTelegram

