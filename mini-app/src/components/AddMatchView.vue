<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { useTelegram } from '../composables/useTelegram'

const props = defineProps({
  leagueCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['back', 'success'])

const { hapticFeedback } = useTelegram()

// State
const step = ref('team1') // 'team1' | 'team2' | 'results'
const members = ref([])
const loading = ref(true)
const submitting = ref(false)
const error = ref(null)

// Team selections
const team1Selected = ref([])
const team2Selected = ref([])

// Results list
const resultsList = ref([])
const currentResult = ref({ team1_score: '', team2_score: '' })
const editingIndex = ref(null)

// Delete confirmation
const deleteConfirmIndex = ref(null)

// Computed
const team1Names = computed(() => {
  return team1Selected.value
    .map(id => members.value.find(m => m.telegram_id === id)?.name || '')
    .join(' و ')
})

const team2Names = computed(() => {
  return team2Selected.value
    .map(id => members.value.find(m => m.telegram_id === id)?.name || '')
    .join(' و ')
})

const availableForTeam1 = computed(() => members.value)

const availableForTeam2 = computed(() => {
  return members.value.filter(m => !team1Selected.value.includes(m.telegram_id))
})

const canFinishTeam1 = computed(() => team1Selected.value.length >= 1)
const canFinishTeam2 = computed(() => team2Selected.value.length >= 1)

const canSubmitCurrent = computed(() => {
  const s1 = currentResult.value.team1_score
  const s2 = currentResult.value.team2_score
  return s1 !== '' && s2 !== '' && 
         !isNaN(parseInt(s1)) && !isNaN(parseInt(s2)) &&
         parseInt(s1) >= 0 && parseInt(s2) >= 0
})

const canFinalSubmit = computed(() => resultsList.value.length > 0 && !submitting.value)

// Methods
const fetchMembers = async () => {
  loading.value = true
  error.value = null
  try {
    members.value = await api.getMembers(props.leagueCode)
  } catch (err) {
    error.value = 'خطا در دریافت اعضای لیگ'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const toggleTeam1 = (telegramId) => {
  hapticFeedback('light')
  const idx = team1Selected.value.indexOf(telegramId)
  if (idx === -1) {
    if (team1Selected.value.length < 2) {
      team1Selected.value.push(telegramId)
    }
  } else {
    team1Selected.value.splice(idx, 1)
  }
}

const toggleTeam2 = (telegramId) => {
  hapticFeedback('light')
  const idx = team2Selected.value.indexOf(telegramId)
  if (idx === -1) {
    if (team2Selected.value.length < 2) {
      team2Selected.value.push(telegramId)
    }
  } else {
    team2Selected.value.splice(idx, 1)
  }
}

const finishTeam1 = () => {
  if (!canFinishTeam1.value) return
  hapticFeedback('medium')
  step.value = 'team2'
}

const finishTeam2 = () => {
  if (!canFinishTeam2.value) return
  hapticFeedback('medium')
  step.value = 'results'
}

const goBackToTeam1 = () => {
  hapticFeedback('light')
  step.value = 'team1'
  team2Selected.value = []
}

const addResultToList = () => {
  if (!canSubmitCurrent.value) return
  hapticFeedback('success')
  
  if (editingIndex.value !== null) {
    // Update existing
    resultsList.value[editingIndex.value] = {
      team1_score: parseInt(currentResult.value.team1_score),
      team2_score: parseInt(currentResult.value.team2_score)
    }
    editingIndex.value = null
  } else {
    // Add new
    resultsList.value.push({
      team1_score: parseInt(currentResult.value.team1_score),
      team2_score: parseInt(currentResult.value.team2_score)
    })
  }
  
  // Reset current
  currentResult.value = { team1_score: '', team2_score: '' }
}

const editResult = (index) => {
  hapticFeedback('light')
  editingIndex.value = index
  currentResult.value = {
    team1_score: resultsList.value[index].team1_score.toString(),
    team2_score: resultsList.value[index].team2_score.toString()
  }
}

const cancelEdit = () => {
  hapticFeedback('light')
  editingIndex.value = null
  currentResult.value = { team1_score: '', team2_score: '' }
}

const confirmDelete = (index) => {
  hapticFeedback('warning')
  deleteConfirmIndex.value = index
}

const cancelDelete = () => {
  hapticFeedback('light')
  deleteConfirmIndex.value = null
}

const deleteResult = (index) => {
  hapticFeedback('medium')
  resultsList.value.splice(index, 1)
  deleteConfirmIndex.value = null
  
  // If we were editing this one, cancel edit
  if (editingIndex.value === index) {
    editingIndex.value = null
    currentResult.value = { team1_score: '', team2_score: '' }
  } else if (editingIndex.value !== null && editingIndex.value > index) {
    editingIndex.value--
  }
}

const finalSubmit = async () => {
  if (!canFinalSubmit.value) return
  
  hapticFeedback('medium')
  submitting.value = true
  error.value = null
  
  try {
    const response = await api.createMatches(
      props.leagueCode,
      team1Selected.value,
      team2Selected.value,
      resultsList.value
    )
    
    hapticFeedback('success')
    emit('success', response)
  } catch (err) {
    console.error('Submit error:', err)
    error.value = err.response?.data?.detail || 'خطا در ثبت مسابقات'
    hapticFeedback('error')
  } finally {
    submitting.value = false
  }
}

const getResultEmoji = (result) => {
  if (result.team1_score > result.team2_score) return '🏆'
  if (result.team1_score < result.team2_score) return '❌'
  return '🤝'
}

onMounted(() => {
  fetchMembers()
})
</script>

<template>
  <div class="add-match-container">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error && step === 'team1'" class="error-state">
      <div class="error-icon">😕</div>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="fetchMembers">تلاش مجدد</button>
    </div>

    <!-- Step 1: Team 1 Selection -->
    <div v-else-if="step === 'team1'" class="step-container">
      <div class="step-header">
        <h3 class="step-title">👥 انتخاب تیم ۱</h3>
        <p class="step-subtitle">حداکثر ۲ بازیکن انتخاب کنید</p>
      </div>

      <div class="members-list">
        <div 
          v-for="member in availableForTeam1" 
          :key="member.telegram_id"
          class="member-item"
          :class="{ selected: team1Selected.includes(member.telegram_id) }"
          @click="toggleTeam1(member.telegram_id)"
        >
          <div class="member-checkbox">
            <span v-if="team1Selected.includes(member.telegram_id)">✓</span>
          </div>
          <span class="member-name">{{ member.name }}</span>
        </div>
      </div>

      <div class="step-actions">
        <button 
          class="finish-btn"
          :class="{ disabled: !canFinishTeam1 }"
          :disabled="!canFinishTeam1"
          @click="finishTeam1"
        >
          اتمام انتخاب
          <span v-if="team1Selected.length > 0" class="selected-count">({{ team1Selected.length }})</span>
        </button>
      </div>
    </div>

    <!-- Step 2: Team 2 Selection -->
    <div v-else-if="step === 'team2'" class="step-container">
      <div class="step-header">
        <div class="team1-preview">
          <span class="preview-label">تیم ۱:</span>
          <span class="preview-names">{{ team1Names }}</span>
        </div>
        <h3 class="step-title">👥 انتخاب تیم ۲</h3>
        <p class="step-subtitle">حداکثر ۲ بازیکن انتخاب کنید</p>
      </div>

      <div class="members-list">
        <div 
          v-for="member in availableForTeam2" 
          :key="member.telegram_id"
          class="member-item"
          :class="{ selected: team2Selected.includes(member.telegram_id) }"
          @click="toggleTeam2(member.telegram_id)"
        >
          <div class="member-checkbox">
            <span v-if="team2Selected.includes(member.telegram_id)">✓</span>
          </div>
          <span class="member-name">{{ member.name }}</span>
        </div>
      </div>

      <div class="step-actions">
        <button class="back-btn" @click="goBackToTeam1">
          ← بازگشت
        </button>
        <button 
          class="finish-btn"
          :class="{ disabled: !canFinishTeam2 }"
          :disabled="!canFinishTeam2"
          @click="finishTeam2"
        >
          اتمام انتخاب
          <span v-if="team2Selected.length > 0" class="selected-count">({{ team2Selected.length }})</span>
        </button>
      </div>
    </div>

    <!-- Step 3: Results Entry -->
    <div v-else-if="step === 'results'" class="results-container">
      <!-- Part 1: Fixed Header - Teams -->
      <div class="teams-header">
        <div class="team-side team1-side">
          <span class="team-names">{{ team1Names }}</span>
        </div>
        <div class="vs-badge">VS</div>
        <div class="team-side team2-side">
          <span class="team-names">{{ team2Names }}</span>
        </div>
      </div>

      <!-- Part 2: Scrollable Results List -->
      <div class="results-list">
        <!-- Error message -->
        <div v-if="error" class="error-banner">
          <span>{{ error }}</span>
          <button @click="error = null">✕</button>
        </div>

        <!-- Submitted Results -->
        <div 
          v-for="(result, index) in resultsList" 
          :key="index"
          class="result-card submitted"
        >
          <!-- Delete Confirmation Overlay -->
          <div v-if="deleteConfirmIndex === index" class="delete-confirm-overlay">
            <p>حذف این نتیجه؟</p>
            <div class="confirm-actions">
              <button class="confirm-yes" @click="deleteResult(index)">بله، حذف شود</button>
              <button class="confirm-no" @click="cancelDelete">انصراف</button>
            </div>
          </div>

          <div class="result-content">
            <div class="result-team">
              <span class="result-team-name">{{ team1Names }}</span>
              <span class="result-score">{{ result.team1_score }}</span>
            </div>
            <div class="result-separator">
              <span class="result-emoji">{{ getResultEmoji(result) }}</span>
              <span class="result-dash">-</span>
            </div>
            <div class="result-team">
              <span class="result-score">{{ result.team2_score }}</span>
              <span class="result-team-name">{{ team2Names }}</span>
            </div>
          </div>
          <div class="result-actions">
            <button class="edit-btn" @click="editResult(index)" :disabled="editingIndex !== null">
              ✏️ ویرایش
            </button>
            <button class="delete-btn" @click="confirmDelete(index)">
              🗑️ حذف
            </button>
          </div>
        </div>

        <!-- Current Input Card -->
        <div class="result-card input-card" :class="{ editing: editingIndex !== null }">
          <div class="input-card-header" v-if="editingIndex !== null">
            <span>✏️ ویرایش نتیجه {{ editingIndex + 1 }}</span>
            <button class="cancel-edit-btn" @click="cancelEdit">انصراف</button>
          </div>
          <div class="input-card-header" v-else>
            <span>➕ نتیجه جدید</span>
          </div>
          
          <div class="result-input-content">
            <div class="input-team">
              <span class="input-team-name">{{ team1Names }}</span>
              <input 
                type="number" 
                v-model="currentResult.team1_score"
                min="0"
                placeholder="0"
                class="score-input"
                inputmode="numeric"
              />
            </div>
            <div class="input-separator">-</div>
            <div class="input-team">
              <input 
                type="number" 
                v-model="currentResult.team2_score"
                min="0"
                placeholder="0"
                class="score-input"
                inputmode="numeric"
              />
              <span class="input-team-name">{{ team2Names }}</span>
            </div>
          </div>
          
          <button 
            class="add-result-btn"
            :class="{ disabled: !canSubmitCurrent }"
            :disabled="!canSubmitCurrent"
            @click="addResultToList"
          >
            {{ editingIndex !== null ? '✓ ذخیره تغییرات' : '➕ افزودن به لیست' }}
          </button>
        </div>

        <!-- Empty state hint -->
        <div v-if="resultsList.length === 0" class="empty-hint">
          <p>💡 نتایج مسابقات را وارد کنید</p>
          <p class="hint-sub">می‌توانید چندین نتیجه اضافه کنید</p>
        </div>
      </div>

      <!-- Part 3: Fixed Footer - Final Submit -->
      <div class="submit-footer">
        <div class="results-summary" v-if="resultsList.length > 0">
          <span class="summary-count">{{ resultsList.length }} نتیجه</span>
        </div>
        <button 
          class="final-submit-btn"
          :class="{ disabled: !canFinalSubmit, loading: submitting }"
          :disabled="!canFinalSubmit"
          @click="finalSubmit"
        >
          <span v-if="submitting" class="btn-spinner"></span>
          <span v-else>✅ ثبت نهایی مسابقات</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.add-match-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 120px);
}

/* Loading & Error States */
.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
}

