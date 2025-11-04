<template>
  <div class="plan-detail">
    <!-- 行程头部信息 -->
    <div class="plan-header">
      <div class="header-main">
        <h2 class="plan-title">{{ plan.title }}</h2>
        <div class="plan-meta">
          <el-tag type="primary">{{ plan.days_count }}天</el-tag>
          <el-tag type="success">{{ plan.activities_count }}个活动</el-tag>
          <el-tag type="info">创建于 {{ formatDate(plan.created_at) }}</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Download"
          @click="downloadPlan"
          :loading="downloading"
        >
          下载Word文档
        </el-button>
        <el-button
          type="default"
          :icon="Printer"
          @click="printPlan"
        >
          打印行程
        </el-button>
      </div>
    </div>

    <!-- 行程描述 -->
    <div v-if="plan.description" class="plan-description">
      <p>{{ plan.description }}</p>
    </div>

    <!-- 天数导航 -->
    <div class="days-navigation" v-if="plan.itinerary && plan.itinerary.length > 0">
      <el-tabs v-model="activeDay" type="card">
        <el-tab-pane
          v-for="day in plan.itinerary"
          :key="day.day"
          :name="`day-${day.day}`"
        >
          <template #label>
            <span class="tab-label">
              第 {{ day.day }} 天
              <span class="day-date" v-if="day.date">
                ({{ formatDayDate(day.date) }})
              </span>
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 行程内容 -->
    <div class="plan-content">
      <div
        v-for="day in plan.itinerary"
        :key="day.day"
        v-show="activeDay === `day-${day.day}`"
        class="day-section"
      >
        <!-- 天头部 -->
        <div class="day-header">
          <h3 class="day-title">
            第 {{ day.day }} 天
            <span class="day-date" v-if="day.date">
              - {{ formatDayDate(day.date) }}
            </span>
          </h3>
          <div class="day-stats">
            <span class="stat-item">
              <span class="stat-icon">🎯</span>
              {{ day.items?.length || 0 }} 个活动
            </span>
          </div>
        </div>

        <!-- 活动列表 -->
        <div class="activities-list" v-if="day.items && day.items.length > 0">
          <div
            v-for="(item, index) in day.items"
            :key="item.id || index"
            :class="['activity-item', getItemTypeClass(item.type)]"
          >
            <!-- 活动时间 -->
            <div class="activity-time" v-if="item.startTime || item.time">
              <span class="time-badge">
                {{ formatTimeDisplay(item) }}
              </span>
            </div>

            <!-- 活动内容 -->
            <div class="activity-content">
              <!-- 图标和标题 -->
              <div class="activity-header">
                <span class="activity-icon">{{ getItemIcon(item.type) }}</span>
                <h4 class="activity-title">{{ item.name }}</h4>
                <el-tag
                  v-if="item.type"
                  :type="getTagType(item.type)"
                  size="small"
                  effect="plain"
                >
                  {{ getItemTypeText(item.type) }}
                </el-tag>
              </div>

              <!-- 地址信息 -->
              <p class="activity-address" v-if="item.details || item.address">
                📍 {{ item.details || item.address }}
              </p>

              <!-- 路径规划信息 -->
              <div v-if="item.type === 'route-planning'" class="route-info">
                <p class="route-points">
                  🚗 从 <strong>{{ item.startPoint }}</strong> 到 <strong>{{ item.endPoint }}</strong>
                </p>
                <div class="route-meta">
                  <span class="meta-item">⏱️ {{ item.duration }}</span>
                  <span class="meta-item">📏 {{ item.distance }}</span>
                  <span class="meta-item" v-if="item.cost && item.cost !== '0'">
                    💰 ¥{{ item.cost }}
                  </span>
                  <span class="meta-item">
                    {{ getTransportText(item.transportMode) }}
                  </span>
                </div>

                <!-- 路线步骤 -->
                <div v-if="item.steps && item.steps.length > 0" class="route-steps">
                  <el-collapse>
                    <el-collapse-item title="查看详细路线">
                      <div
                        v-for="(step, stepIndex) in item.steps"
                        :key="stepIndex"
                        class="route-step"
                      >
                        <span class="step-number">{{ stepIndex + 1 }}</span>
                        <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                        <span class="step-text">{{ step.instruction }}</span>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>

              <!-- 备注信息 -->
              <div v-if="item.note" class="activity-note">
                <p class="note-content">
                  <span class="note-icon">📝</span>
                  {{ item.note }}
                </p>
              </div>

              <!-- 其他信息 -->
              <div class="activity-meta" v-if="showActivityMeta(item)">
                <span class="meta-item" v-if="item.duration && item.type !== 'route-planning'">
                  时长: {{ item.duration }}
                </span>
                <span class="meta-item" v-if="item.tel">
                  电话: {{ item.tel }}
                </span>
                <span class="meta-item" v-if="item.website">
                  网站: {{ item.website }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="day-empty">
          <el-empty description="这一天还没有安排活动" :image-size="80" />
        </div>
      </div>

      <!-- 没有行程数据 -->
      <div v-if="!plan.itinerary || plan.itinerary.length === 0" class="no-itinerary">
        <el-empty description="暂无行程数据" :image-size="100" />
      </div>
    </div>

    <!-- 行程统计 -->
    <div class="plan-statistics" v-if="plan.itinerary && plan.itinerary.length > 0">
      <h4>📊 行程统计</h4>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ totalActivities }}</div>
          <div class="stat-label">总活动数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ totalDays }}</div>
          <div class="stat-label">总天数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ attractionCount }}</div>
          <div class="stat-label">景点数量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ restaurantCount }}</div>
          <div class="stat-label">餐厅数量</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Printer } from '@element-plus/icons-vue'

