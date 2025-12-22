<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const props = defineProps({
  leagueCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const { hapticFeedback } = useTelegram()

const matches = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const error = ref(null)
const hasMore = ref(true)
const offset = ref(0)
const limit = 15

// Edit state
const editingMatchId = ref(null)
const editTeam1Score = ref(0)
const editTeam2Score = ref(0)
const saving = ref(false)

// Delete state
const deleteModalVisible = ref(false)
const matchToDelete = ref(null)
const deleting = ref(false)

const fetchMatches = async (reset = true) => {
  if (!props.leagueCode) return
  
  if (reset) {
    loading.value = true
    offset.value = 0
    matches.value = []
    hasMore.value = true
  } else {
    loadingMore.value = true
  }
  
  error.value = null
  
  try {
    const newMatches = await api.getMatches(props.leagueCode, limit, offset.value)
    
    if (reset) {
      matches.value = newMatches
    } else {
      matches.value = [...matches.value, ...newMatches]
    }
    
    hasMore.value = newMatches.length === limit
    offset.value += newMatches.length
    
    if (reset) hapticFeedback('success')
  } catch (err) {
    error.value = 'خطا در دریافت مسابقات'
    console.error('Matches error:', err)
    hapticFeedback('error')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Infinite scroll
const scrollContainer = ref(null)
const handleScroll = () => {
  if (!scrollContainer.value || loadingMore.value || !hasMore.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
  if (scrollTop + clientHeight >= scrollHeight - 100) {
    fetchMatches(false)
  }
}

onMounted(() => {
  fetchMatches()
  // Try to find scroll container (parent or window)
  setTimeout(() => {
    const el = document.querySelector('.main-content')
    if (el) {
      scrollContainer.value = el
      el.addEventListener('scroll', handleScroll)
    }
  }, 100)
})

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', handleScroll)
  }
})

watch(() => props.leagueCode, () => fetchMatches(true))

// Format date in Tehran timezone (UTC+3:30)
const formatDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('fa-IR', {
      timeZone: 'Asia/Tehran',
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
  return `${Math.min(index, 10) * 0.05}s`
}

// Edit functions
const startEdit = (match) => {
  hapticFeedback('light')
  editingMatchId.value = match.id
  editTeam1Score.value = match.team1_score
  editTeam2Score.value = match.team2_score
}

const cancelEdit = () => {
  hapticFeedback('light')
  editingMatchId.value = null
}

const saveEdit = async (match) => {
  if (saving.value) return
  
  saving.value = true
  hapticFeedback('light')
  
  try {
    await api.updateMatch(match.id, editTeam1Score.value, editTeam2Score.value)
    
    // Update local data
    const idx = matches.value.findIndex(m => m.id === match.id)
    if (idx !== -1) {
      matches.value[idx] = {
        ...matches.value[idx],
        team1_score: editTeam1Score.value,
        team2_score: editTeam2Score.value
      }
    }
    
    editingMatchId.value = null
    hapticFeedback('success')
    emit('refresh')
  } catch (err) {
    console.error('Update match error:', err)
    hapticFeedback('error')
    alert(err.response?.data?.detail || 'خطا در ویرایش مسابقه')
  } finally {
    saving.value = false
  }
}

const incrementScore = (team) => {
  hapticFeedback('light')
  if (team === 1) {
    editTeam1Score.value++
  } else {
    editTeam2Score.value++
  }
}

const decrementScore = (team) => {
  hapticFeedback('light')
  if (team === 1 && editTeam1Score.value > 0) {
    editTeam1Score.value--
  } else if (team === 2 && editTeam2Score.value > 0) {
    editTeam2Score.value--
  }
}

// Delete functions
const confirmDelete = (match) => {
  hapticFeedback('warning')
  matchToDelete.value = match
  deleteModalVisible.value = true
}

const cancelDelete = () => {
  hapticFeedback('light')
  deleteModalVisible.value = false
  matchToDelete.value = null
}

const executeDelete = async () => {
  if (!matchToDelete.value || deleting.value) return
  
  deleting.value = true
  hapticFeedback('light')
  
  try {
    await api.deleteMatch(matchToDelete.value.id)
    
    // Remove from local data
    matches.value = matches.value.filter(m => m.id !== matchToDelete.value.id)
    
    deleteModalVisible.value = false
    matchToDelete.value = null
    hapticFeedback('success')
    emit('refresh')
  } catch (err) {
    console.error('Delete match error:', err)
    hapticFeedback('error')
    alert(err.response?.data?.detail || 'خطا در حذف مسابقه')
  } finally {
    deleting.value = false
  }
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
      <button class="retry-btn" @click="fetchMatches(true)">
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
        :class="{ 'editing': editingMatchId === match.id }"
        :style="{ animationDelay: getAnimationDelay(index) }"
      >
        <!-- Normal View -->
        <template v-if="editingMatchId !== match.id">
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

          <!-- Action Buttons -->
          <div class="match-actions">
            <button class="action-btn edit-btn" @click="startEdit(match)">
              ✏️ ویرایش
            </button>
            <button class="action-btn delete-btn" @click="confirmDelete(match)">
              🗑️ حذف
            </button>
          </div>
        </template>

        <!-- Edit View -->
        <template v-else>
          <div class="edit-header">
            <span class="edit-title">ویرایش نتیجه</span>
            <span class="match-date">{{ formatDate(match.created_at) }}</span>
          </div>

          <div class="edit-teams">
            <!-- Team 1 -->
            <div class="edit-team">
              <div class="team-players compact">
                <div v-for="player in match.team1" :key="player" class="player">
                  {{ player }}
                </div>
              </div>
              <div class="score-controls">
                <button class="score-btn minus" @click="decrementScore(1)" :disabled="editTeam1Score <= 0">−</button>
                <span class="score-value">{{ editTeam1Score }}</span>
                <button class="score-btn plus" @click="incrementScore(1)">+</button>
              </div>
            </div>

            <div class="vs-separator">VS</div>

            <!-- Team 2 -->
            <div class="edit-team">
              <div class="team-players compact">
                <div v-for="player in match.team2" :key="player" class="player">
                  {{ player }}
                </div>
              </div>
              <div class="score-controls">
                <button class="score-btn minus" @click="decrementScore(2)" :disabled="editTeam2Score <= 0">−</button>
                <span class="score-value">{{ editTeam2Score }}</span>
                <button class="score-btn plus" @click="incrementScore(2)">+</button>
              </div>
            </div>
          </div>

          <div class="edit-actions">
            <button class="action-btn cancel-btn" @click="cancelEdit" :disabled="saving">
              انصراف
            </button>
            <button class="action-btn save-btn" @click="saveEdit(match)" :disabled="saving">
              {{ saving ? '...' : '💾 ذخیره' }}
            </button>
          </div>
        </template>
      </div>

      <!-- Load More Indicator -->
      <div v-if="loadingMore" class="loading-more">
        <div class="spinner small"></div>
        <span>بارگذاری بیشتر...</span>
      </div>

      <!-- End of List -->
      <div v-else-if="!hasMore && matches.length > 0" class="end-of-list">
        پایان لیست
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="deleteModalVisible" class="modal-overlay" @click.self="cancelDelete">
        <div class="modal-content">
          <div class="modal-icon">⚠️</div>
          <h3 class="modal-title">حذف مسابقه</h3>
          <p class="modal-message">
            آیا از حذف این مسابقه مطمئن هستید؟
            <br>
            <strong>{{ matchToDelete?.team1?.join(' و ') }}</strong>
            {{ matchToDelete?.team1_score }} - {{ matchToDelete?.team2_score }}
            <strong>{{ matchToDelete?.team2?.join(' و ') }}</strong>
          </p>
          <div class="modal-actions">
            <button class="modal-btn cancel" @click="cancelDelete" :disabled="deleting">
              انصراف
            </button>
            <button class="modal-btn confirm" @click="executeDelete" :disabled="deleting">
              {{ deleting ? '...' : '🗑️ حذف' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.matches-view {
  padding-bottom: 20px;
}

.match-card {
  position: relative;
  overflow: hidden;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 12px;
  animation: slideIn 0.3s ease forwards;
  opacity: 0;
  transform: translateY(10px);
}

.match-card.editing {
  border-color: var(--primary);
  background: rgba(139, 92, 246, 0.05);
}

@keyframes slideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

.team-players.compact {
  gap: 2px;
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

/* Action Buttons */
.match-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: var(--primary);
  color: var(--text-primary);
}

.action-btn:active {
  transform: scale(0.98);
}

.edit-btn:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: var(--primary);
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: var(--danger);
  color: var(--danger);
}

/* Edit View */
.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.edit-title {
  font-weight: 600;
  color: var(--primary);
}

.edit-teams {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-team {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-md);
}

.vs-separator {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
}

.score-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: var(--card-bg);
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.score-btn:hover:not(:disabled) {
  border-color: var(--primary);
  background: rgba(139, 92, 246, 0.1);
}

.score-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.score-btn.plus:hover:not(:disabled) {
  border-color: var(--success);
  background: rgba(16, 185, 129, 0.1);
}

.score-btn.minus:hover:not(:disabled) {
  border-color: var(--danger);
  background: rgba(239, 68, 68, 0.1);
}

.score-value {
  min-width: 40px;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary);
}

.edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.cancel-btn {
  background: transparent;
}

.save-btn {
  background: linear-gradient(135deg, var(--primary), #6366f1);
  border-color: transparent;
  color: white;
}

.save-btn:hover {
  opacity: 0.9;
}

/* Loading More */
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

.end-of-list {
  text-align: center;
  padding: 16px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  padding: 20px;
}

.modal-content {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  max-width: 320px;
  width: 100%;
  text-align: center;
  animation: modalIn 0.2s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.modal-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.modal-message {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
}

.modal-message strong {
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  gap: 10px;
}

.modal-btn {
  flex: 1;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn.cancel {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.modal-btn.cancel:hover {
  border-color: var(--text-muted);
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  color: white;
}

.modal-btn.confirm:hover {
  opacity: 0.9;
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
