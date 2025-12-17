<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from './services/api'
import { useTelegram } from './composables/useTelegram'
import LeaderboardView from './components/LeaderboardView.vue'
import MatchesView from './components/MatchesView.vue'
import MembersView from './components/MembersView.vue'
import PlayerStatsView from './components/PlayerStatsView.vue'

const { isReady, userName, userId, hapticFeedback, isTelegram, initDataRaw, openTelegramBot, shareUrl } = useTelegram()

// App state
const currentView = ref('leagues') // 'leagues' | 'detail' | 'leaderboard' | 'members' | 'stats' | 'matches'
const selectedLeague = ref(null)
const leagues = ref([])
const loading = ref(true)
const error = ref(null)
const notInTelegram = ref(false)
const realUserName = ref(null)
const copySuccess = ref(false)

// Bot username for links
const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || 'frontAssistantbot'

// Display name
const displayName = computed(() => realUserName.value || userName.value || 'کاربر')

// Join link for selected league
const joinLink = computed(() => {
  if (!selectedLeague.value) return ''
  return `https://t.me/${BOT_USERNAME}?start=join_${selectedLeague.value.code}`
})

// Menu items for league detail
const menuItems = [
  { id: 'leaderboard', icon: '🏅', label: 'جدول لیگ' },
  { id: 'members', icon: '👥', label: 'اعضای لیگ' },
  { id: 'stats', icon: '📊', label: 'آمار من' },
  { id: 'matches', icon: '⚽', label: 'مسابقات اخیر' }
]

const fetchUserInfo = async () => {
  if (!userId.value) return
  try {
    const userInfo = await api.getUserInfo(userId.value)
    realUserName.value = userInfo.name
  } catch (err) {
    console.error('Failed to fetch user info:', err)
  }
}

