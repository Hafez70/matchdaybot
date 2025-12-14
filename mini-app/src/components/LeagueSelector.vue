<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const emit = defineEmits(['select-league'])

const { userId, userName, hapticFeedback, isTelegram, initDataRaw, openTelegramBot } = useTelegram()

const leagues = ref([])
const loading = ref(true)
const error = ref(null)
const notInTelegram = ref(false)
const realUserName = ref(null) // Real user name from database

// Bot username for redirect link
const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || 'frontAssistantbot'

// Display name: use real name from DB if available, otherwise use Telegram name
const displayName = () => realUserName.value || userName.value

const fetchUserInfo = async () => {
  if (!userId.value) return
  try {
    const userInfo = await api.getUserInfo(userId.value)
    realUserName.value = userInfo.name
    console.log('✅ Real user name:', realUserName.value)
  } catch (err) {
    console.error('Failed to fetch user info:', err)
    // Fall back to Telegram name
  }
}

const fetchLeagues = async () => {
  // Check if opened from Telegram (in production)
  // In dev mode, we allow mock user
  const isDevMode = import.meta.env.DEV
  
  if (!isTelegram.value && !isDevMode) {
    notInTelegram.value = true
    loading.value = false
    return
  }
  
  if (!userId.value) {
    error.value = 'کاربر شناسایی نشد'
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    // Fetch user info to get real name
    await fetchUserInfo()
    
    // Use secure endpoint if we have initData (running in Telegram)
    if (initDataRaw.value) {
      console.log('🔐 Using secure API with Telegram auth')
      leagues.value = await api.getMyLeagues()
    } else {
      // Fallback for development - use legacy endpoint
      console.log('⚠️ Using legacy API (dev mode)')
      leagues.value = await api.getUserLeagues(userId.value)
    }
  } catch (err) {
    if (err.response?.status === 401) {
      error.value = 'احراز هویت ناموفق. لطفاً دوباره از تلگرام وارد شوید.'
    } else if (err.response?.status === 404) {
      error.value = 'کاربر پیدا نشد. لطفاً اول در ربات ثبت‌نام کنید.'
    } else {
      error.value = 'خطا در دریافت لیگ‌ها'
    }
    console.error('Leagues fetch error:', err)
  } finally {
    loading.value = false
  }
}

const selectLeague = (league) => {
  hapticFeedback('light')
  emit('select-league', league)
}

const goToTelegram = () => {
  openTelegramBot()
}

onMounted(() => {
  fetchLeagues()
})
</script>

<template>
  <div class="league-selector">
    <!-- Header -->
    <div class="selector-header">
      <div class="app-logo">🎮</div>
      <h1 class="app-title">MatchDay</h1>
      <p class="welcome-text">
        سلام {{ displayName() }}! 👋
      </p>
    </div>

    <!-- Not in Telegram -->
    <div v-if="notInTelegram" class="not-telegram-state">
      <div class="telegram-icon">
        <svg viewBox="0 0 24 24" width="80" height="80" fill="#8b5cf6">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .37z"/>
        </svg>
      </div>
      <h2>دسترسی از طریق تلگرام</h2>
      <p class="not-telegram-text">
        برای استفاده از این اپلیکیشن، لطفاً از طریق ربات تلگرام وارد شوید.
      </p>
      <button class="telegram-btn" @click="goToTelegram">
        <span class="btn-icon">📱</span>
        باز کردن در تلگرام
      </button>
      <p class="bot-info">
        @{{ BOT_USERNAME }}
      </p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>در حال دریافت لیگ‌ها...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchLeagues">
        تلاش مجدد
      </button>
    </div>

    <!-- No Leagues -->
    <div v-else-if="leagues.length === 0" class="empty-state">
      <div class="empty-icon">🏆</div>
      <h3>هنوز عضو هیچ لیگی نیستید</h3>
      <p class="empty-text">
        از طریق ربات تلگرام یک لیگ بسازید یا به لیگی بپیوندید
      </p>
    </div>

    <!-- League List -->
    <div v-else class="leagues-list">
      <h2 class="section-title">🏆 لیگ‌های من</h2>
      
      <div 
        v-for="league in leagues" 
        :key="league.code"
        class="league-card"
        @click="selectLeague(league)"
      >
        <div class="league-card-header">
          <span class="league-icon">{{ league.is_owner ? '👑' : '🏆' }}</span>
          <span class="league-name">{{ league.name }}</span>
        </div>
        
        <div class="league-card-stats">
          <div class="stat">
            <span class="stat-value">{{ league.member_count }}</span>
            <span class="stat-label">عضو</span>
          </div>
          <div class="stat">
            <span class="stat-value" :class="{ 
              positive: league.my_points > 0, 
              negative: league.my_points < 0 
            }">
              {{ league.my_points > 0 ? '+' : '' }}{{ league.my_points }}
            </span>
            <span class="stat-label">امتیاز</span>
          </div>
          <div class="stat">
            <span class="stat-value">#{{ league.my_rank }}</span>
            <span class="stat-label">رتبه</span>
          </div>
        </div>
        
        <div class="league-card-arrow">→</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.league-selector {
  min-height: 100vh;
  padding: 20px;
}

.selector-header {
  text-align: center;
  margin-bottom: 30px;
  padding-top: 20px;
}

.app-logo {
  font-size: 64px;
  margin-bottom: 10px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.app-title {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #a855f7, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.welcome-text {
  color: var(--text-secondary);
  font-size: 16px;
}

.loading-state,
.error-state,
.empty-state,
.not-telegram-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  text-align: center;
}

.not-telegram-state {
  padding: 40px 20px;
}

.telegram-icon {
  margin-bottom: 20px;
  opacity: 0.9;
}

.not-telegram-state h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.not-telegram-text {
  color: var(--text-secondary);
  margin-bottom: 24px;
  max-width: 300px;
  line-height: 1.6;
}

.telegram-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
  text-decoration: none;
  padding: 14px 32px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
}

.telegram-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(139, 92, 246, 0.5);
}

.telegram-btn:active {
  transform: scale(0.98);
}

.btn-icon {
  font-size: 20px;
}

.bot-info {
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 14px;
}

.error-icon,
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.error-message,
.empty-text {
  color: var(--text-secondary);
  margin-bottom: 20px;
  max-width: 280px;
}

.retry-btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  transform: scale(1.05);
}

.section-title {
  font-size: 18px;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.leagues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.league-card {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.league-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  opacity: 0;
  transition: opacity 0.2s;
}

.league-card:hover::before,
.league-card:active::before {
  opacity: 1;
}

.league-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(168, 85, 247, 0.2);
}

.league-card:active {
  transform: scale(0.98);
}

.league-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.league-icon {
  font-size: 24px;
}

.league-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.league-card-stats {
  display: flex;
  justify-content: space-around;
  padding: 12px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.positive {
  color: var(--success);
}

.stat-value.negative {
  color: var(--error);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.league-card-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  color: var(--text-secondary);
  opacity: 0.5;
  transition: all 0.2s;
}

.league-card:hover .league-card-arrow {
  opacity: 1;
  transform: translateY(-50%) translateX(4px);
  color: var(--primary);
}
</style>

