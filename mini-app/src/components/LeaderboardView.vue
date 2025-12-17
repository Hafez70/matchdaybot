<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const props = defineProps({
  leagueCode: {
    type: String,
    required: true
  }
})

const { userId, hapticFeedback } = useTelegram()

const qualifiedPlayers = ref([])
const unqualifiedPlayers = ref([])
const minMatches = ref(0)
const loading = ref(true)
const error = ref(null)

const fetchLeaderboard = async () => {
  if (!props.leagueCode) return
  
  loading.value = true
  error.value = null
  
  try {
    const response = await api.getLeaderboard(props.leagueCode, userId.value)
    qualifiedPlayers.value = response.qualified || []
    unqualifiedPlayers.value = response.unqualified || []
    minMatches.value = response.min_matches || 0
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
    <div v-else-if="qualifiedPlayers.length === 0 && unqualifiedPlayers.length === 0" class="empty-state">
      <div class="empty-icon">🏆</div>
      <p class="empty-text">هنوز هیچ بازیکنی در جدول نیست</p>
    </div>

    <!-- Leaderboard Content -->
    <div v-else class="leaderboard-content">
      <!-- Qualified Players Section -->
      <div v-if="qualifiedPlayers.length > 0" class="leaderboard-section">
        <h3 class="section-title">🏆 جدول رتبه‌بندی</h3>
        <div class="leaderboard">
          <div
            v-for="(player, index) in qualifiedPlayers"
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

      <!-- No Qualified Players -->
      <div v-else class="no-qualified-notice">
        <span class="notice-icon">📊</span>
        <p>هنوز کسی واجد شرایط رتبه‌بندی نیست</p>
        <p class="notice-hint">حداقل {{ minMatches }} بازی برای ورود به جدول نیاز است</p>
      </div>

      <!-- Unqualified Players Section -->
      <div v-if="unqualifiedPlayers.length > 0" class="leaderboard-section unqualified-section">
        <h3 class="section-title unqualified">
          <span>⏳</span>
          در انتظار واجد شرایط شدن
          <span class="min-matches-hint">(حداقل {{ minMatches }} بازی)</span>
        </h3>
        <div class="leaderboard unqualified-list">
          <div
            v-for="(player, index) in unqualifiedPlayers"
            :key="player.telegram_id"
            class="leaderboard-item unqualified"
            :class="{ 'is-me': player.telegram_id === userId }"
            :style="{ animationDelay: getAnimationDelay(index + qualifiedPlayers.length) }"
          >
            <!-- No Rank -->
            <div class="rank no-rank">
              <span class="rank-dash">—</span>
            </div>

            <!-- Player Info -->
            <div class="player-info">
              <div class="player-name">
                {{ player.name }}
                <span v-if="player.telegram_id === userId" class="me-badge">شما</span>
              </div>
              <div class="player-stats">
                <span class="stat matches">{{ player.matches }} بازی</span>
                <span class="stat needed">{{ minMatches - player.matches }} مانده</span>
              </div>
            </div>

            <!-- Points (muted) -->
            <div class="player-points muted">
              <span class="points-value">
                {{ player.points > 0 ? '+' : '' }}{{ player.points }}
              </span>
              <span class="points-label">امتیاز</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard-view {
  padding-bottom: 20px;
}

.leaderboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.leaderboard-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title.unqualified {
  color: var(--warning);
  font-size: 13px;
}

.min-matches-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
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

.stat.matches {
  background: rgba(100, 116, 139, 0.15);
  color: var(--text-secondary);
}

.stat.needed {
  background: rgba(251, 191, 36, 0.15);
  color: var(--warning);
}

.points-value.positive {
  color: var(--success);
}

.points-value.negative {
  color: var(--danger);
}

/* Unqualified Section */
.unqualified-section {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px dashed var(--border);
}

.leaderboard-item.unqualified {
  opacity: 0.7;
  background: rgba(100, 116, 139, 0.05);
}

.leaderboard-item.unqualified.is-me {
  opacity: 1;
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.3);
}

.rank.no-rank {
  background: rgba(100, 116, 139, 0.1);
}

.rank-dash {
  color: var(--text-muted);
  font-weight: 400;
}

.player-points.muted {
  opacity: 0.6;
}

.player-points.muted .points-value {
  color: var(--text-secondary);
}

/* No Qualified Notice */
.no-qualified-notice {
  text-align: center;
  padding: 24px;
  background: rgba(100, 116, 139, 0.1);
  border-radius: 12px;
}

.no-qualified-notice .notice-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.no-qualified-notice p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.no-qualified-notice .notice-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}
</style>