.retry-btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
}

/* Step Container */
.step-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.step-header {
  text-align: center;
  margin-bottom: 20px;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.step-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.team1-preview {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.preview-names {
  font-size: 14px;
  font-weight: 600;
  color: #10b981;
}

/* Members List */
.members-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-bottom: 80px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.member-item:active {
  transform: scale(0.98);
}

.member-item.selected {
  border-color: var(--primary);
  background: rgba(139, 92, 246, 0.1);
}

.member-checkbox {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  transition: all 0.2s;
}

.member-item.selected .member-checkbox {
  background: var(--primary);
  border-color: var(--primary);
}

.member-name {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

/* Step Actions */
.step-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: var(--bg);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 12px;
}

.finish-btn {
  flex: 1;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
  border: none;
  padding: 16px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.finish-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.selected-count {
  opacity: 0.9;
}

.back-btn {
  background: var(--card-bg);
  color: var(--text-primary);
  border: 1px solid var(--border);
  padding: 16px 24px;
  border-radius: 14px;
  font-size: 14px;
  cursor: pointer;
}

/* Results Container */
.results-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Teams Header (Part 1) */
.teams-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(99, 102, 241, 0.1));
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.team-side {
  flex: 1;
  text-align: center;
}

.team1-side {
  text-align: left;
}

.team2-side {
  text-align: right;
}

.team-names {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.vs-badge {
  background: var(--primary);
  color: white;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 20px;
}

/* Results List (Part 2) */
.results-list {
  flex: 1;
  padding: 16px;
  padding-bottom: 100px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #ef4444;
  font-size: 14px;
}

.error-banner button {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  font-size: 16px;
}

/* Result Card */
.result-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  position: relative;
}

.result-card.submitted {
  border-color: rgba(16, 185, 129, 0.3);
}

.result-card.input-card {
  border-color: var(--primary);
  border-width: 2px;
  border-style: dashed;
}

.result-card.input-card.editing {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.05);
}

/* Delete Confirmation Overlay */
.delete-confirm-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 5;
  border-radius: 14px;
}

