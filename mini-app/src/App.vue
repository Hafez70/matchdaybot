<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from './services/api'
import { useTelegram } from './composables/useTelegram'
import LeagueSelector from './components/LeagueSelector.vue'
import LeaderboardView from './components/LeaderboardView.vue'
import MatchesView from './components/MatchesView.vue'
import MembersView from './components/MembersView.vue'
import PlayerStatsView from './components/PlayerStatsView.vue'

const { leagueCode: initialLeagueCode, isReady, userName, userId, hapticFeedback, showBackButton, hideBackButton } = useTelegram()

// App state
const currentView = ref('selector') // 'selector' | 'league'
const selectedLeague = ref(null)
const activeTab = ref('leaderboard')
const league = ref(null)
const loading = ref(false)
const error = ref(null)

const tabs = [
  { id: 'leaderboard', label: '🏆 جدول', icon: '🏆' },
  { id: 'matches', label: '⚽ مسابقات', icon: '⚽' },
  { id: 'members', label: '👥 اعضا', icon: '👥' },
  { id: 'stats', label: '📊 آمار من', icon: '📊' }
]

const currentLeagueCode = computed(() => {
  return selectedLeague.value?.code || initialLeagueCode.value
})

const fetchLeagueInfo = async () => {
  if (!currentLeagueCode.value) {
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    league.value = await api.getLeagueInfo(currentLeagueCode.value)
    currentView.value = 'league'
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

const onSelectLeague = (leagueData) => {
  selectedLeague.value = leagueData
  fetchLeagueInfo()
}

const goBack = () => {
  hapticFeedback('light')
  currentView.value = 'selector'
  selectedLeague.value = null
  league.value = null
  hideBackButton()
}

const switchTab = (tabId) => {
  activeTab.value = tabId
  hapticFeedback('light')
}

// Watch for view changes to show/hide back button
watch(currentView, (newView) => {
  if (newView === 'league') {
    showBackButton(goBack)
  } else {
    hideBackButton()
  }
})

onMounted(() => {
  // If league code is provided (from bot deep link), go directly to league view
  if (isReady.value && initialLeagueCode.value) {
    fetchLeagueInfo()
  }
})

watch([isReady, initialLeagueCode], ([ready, code]) => {
  if (ready && code && !selectedLeague.value) {
    fetchLeagueInfo()
  }
})
</script>

<template>
  <div class="app">
    <!-- League Selector View -->
    <LeagueSelector 
      v-if="currentView === 'selector' && !loading"
      @select-league="onSelectLeague"
    />

    <!-- Loading State -->
    <div v-else-if="loading" class="loading full-screen">
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
      <button class="back-btn" @click="goBack">
        بازگشت
      </button>
    </div>

    <!-- League Detail View -->
    <div v-else-if="currentView === 'league' && league" class="main-content">
      <!-- League Header -->
      <div class="league-header">
        <button class="back-arrow" @click="goBack">←</button>
        <div class="header-content">
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
          :league-code="currentLeagueCode"
        />
      </Transition>
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
    LeagueSelector,
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
  gap: 16px;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.league-header {
  position: relative;
  padding: 20px;
  padding-top: 10px;
}

.back-arrow {
  position: absolute;
  left: 10px;
  top: 10px;
  background: var(--card-bg);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: var(--text-primary);
}

.back-arrow:hover {
  background: var(--primary);
  color: white;
}

.header-content {
  text-align: center;
}

.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  margin-top: 10px;
}

.back-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
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
}

.error-icon {
  font-size: 64px;
}

.error-message {
  color: var(--text-secondary);
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
