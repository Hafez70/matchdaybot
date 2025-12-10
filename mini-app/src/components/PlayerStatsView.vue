<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const props = defineProps({
  leagueCode: {
    type: String,
    required: true
  }
})

const { userId, userName, hapticFeedback } = useTelegram()

const stats = ref(null)
const loading = ref(true)
const error = ref(null)

const fetchStats = async () => {
  if (!props.leagueCode || !userId.value) return
  
  loading.value = true
  error.value = null
  
  try {
    stats.value = await api.getPlayerStats(props.leagueCode, userId.value)
    hapticFeedback('success')
  } catch (err) {
    if (err.response?.status === 404) {
      error.value = 'شما هنوز عضو این لیگ نیستید'
    } else {
      error.value = 'خطا در دریافت آمار'
    }
    console.error('Stats error:', err)
    hapticFeedback('error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
watch(() => props.leagueCode, fetchStats)

const winRate = computed(() => {
  if (!stats.value || stats.value.matches === 0) return 0
  return Math.round((stats.value.wins / stats.value.matches) * 100)
})

const pointsClass = computed(() => {
  if (!stats.value) return ''
  if (stats.value.points > 0) return 'positive'
  if (stats.value.points < 0) return 'negative'
  return 'neutral'
})

const gdClass = computed(() => {
  if (!stats.value) return ''
  if (stats.value.goal_difference > 0) return 'positive'
  if (stats.value.goal_difference < 0) return 'negative'
  return 'neutral'
})
</script>

<template>
  <div class="stats-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchStats">
        تلاش مجدد
      </button>
    </div>

    <!-- Stats Content -->
    <div v-else-if="stats" class="stats-content">
      <!-- Player Header -->
      <div class="player-header">
        <div class="player-avatar">
          {{ stats.name?.charAt(0)?.toUpperCase() || '?' }}
        </div>
        <div class="player-details">
          <h2 class="player-name">{{ stats.name }}</h2>
          <div class="player-rank">
            <span class="rank-badge" :class="getRankBadgeClass(stats.rank)">
              {{ getRankEmoji(stats.rank) }} رتبه {{ stats.rank }}
            </span>
          </div>
        </div>
      </div>

      <!-- Main Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card highlight">
          <div class="stat-value" :class="pointsClass">
            {{ stats.points > 0 ? '+' : '' }}{{ stats.points }}
          </div>
          <div class="stat-label">امتیاز</div>
        </div>

        <div class="stat-card">
          <div class="stat-value primary">{{ stats.matches }}</div>
          <div class="stat-label">بازی</div>
        </div>

        <div class="stat-card">
          <div class="stat-value positive">{{ stats.wins }}</div>
          <div class="stat-label">برد</div>
        </div>

        <div class="stat-card">
          <div class="stat-value negative">{{ stats.losses }}</div>
          <div class="stat-label">باخت</div>
        </div>
      </div>

      <!-- Secondary Stats -->
      <div class="secondary-stats">
        <div class="stat-row">
          <span class="stat-name">مساوی</span>
          <span class="stat-value-inline neutral">{{ stats.draws }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-name">تفاضل گل</span>
          <span class="stat-value-inline" :class="gdClass">
            {{ stats.goal_difference > 0 ? '+' : '' }}{{ stats.goal_difference }}
          </span>
        </div>
        <div class="stat-row">
          <span class="stat-name">درصد برد</span>
          <span class="stat-value-inline primary">{{ winRate }}%</span>
        </div>
      </div>

      <!-- Performance Chart (Visual) -->
      <div class="performance-chart">
        <h4 class="chart-title">عملکرد</h4>
        <div class="chart-bars">
          <div class="chart-bar wins" :style="{ width: `${(stats.wins / Math.max(stats.matches, 1)) * 100}%` }">
            <span v-if="stats.wins > 0">{{ stats.wins }}</span>
          </div>
          <div class="chart-bar draws" :style="{ width: `${(stats.draws / Math.max(stats.matches, 1)) * 100}%` }">
            <span v-if="stats.draws > 0">{{ stats.draws }}</span>
          </div>
          <div class="chart-bar losses" :style="{ width: `${(stats.losses / Math.max(stats.matches, 1)) * 100}%` }">
            <span v-if="stats.losses > 0">{{ stats.losses }}</span>
          </div>
        </div>
        <div class="chart-legend">
          <span class="legend-item wins">برد</span>
          <span class="legend-item draws">مساوی</span>
          <span class="legend-item losses">باخت</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    getRankEmoji(rank) {
      if (rank === 1) return '🥇'
      if (rank === 2) return '🥈'
      if (rank === 3) return '🥉'
      return '🏅'
    },
    getRankBadgeClass(rank) {
      if (rank === 1) return 'gold'
      if (rank === 2) return 'silver'
      if (rank === 3) return 'bronze'
      return ''
    }
  }
}
</script>

<style scoped>
.stats-view {
  padding-bottom: 20px;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.05));
  border-radius: var(--radius-xl);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.player-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  box-shadow: var(--shadow-glow);
}

.player-details {
  flex: 1;
}

.player-name {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.rank-badge {
  display: inline-block;
  padding: 6px 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 500;
}

.rank-badge.gold {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 215, 0, 0.1));
  color: var(--gold);
}

.rank-badge.silver {
  background: linear-gradient(135deg, rgba(192, 192, 192, 0.2), rgba(192, 192, 192, 0.1));
  color: var(--silver);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, rgba(205, 127, 50, 0.2), rgba(205, 127, 50, 0.1));
  color: var(--bronze);
}

.stat-card.highlight {
  grid-column: span 2;
  background: linear-gradient(135deg, var(--bg-card), rgba(139, 92, 246, 0.1));
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.stat-card.highlight .stat-value {
  font-size: 2.5rem;
}

.secondary-stats {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-name {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stat-value-inline {
  font-weight: 700;
  font-size: 1rem;
}

.stat-value-inline.positive { color: var(--success); }
.stat-value-inline.negative { color: var(--danger); }
.stat-value-inline.neutral { color: var(--warning); }
.stat-value-inline.primary { color: var(--primary-light); }

.performance-chart {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.chart-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.chart-bars {
  display: flex;
  height: 32px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.chart-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: white;
  transition: width 0.5s ease;
  min-width: 0;
}

.chart-bar.wins {
  background: var(--success);
}

.chart-bar.draws {
  background: var(--warning);
}

.chart-bar.losses {
  background: var(--danger);
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.legend-item::before {
  content: '';
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-item.wins::before {
  background: var(--success);
}

.legend-item.draws::before {
  background: var(--warning);
}

.legend-item.losses::before {
  background: var(--danger);
}
</style>