.delete-confirm-overlay p {
  color: white;
  font-size: 15px;
  margin: 0;
}

.confirm-actions {
  display: flex;
  gap: 10px;
}

.confirm-yes {
  background: #ef4444;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

.confirm-no {
  background: var(--card-bg);
  color: var(--text-primary);
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

/* Result Content */
.result-content {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 8px;
}

.result-team {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-team:first-child {
  justify-content: flex-start;
}

.result-team:last-child {
  justify-content: flex-end;
}

.result-team-name {
  font-size: 13px;
  color: var(--text-secondary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-score {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 30px;
  text-align: center;
}

.result-separator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.result-emoji {
  font-size: 16px;
}

.result-dash {
  font-size: 18px;
  color: var(--text-muted);
}

.result-actions {
  display: flex;
  border-top: 1px solid var(--border);
}

.result-actions button {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn {
  color: var(--primary);
  border-right: 1px solid var(--border) !important;
}

.edit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.delete-btn {
  color: #ef4444;
}

/* Input Card */
.input-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(139, 92, 246, 0.1);
  font-size: 14px;
  font-weight: 500;
  color: var(--primary);
}

.result-card.editing .input-card-header {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.cancel-edit-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.result-input-content {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.input-team {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-team:first-child {
  flex-direction: row;
}

.input-team:last-child {
  flex-direction: row-reverse;
}

.input-team-name {
  font-size: 12px;
  color: var(--text-secondary);
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score-input {
  width: 60px;
  height: 50px;
  border: 2px solid var(--border);
  border-radius: 12px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}

.score-input::-webkit-outer-spin-button,
.score-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.score-input:focus {
  border-color: var(--primary);
}

.input-separator {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-muted);
}

.add-result-btn {
  width: calc(100% - 32px);
  margin: 0 16px 16px;
  padding: 14px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.add-result-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty Hint */
.empty-hint {
  text-align: center;
  padding: 30px;
  color: var(--text-secondary);
}

.empty-hint p {
  margin: 0;
}

.hint-sub {
  font-size: 13px;
  margin-top: 8px !important;
  opacity: 0.7;
}

/* Submit Footer (Part 3) */
.submit-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: var(--bg);
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.results-summary {
  text-align: center;
}

.summary-count {
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 4px 12px;
  border-radius: 20px;
}

.final-submit-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.final-submit-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--text-muted);
}

.final-submit-btn.loading {
  pointer-events: none;
}

.btn-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>

