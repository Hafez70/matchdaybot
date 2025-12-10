<script setup>
import { ref, onMounted, defineEmits } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const emit = defineEmits(['select-league'])

const { userId, userName, hapticFeedback } = useTelegram()

const leagues = ref([])
const loading = ref(true)
const error = ref(null)

const fetchLeagues = async () => {
  if (!userId.value) {
    error.value = 'کاربر شناسایی نشد'
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    leagues.value = await api.getUserLeagues(userId.value)
  } catch (err) {
    if (err.response?.status === 404) {
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
        سلام {{ userName }}! 👋
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
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
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  text-align: center;
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

