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

const members = ref([])
const loading = ref(true)
const error = ref(null)

const fetchMembers = async () => {
  if (!props.leagueCode) return
  
  loading.value = true
  error.value = null
  
  try {
    members.value = await api.getMembers(props.leagueCode)
    hapticFeedback('success')
  } catch (err) {
    error.value = 'خطا در دریافت اعضا'
    console.error('Members error:', err)
    hapticFeedback('error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchMembers)
watch(() => props.leagueCode, fetchMembers)

const getInitials = (name) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

const getAvatarColor = (name) => {
  const colors = [
    'linear-gradient(135deg, #667eea, #764ba2)',
    'linear-gradient(135deg, #f093fb, #f5576c)',
    'linear-gradient(135deg, #4facfe, #00f2fe)',
    'linear-gradient(135deg, #43e97b, #38f9d7)',
    'linear-gradient(135deg, #fa709a, #fee140)',
    'linear-gradient(135deg, #a8edea, #fed6e3)',
    'linear-gradient(135deg, #5ee7df, #b490ca)',
    'linear-gradient(135deg, #d299c2, #fef9d7)'
  ]
  const index = name ? name.charCodeAt(0) % colors.length : 0
  return colors[index]
}

const getAnimationDelay = (index) => {
  return `${index * 0.03}s`
}
</script>

<template>
  <div class="members-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>در حال بارگذاری...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">😕</div>
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchMembers">
        تلاش مجدد
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="members.length === 0" class="empty-state">
      <div class="empty-icon">👥</div>
      <p class="empty-text">هنوز هیچ عضوی در لیگ نیست</p>
    </div>

    <!-- Members Count -->
    <div v-else class="members-header">
      <span class="members-count">👥 {{ members.length }} عضو</span>
    </div>

    <!-- Members Grid -->
    <div v-if="members.length > 0" class="members-grid">
      <div
        v-for="(member, index) in members"
        :key="member.telegram_id"
        class="member-card"
        :class="{ 'is-me': member.telegram_id === userId }"
        :style="{ animationDelay: getAnimationDelay(index) }"
      >
        <div 
          class="member-avatar"
          :style="{ background: getAvatarColor(member.name) }"
        >
          {{ getInitials(member.name) }}
        </div>
        <div class="member-name">
          {{ member.name }}
          <span v-if="member.telegram_id === userId" class="me-indicator">👤</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.members-view {
  padding-bottom: 20px;
}

.members-header {
  text-align: center;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
}

.members-count {
  font-weight: 600;
  color: var(--text-secondary);
}

.member-card.is-me {
  border: 2px solid var(--primary);
  box-shadow: var(--shadow-glow);
}

.me-indicator {
  margin-right: 4px;
  font-size: 0.85rem;
}

.member-avatar {
  width: 56px;
  height: 56px;
  font-size: 1.5rem;
}
</style>