// 定义props
const props = defineProps({
  plan: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 定义emits
const emit = defineEmits(['close'])

// 响应式数据
const activeDay = ref('day-1')
const downloading = ref(false)

// 计算属性
const totalActivities = computed(() => {
  if (!props.plan.itinerary) return 0
  return props.plan.itinerary.reduce((total, day) => total + (day.items?.length || 0), 0)
})

const totalDays = computed(() => {
  return props.plan.itinerary?.length || 0
})

const attractionCount = computed(() => {
  return countItemsByType('attraction')
})

const restaurantCount = computed(() => {
  return countItemsByType('restaurant')
})

// 方法
const countItemsByType = (type) => {
  if (!props.plan.itinerary) return 0
  let count = 0
  props.plan.itinerary.forEach(day => {
    if (day.items) {
      count += day.items.filter(item => item.type === type).length
    }
  })
  return count
}

const downloadPlan = async () => {
  downloading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:5000/api/plans/${props.plan.id}/download`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${props.plan.title}.docx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('下载成功！')
    } else {
      throw new Error('下载失败')
    }
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败，请重试')
  } finally {
    downloading.value = false
  }
}

const printPlan = () => {
  window.print()
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const formatDayDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short'
  })
}

const formatTimeDisplay = (item) => {
  if (item.startTime && item.endTime) {
    return `${item.startTime}-${item.endTime}`
  } else if (item.time) {
    return item.time
  }
  return '时间待定'
}

const getItemTypeClass = (type) => {
  const classes = {
    attraction: 'type-attraction',
    restaurant: 'type-restaurant',
    hotel: 'type-hotel',
    route: 'type-route',
    'route-planning': 'type-route-planning'
  }
  return classes[type] || ''
}

const getItemIcon = (type) => {
  const icons = {
    attraction: '🗺️',
    restaurant: '🍽️',
    hotel: '🏨',
    route: '🛣️',
    'route-planning': '🚗'
  }
  return icons[type] || '📍'
}

const getItemTypeText = (type) => {
  const typeMap = {
    'attraction': '景点',
    'restaurant': '餐厅',
    'hotel': '酒店',
    'route': '路程',
    'route-planning': '行程'
  }
  return typeMap[type] || '活动'
}

const getTagType = (type) => {
  const types = {
    'attraction': 'primary',
    'restaurant': 'success',
    'hotel': 'warning',
    'route': 'info',
    'route-planning': 'danger'
  }
  return types[type] || 'info'
}

const getTransportText = (mode) => {
  const modes = {
    'transit': '公交',
    'driving': '驾车',
    'walking': '步行'
  }
  return modes[mode] || '交通'
}

const getStepIcon = (type) => {
  const icons = {
    walking: '🚶',
    bus: '🚌',
    driving: '🚗',
    subway: '🚇'
  }
  return icons[type] || '📍'
}

const showActivityMeta = (item) => {
  return item.duration || item.tel || item.website
}

// 初始化
onMounted(() => {
  if (props.plan.itinerary && props.plan.itinerary.length > 0) {
    activeDay.value = `day-${props.plan.itinerary[0].day}`
  }
})
</script>

<style scoped>
.plan-detail {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.header-main .plan-title {
  margin: 0 0 12px 0;
  font-size: 24px;
  color: #303133;
  font-weight: 600;
}

.plan-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.plan-description {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.plan-description p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.days-navigation {
  margin-bottom: 24px;
}

.plan-content {
  min-height: 400px;
}

.day-section {
  animation: fadeIn 0.3s ease-in;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

.day-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

.day-date {
  color: #409eff;
  font-size: 16px;
  font-weight: normal;
}

.day-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 14px;
}

.stat-icon {
  font-size: 16px;
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.activity-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.activity-time {
  flex-shrink: 0;
  width: 100px;
}

.time-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #409eff;
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.activity-icon {
  font-size: 20px;
}

.activity-title {
  margin: 0;
  font-size: 16px;
  color: #303133;
  font-weight: 600;
  flex: 1;
  min-width: 0;
}

.activity-address {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.route-info {
  margin-bottom: 12px;
}

.route-points {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.route-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.meta-item {
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.route-steps {
  margin-top: 12px;
}

.route-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.step-number {
  width: 20px;
  height: 20px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}

.step-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.step-text {
  flex: 1;
  font-size: 13px;
  line-height: 1.4;
  color: #606266;
}

.activity-note {
  margin: 12px 0;
  padding: 12px;
  background: #fdf6ec;
  border-radius: 6px;
  border-left: 3px solid #e6a23c;
}

.note-content {
  margin: 0;
  color: #e6a23c;
  font-size: 14px;
  line-height: 1.5;
}

.note-icon {
  margin-right: 6px;
}

.activity-meta {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.day-empty {
  padding: 40px 0;
}

.no-itinerary {
  padding: 60px 0;
  text-align: center;
}

.plan-statistics {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.plan-statistics h4 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-card {
  padding: 20px;
  background: white;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

/* 类型颜色 */
.type-attraction { border-left-color: #409eff; }
.type-restaurant { border-left-color: #67c23a; }
.type-hotel { border-left-color: #e6a23c; }
.type-route { border-left-color: #909399; }
.type-route-planning { border-left-color: #f56c6c; }

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .plan-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .activity-item {
    flex-direction: column;
    gap: 12px;
  }

  .activity-time {
    width: auto;
    text-align: left;
  }

  .route-meta {
    flex-direction: column;
    gap: 6px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 打印样式 */
@media print {
  .header-actions {
    display: none;
  }

  .activity-item {
    break-inside: avoid;
    box-shadow: none;
    border: 1px solid #ddd;
  }
}
</style>
