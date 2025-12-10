<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const props = defineProps({
  leagueCode: {
    type: String,
    required: true
  }
})

const { userId, hapticFeedback } = useTelegram()

const leaderboard = ref([])
const loading = ref(true)
const error = ref(null)

const fetchLeaderboard = async () => {
  if (!props.leagueCode) return
  
  loading.value = true
  error.value = null
  
  try {
    leaderboard.value = await api.getLeaderboard(props.leagueCode, userId.value)
    hapticFeedback('success')
  } catch (err) {
    error.value = 'خطا در دریافت جدول امتیازات'
    console.error('Leaderboard error:', err)
    hapticFeedback('error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchLeaderboard)
watch(() => props.leagueCode, fetchLeaderboard)

const getRankClass = (rank) => {
  if (rank === 1) return 'gold'
  if (rank === 2) return 'silver'
  if (rank === 3) return 'bronze'
  return ''
}

const getItemClass = (player) => {
  const classes = []
  if (player.rank === 1) classes.push('top-1')
  if (player.rank === 2) classes.push('top-2')
  if (player.rank === 3) classes.push('top-3')
  if (player.telegram_id === userId.value) classes.push('is-me')
  return classes.join(' ')
}

const getAnimationDelay = (index) => {
  return `${index * 0.05}s`
}
</script>

<template>
  <div class="leaderboard-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchLeaderboard">
        تلاش مجدد
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="leaderboard.length === 0" class="empty-state">
      <div class="empty-icon">🏆</div>
      <p class="empty-text">هنوز هیچ بازیکنی در جدول نیست</p>
    </div>

    <!-- Leaderboard List -->
    <div v-else class="leaderboard">
      <div
        v-for="(player, index) in leaderboard"
        :key="player.telegram_id"
        class="leaderboard-item"
        :class="getItemClass(player)"
        :style="{ animationDelay: getAnimationDelay(index) }"
      >
        <!-- Rank -->
        <div class="rank" :class="getRankClass(player.rank)">
          <template v-if="player.rank === 1">🥇</template>
          <template v-else-if="player.rank === 2">🥈</template>
          <template v-else-if="player.rank === 3">🥉</template>
          <template v-else>{{ player.rank }}</template>
        </div>

        <!-- Player Info -->
        <div class="player-info">
          <div class="player-name">
            {{ player.name }}
            <span v-if="player.telegram_id === userId" class="me-badge">شما</span>
          </div>
          <div class="player-stats">
            <span class="stat win">{{ player.wins }}W</span>
            <span class="stat draw">{{ player.draws }}D</span>
            <span class="stat loss">{{ player.losses }}L</span>
            <span class="stat gd" :class="{ positive: player.goal_difference > 0, negative: player.goal_difference < 0 }">
              {{ player.goal_difference > 0 ? '+' : '' }}{{ player.goal_difference }}
            </span>
          </div>
        </div>

        <!-- Points -->
        <div class="player-points">
          <span class="points-value" :class="{ positive: player.points > 0, negative: player.points < 0 }">
            {{ player.points > 0 ? '+' : '' }}{{ player.points }}
          </span>
          <span class="points-label">امتیاز</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard-view {
  padding-bottom: 20px;
}

.me-badge {
  display: inline-block;
  background: var(--primary);
  color: white;
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 6px;
  vertical-align: middle;
}

.player-stats {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  margin-top: 4px;
}

.stat {
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.stat.win {
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
}

.stat.draw {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.stat.loss {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

.stat.gd {
  background: rgba(139, 92, 246, 0.15);
  color: var(--primary-light);
}

.stat.gd.positive {
  color: var(--success);
}

.stat.gd.negative {
  color: var(--danger);
}

.points-value.positive {
  color: var(--success);
}

.points-value.negative {
  color: var(--danger);
}
</style>