const fetchLeagues = async () => {
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
    await fetchUserInfo()
    
    if (initDataRaw.value) {
      leagues.value = await api.getMyLeagues()
    } else {
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
  selectedLeague.value = league
  currentView.value = 'detail'
}

const openView = (viewId) => {
  hapticFeedback('light')
  currentView.value = viewId
}

const goBack = () => {
  hapticFeedback('light')
  if (currentView.value === 'detail') {
    currentView.value = 'leagues'
    selectedLeague.value = null
  } else {
    currentView.value = 'detail'
  }
}

const goToTelegram = () => {
  openTelegramBot()
}

const retry = () => {
  fetchLeagues()
}

const copyCode = async () => {
  if (!selectedLeague.value) return
  try {
    await navigator.clipboard.writeText(selectedLeague.value.code)
    hapticFeedback('success')
    copySuccess.value = true
    setTimeout(() => copySuccess.value = false, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(joinLink.value)
    hapticFeedback('success')
    copySuccess.value = true
    setTimeout(() => copySuccess.value = false, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}

const shareLeague = () => {
  hapticFeedback('light')
  const text = `🏆 به لیگ "${selectedLeague.value.name}" بپیوندید!\n\nکد عضویت: ${selectedLeague.value.code}`
  shareUrl(joinLink.value, text)
}

onMounted(() => {
  if (isReady.value) {
    fetchLeagues()
  }
})

watch(isReady, (ready) => {
  if (ready) {
    fetchLeagues()
  }
})
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <button v-if="currentView !== 'leagues'" class="back-btn" @click="goBack">
          ←
        </button>
        <div v-else class="logo">🎮</div>
      </div>
      <div class="header-center">
        <h1 class="app-title">MatchDay</h1>
      </div>
      <div class="header-right">
        <div class="user-badge" v-if="!loading && !error && !notInTelegram">
          <span class="user-name">{{ displayName }}</span>
          <span class="user-icon">👤</span>
        </div>
      </div>
    </header>

    <!-- Not in Telegram -->
    <div v-if="notInTelegram" class="state-container">
      <div class="telegram-icon">
        <svg viewBox="0 0 24 24" width="80" height="80" fill="#8b5cf6">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .37z"/>
        </svg>
      </div>
      <h2>دسترسی از طریق تلگرام</h2>
      <p class="state-text">برای استفاده از این اپلیکیشن، لطفاً از طریق ربات تلگرام وارد شوید.</p>
      <button class="primary-btn" @click="goToTelegram">
        <span>📱</span> باز کردن در تلگرام
      </button>
      <p class="bot-info">@{{ BOT_USERNAME }}</p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="state-container">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="state-container">
      <div class="state-icon">😕</div>
      <p class="state-text">{{ error }}</p>
      <button class="primary-btn" @click="retry">تلاش مجدد</button>
    </div>

    <!-- No Leagues -->
    <div v-else-if="leagues.length === 0" class="state-container">
      <div class="state-icon">🏆</div>
      <h3>هنوز عضو هیچ لیگی نیستید</h3>
      <p class="state-text">از طریق ربات تلگرام یک لیگ بسازید یا به لیگی بپیوندید</p>
      <button class="primary-btn" @click="goToTelegram">
        <span>🤖</span> رفتن به ربات
      </button>
    </div>

    <!-- Main Content -->
    <main v-else class="main-content">
      <!-- Leagues List View -->
      <template v-if="currentView === 'leagues'">
        <div class="section-header">
          <h2 class="section-title">لیگ‌های من</h2>
          <span class="league-count">{{ leagues.length }} لیگ</span>
        </div>
        
        <div class="leagues-list">
          <div 
            v-for="league in leagues" 
            :key="league.code"
            class="league-card"
            @click="selectLeague(league)"
          >
            <div class="league-card-header">
              <span class="league-icon">{{ league.is_owner ? '👑' : '🏆' }}</span>
              <span class="league-name">{{ league.name }}</span>
              <span class="league-members">{{ league.member_count }} 👥</span>
            </div>
            <div class="league-card-divider"></div>
            <div class="league-card-stats">
              <div class="card-stat">
                <span class="card-stat-label">امتیاز</span>
                <span class="card-stat-value" :class="{ positive: league.my_points > 0, negative: league.my_points < 0 }">
                  {{ league.my_points > 0 ? '+' : '' }}{{ league.my_points }}
                </span>
              </div>
              <div class="card-stat">
                <span class="card-stat-label">رتبه</span>
                <span class="card-stat-value rank">#{{ league.my_rank || '-' }}</span>
              </div>
            </div>
            <div class="card-arrow">←</div>
          </div>
        </div>
      </template>

      <!-- League Detail View -->
      <template v-else-if="currentView === 'detail'">
        <div class="detail-header">
          <div class="detail-icon">{{ selectedLeague?.is_owner ? '👑' : '🏆' }}</div>
          <h2 class="detail-title">{{ selectedLeague?.name }}</h2>
          <p class="detail-meta">{{ selectedLeague?.member_count }} عضو</p>
        </div>

        <!-- My Stats -->
        <div class="my-stats-card">
          <div class="my-stat">
            <span class="my-stat-value" :class="{ positive: selectedLeague?.my_points > 0, negative: selectedLeague?.my_points < 0 }">
              {{ selectedLeague?.my_points > 0 ? '+' : '' }}{{ selectedLeague?.my_points }}
            </span>
            <span class="my-stat-label">امتیاز من</span>
          </div>
          <div class="stat-divider"></div>
          <div class="my-stat">
            <span class="my-stat-value">#{{ selectedLeague?.my_rank || '-' }}</span>
            <span class="my-stat-label">رتبه من</span>
          </div>
        </div>

        <!-- Menu Buttons -->
        <div class="menu-grid">
          <button 
            v-for="item in menuItems" 
            :key="item.id"
            class="menu-btn"
            @click="openView(item.id)"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span class="menu-label">{{ item.label }}</span>
          </button>
        </div>

        <!-- Share Section -->
        <div class="share-section">
          <h3 class="share-title">دعوت از دوستان</h3>
          
          <div class="share-code-box">
            <div class="code-label">کد عضویت:</div>
            <div class="code-value">{{ selectedLeague?.code }}</div>
            <button class="copy-btn" @click="copyCode">
              {{ copySuccess ? '✓' : '📋' }}
            </button>
          </div>

          <div class="share-buttons">
            <button class="share-btn link-btn" @click="copyLink">
              <span>🔗</span> کپی لینک
            </button>
            <button class="share-btn telegram-btn" @click="shareLeague">
              <span>📤</span> اشتراک‌گذاری
            </button>
          </div>
        </div>
      </template>

      <!-- Detail Sub-Views -->
      <template v-else>
        <div class="view-header">
          <h2 class="view-title">
            {{ menuItems.find(m => m.id === currentView)?.icon }}
            {{ menuItems.find(m => m.id === currentView)?.label }}
          </h2>
          <p class="view-subtitle">{{ selectedLeague?.name }}</p>
        </div>
        
        <LeaderboardView 
          v-if="currentView === 'leaderboard'" 
          :league-code="selectedLeague?.code" 
        />
        <MembersView 
          v-if="currentView === 'members'" 
          :league-code="selectedLeague?.code" 
        />
        <PlayerStatsView 
          v-if="currentView === 'stats'" 
          :league-code="selectedLeague?.code" 
        />
        <MatchesView 
          v-if="currentView === 'matches'" 
          :league-code="selectedLeague?.code" 
        />
      </template>
    </main>

    <!-- Copy Toast -->
    <div v-if="copySuccess" class="toast">
      ✓ کپی شد!
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left, .header-right {
  width: 80px;
}

.header-center {
  flex: 1;
  text-align: center;
}

.logo {
  font-size: 28px;
}

.back-btn {
  background: var(--bg-secondary);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #a855f7, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-secondary);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.user-name {
  color: var(--text-secondary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-icon {
  font-size: 14px;
}

/* State containers */
.state-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  gap: 16px;
}

.state-icon {
  font-size: 64px;
}

.state-text {
  color: var(--text-secondary);
  max-width: 280px;
  line-height: 1.6;
}

.telegram-icon {
  margin-bottom: 10px;
}

.bot-info {
  color: var(--text-muted);
  font-size: 14px;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
  border: none;
  padding: 14px 28px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn:active {
  transform: scale(0.98);
}

/* Main content */
.main-content {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Section Header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.league-count {
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 12px;
}

/* Leagues List */
.leagues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.league-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.league-card:hover {
  border-color: var(--primary);
  transform: translateX(-4px);
}

.league-card:active {
  transform: scale(0.98);
}

.league-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.league-icon {
  font-size: 24px;
}

.league-name {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.league-members {
  font-size: 13px;
  color: var(--text-secondary);
}

.league-card-divider {
  height: 1px;
  background: var(--border);
  margin: 12px 0;
}

.league-card-stats {
  display: flex;
  gap: 24px;
}

.card-stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.card-stat-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.card-stat-value.positive {
  color: var(--success);
}

.card-stat-value.negative {
  color: var(--error);
}

.card-stat-value.rank {
  color: var(--primary);
}

.card-arrow {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: var(--text-muted);
}

/* Detail Header */
.detail-header {
  text-align: center;
  padding: 16px 0;
}

.detail-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.detail-meta {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* My Stats Card */
.my-stats-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  background: var(--card-bg);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--border);
}

.my-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.my-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.my-stat-value.positive {
  color: var(--success);
}

.my-stat-value.negative {
  color: var(--error);
}

.my-stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-divider {
  width: 1px;
  height: 50px;
  background: var(--border);
}

/* Menu Grid */
.menu-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.menu-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  padding: 16px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 500;
}

.menu-btn:hover {
  border-color: var(--primary);
  background: rgba(139, 92, 246, 0.1);
}

.menu-btn:active {
  transform: scale(0.98);
}

.menu-icon {
  font-size: 22px;
}

.menu-label {
  flex: 1;
  text-align: right;
}

/* Share Section */
.share-section {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid var(--border);
}

.share-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-primary);
}

.share-code-box {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-secondary);
  padding: 12px 14px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.code-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.code-value {
  flex: 1;
  font-size: 18px;
  font-weight: 700;
  font-family: monospace;
  color: var(--primary);
  letter-spacing: 2px;
}

.copy-btn {
  background: var(--primary);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: white;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-buttons {
  display: flex;
  gap: 10px;
}

.share-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.link-btn {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.telegram-btn {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
}

.share-btn:active {
  transform: scale(0.98);
}

/* View header */
.view-header {
  text-align: center;
  margin-bottom: 8px;
}

.view-title {
  font-size: 18px;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.view-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--success);
  color: white;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  animation: slideUp 0.3s ease;
  z-index: 1000;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
