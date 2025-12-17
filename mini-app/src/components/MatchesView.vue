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

const { hapticFeedback } = useTelegram()

const matches = ref([])
const loading = ref(true)
const error = ref(null)

const fetchMatches = async () => {
  if (!props.leagueCode) return
  
  loading.value = true
  error.value = null
  
  try {
    matches.value = await api.getMatches(props.leagueCode, 30)
    hapticFeedback('success')
  } catch (err) {
    error.value = 'خطا در دریافت مسابقات'
    console.error('Matches error:', err)
    hapticFeedback('error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchMatches)
watch(() => props.leagueCode, fetchMatches)

const formatDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('fa-IR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  } catch {
    return dateStr
  }
}

const getResultEmoji = (match) => {
  if (match.team1_score > match.team2_score) return '🏆'
  if (match.team1_score < match.team2_score) return '❌'
  return '🤝'
}

const getScoreClass = (match, team) => {
  if (match.team1_score === match.team2_score) return 'draw'
  if (team === 1) {
    return match.team1_score > match.team2_score ? 'winner' : 'loser'
  }
  return match.team2_score > match.team1_score ? 'winner' : 'loser'
}

const getAnimationDelay = (index) => {
  return `${index * 0.05}s`
}
</script>

<template>
  <div class="matches-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchMatches">
        تلاش مجدد
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="matches.length === 0" class="empty-state">
      <div class="empty-icon">⚽</div>
      <p class="empty-text">هنوز هیچ مسابقه‌ای ثبت نشده</p>
    </div>

    <!-- Matches List -->
    <div v-else class="matches-list">
      <div
        v-for="(match, index) in matches"
        :key="match.id"
        class="match-card"
        :style="{ animationDelay: getAnimationDelay(index) }"
      >
        <!-- Match Header -->
        <div class="match-header">
          <div class="match-meta">
            <span class="match-date">{{ formatDate(match.created_at) }}</span>
            <span class="result-emoji">{{ getResultEmoji(match) }}</span>
          </div>
          <span class="match-type">{{ match.match_type }}</span>
        </div>

        <!-- Teams and Score -->
        <div class="match-teams">
          <!-- Team 1 -->
          <div class="team team-1">
            <div class="team-players">
              <div v-for="player in match.team1" :key="player" class="player">
                {{ player }}
              </div>
            </div>
          </div>

          <!-- Score -->
          <div class="match-score">
            <span class="score" :class="getScoreClass(match, 1)">
              {{ match.team1_score }}
            </span>
            <span class="score-separator">-</span>
            <span class="score" :class="getScoreClass(match, 2)">
              {{ match.team2_score }}
            </span>
          </div>

          <!-- Team 2 -->
          <div class="team team-2">
            <div class="team-players">
              <div v-for="player in match.team2" :key="player" class="player">
                {{ player }}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.matches-view {
  padding-bottom: 20px;
}

.match-card {
  position: relative;
  overflow: hidden;
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.match-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.match-date {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.result-emoji {
  font-size: 1rem;
}

.match-teams {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: center;
}

.team {
  text-align: center;
}

.team-1 {
  text-align: left;
}

.team-2 {
  text-align: right;
}

.team-players {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.team-1 .team-players {
  align-items: flex-start;
}

.team-2 .team-players {
  align-items: flex-end;
}

.player {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.match-score {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
}

.score {
  font-size: 1.5rem;
  font-weight: 800;
  min-width: 32px;
  text-align: center;
}

.score.winner {
  color: var(--success);
}

.score.loser {
  color: var(--danger);
}

.score.draw {
  color: var(--warning);
}

.score-separator {
  color: var(--text-muted);
  font-weight: 400;
}

.match-type {
  font-size: 0.75rem;
  color: var(--primary);
  background: rgba(139, 92, 246, 0.15);
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
}
</style>

