<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from './services/api'
import { useTelegram } from './composables/useTelegram'
import LeaderboardView from './components/LeaderboardView.vue'
import MatchesView from './components/MatchesView.vue'
import MembersView from './components/MembersView.vue'
import PlayerStatsView from './components/PlayerStatsView.vue'

const { leagueCode, isReady, userName, hapticFeedback } = useTelegram()

const activeTab = ref('leaderboard')
const league = ref(null)
const loading = ref(true)
const error = ref(null)

const tabs = [
  { id: 'leaderboard', label: '🏆 جدول', icon: '🏆' },
  { id: 'matches', label: '⚽ مسابقات', icon: '⚽' },
  { id: 'members', label: '👥 اعضا', icon: '👥' },
  { id: 'stats', label: '📊 آمار من', icon: '📊' }
]

const fetchLeagueInfo = async () => {
  if (!leagueCode.value) {
    error.value = 'کد لیگ مشخص نشده'
    loading.value = false
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    league.value = await api.getLeagueInfo(leagueCode.value)
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'لیگ پیدا نشد'
    } else {
      error.value = 'خطا در دریافت اطلاعات لیگ'
    }
    console.error('League info error:', err)
  } finally {
    loading.value = false
  }
}

const switchTab = (tabId) => {
  activeTab.value = tabId
  hapticFeedback('light')
}

onMounted(() => {
  if (isReady.value && leagueCode.value) {
    fetchLeagueInfo()
  }
})

watch([isReady, leagueCode], ([ready, code]) => {
  if (ready && code) {
    fetchLeagueInfo()
  }
})
</script>

<template>
  <div class="app">
    <!-- Loading State -->
    <div v-if="loading" class="loading full-screen">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state full-screen">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchLeagueInfo">
        تلاش مجدد
      </button>
    </div>

    <!-- Main Content -->
    <div v-else-if="league" class="main-content">
      <!-- League Header -->
      <div class="league-header">
        <div class="league-icon">🏆</div>
        <h1 class="league-name">{{ league.name }}</h1>
        <div class="league-meta">
          <span class="league-meta-item">
            👥 {{ league.member_count }} عضو
          </span>
          <span class="league-meta-item">
            👑 {{ league.owner_name }}
          </span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab"
          :class="{ active: activeTab === tab.id }"
          @click="switchTab(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <Transition name="fade" mode="out-in">
        <component
          :is="activeComponent"
          :key="activeTab"
          :league-code="leagueCode"
        />
      </Transition>
    </div>

    <!-- No League Selected -->
    <div v-else class="empty-state full-screen">
      <div class="empty-icon">🎮</div>
      <h2>MatchDay</h2>
      <p class="empty-text">
        لطفاً از طریق ربات تلگرام وارد شوید
      </p>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    activeComponent() {
      const components = {
        leaderboard: 'LeaderboardView',
        matches: 'MatchesView',
        members: 'MembersView',
        stats: 'PlayerStatsView'
      }
      return components[this.activeTab] || 'LeaderboardView'
    }
  },
  components: {
    LeaderboardView,
    MatchesView,
    MembersView,
    PlayerStatsView
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
}

.full-screen {
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
