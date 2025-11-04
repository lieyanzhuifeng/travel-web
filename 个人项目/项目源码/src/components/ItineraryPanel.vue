<template>
  <div class="itinerary-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        📅 行程计划
      </h3>
    </div>

    <!-- 天数页签 -->
    <div class="days-tabs" v-if="itinerary.length > 0">
      <el-tabs v-model="activeDay" type="card" @tab-click="handleTabClick">
        <el-tab-pane
          v-for="(day, index) in itinerary"
          :key="day.day"
          :name="`day-${day.day}`"
        >
          <template #label>
            <span class="tab-label">
              第 {{ day.day }} 天
              <el-icon
                v-if="index === itinerary.length - 1"
                class="add-day-icon"
                @click.stop="addDay"
              >
                <Plus />
              </el-icon>
            </span>
          </template>

          <!-- 修改 day-header 部分 -->
          <div class="day-header">
  <div class="day-info">
    <span class="day-title">第 {{ day.day }} 天</span>
    <el-date-picker
      v-model="day.date"
      type="date"
      placeholder="选择日期"
      size="small"
      style="width: 140px; margin-left: 10px;"
      @change="(date) => handleDateChange(date, index)"
    />
    <!-- 添加排序按钮 -->
    <el-button
      class="sort-btn"
      type="primary"
      link
      :icon="Sort"
      @click="sortDayItems(index)"
      size="small"
      title="按时间排序"
    >
      排序
    </el-button>
    <!-- 添加显示地图按钮 -->
    <el-button
      class="map-show-btn"
      type="success"
      link
      :icon="MapLocation"
      @click="showDayActivitiesOnMap(index)"
      size="small"
      title="在地图上显示这天所有活动"
    >
      显示在地图
    </el-button>
  </div>
  <div class="day-actions">
    <el-button
      v-if="itinerary.length > 1"
      type="danger"
      link
      :icon="Delete"
      @click="removeDay(index)"
      size="small"
    >
      删除这天
    </el-button>
    <!-- 可选：添加清除地图标记按钮 -->
    <el-button
      class="clear-map-btn"
      type="warning"
      link
      :icon="Close"
      @click="clearMapMarkers"
      size="small"
      title="清除地图标记"
    >
      清除标记
    </el-button>
  </div>
</div>

          <!-- 行程项目列表 -->
          <div class="day-content">
            <div :class="['items-container', `day-${index}`]">
              <!-- 修改行程项目的点击事件，排除时间区域 -->
              <div
  v-for="(item, itemIndex) in day.items"
  :key="item.id"
  :class="['itinerary-item', getItemTypeClass(item.type), { 'dragging': draggingItemId === item.id }]"
  :data-item-id="item.id"
>
  <!-- 拖拽手柄 -->
  <div class="drag-handle" title="拖拽排序" @mousedown.stop>
    <el-icon><More /></el-icon>
  </div>

  <!-- 项目图标 -->
  <el-icon :size="20" class="item-icon" @click.stop="viewOnMap(item)">
    <component :is="getItemIcon(item.type)" />
  </el-icon>

  <!-- 项目详情 - 这里需要特殊处理点击事件 -->
  <div class="item-details" @click="handleItemClick(item, $event)">
    <div class="item-main">
      <p class="item-name">{{ item.name }}</p>
      <!-- 时间显示区域（已经阻止冒泡） -->
      <div
        class="time-display-container"
        @mouseenter="showEditButton = item.id"
        @mouseleave="showEditButton = null"
      >
        <div
          class="time-display"
          @click.stop="openTimeEditor(day.day, itemIndex)"
          @mousedown.stop
        >
          {{ formatTimeDisplay(item) }}
        </div>
        <el-button
          v-if="showEditButton === item.id"
          class="edit-time-btn"
          type="primary"
          link
          :icon="Edit"
          @click.stop="openTimeEditor(day.day, itemIndex)"
          @mousedown.stop
          size="small"
          title="修改时间"
        />
      </div>
    </div>
    <p class="item-address">{{ item.details }}</p>
  </div>

  <!-- 修改操作按钮部分 -->
  <div class="item-actions">
  <!-- 修改：将编辑按钮改为添加备注按钮 -->
  <el-button
    type="info"
    link
    :icon="Edit"
    @click.stop="addNote(day.day, itemIndex)"
    size="small"
    title="添加备注"
  />
  <el-button
    type="danger"
    link
    :icon="Delete"
    @click.stop="deleteItem(index, itemIndex)"
    size="small"
    title="删除"
  />
</div>
</div>

              <!-- 添加项目按钮 -->
              <div class="add-item-section">
                <el-button
                  type="primary"
                  plain
                  :icon="Plus"
                  class="add-item-btn"
                  @click="openRoutePlanning(index)"
                >
                  添加行程
                </el-button>
              </div>

              <!-- 统计信息 -->
              <div class="day-stats">
                <el-tag size="small" type="info">
                  {{ getStats(day) }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="暂无行程计划" :image-size="100">
        <el-button type="primary" :icon="Plus" @click="addDay">
          开始规划行程
        </el-button>
      </el-empty>
    </div>

    <!-- 备注编辑器模态框 - 简化版 -->
    <el-dialog
  v-model="noteEditorVisible"
  title="📝 添加备注"
  width="500px"
  :before-close="handleNoteEditorClose"
>
  <div class="note-editor-dialog">
    <div class="note-header">
      <h4>{{ noteEditingData.itemName }}</h4>
      <p class="item-type">{{ getItemTypeText(noteEditingData.itemType) }}</p>
    </div>

    <div class="note-input-section">
      <el-input
        v-model="noteEditingData.note"
        type="textarea"
        :rows="8"
        placeholder="请输入备注内容..."
        maxlength="500"
        show-word-limit
        resize="none"
      />
    </div>
  </div>

  <template #footer>
    <el-button @click="handleNoteEditorClose">取消</el-button>
    <el-button
      type="primary"
      :disabled="!noteEditingData.note?.trim()"
      @click="saveNote"
    >
      保存备注
    </el-button>
  </template>
</el-dialog>

    <!-- 路径规划模态框 -->
    <el-dialog
      v-model="routePlanningVisible"
      title="🗺️ 路径规划"
      width="700px"
      :before-close="handleRoutePlanningClose"
    >
      <div class="route-planning-dialog">
        <!-- 起点终点选择 -->
        <div class="route-inputs">
          <div class="input-group">
            <label>📍 起点</label>
            <el-select
              v-model="routePlanningData.startPoint"
              placeholder="选择起点"
              clearable
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="location in availableLocations"
                :key="location.id"
                :label="location.name"
                :value="location.name"
              />
            </el-select>
          </div>

          <div class="input-group">
            <label>🎯 终点</label>
            <el-select
              v-model="routePlanningData.endPoint"
              placeholder="选择终点"
              clearable
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="location in availableLocations"
                :key="location.id"
                :label="location.name"
                :value="location.name"
              />
            </el-select>
          </div>
        </div>

        <!-- 规划按钮 -->
        <div class="plan-actions">
          <el-button @click="handleRoutePlanningClose">取消</el-button>
          <el-button
            type="primary"
            :loading="planningLoading"
            :disabled="!routePlanningData.startPoint || !routePlanningData.endPoint"
            @click="handlePlanRoute"
          >
            {{ planningLoading ? '规划中...' : '开始规划' }}
          </el-button>
        </div>

        <!-- 路线结果展示区域 -->
        <div v-if="routeResult && (routeResult.transit || routeResult.driving || routeResult.walking)" class="route-result">
          <h4>📊 路线方案</h4>

          <!-- 交通方式标签页 -->
          <div class="transport-tabs">
            <el-tabs v-model="selectedTransportMode">
              <el-tab-pane label="🚌 公交" name="transit" :disabled="!routeResult.transit">
                <div v-if="routeResult.transit" class="route-options">
                  <el-card
                    v-for="(plan, index) in routeResult.transit.plans"
                    :key="index"
                    class="route-plan-card"
                    :class="{ active: selectedPlanIndex === index }"
                    @click="selectedPlanIndex = index"
                  >
                    <div class="plan-header">
                      <span class="plan-title">方案 {{ index + 1 }}</span>
                      <el-tag type="success">{{ plan.duration }}分钟</el-tag>
                    </div>
                    <div class="plan-details">
                      <p>💰 费用: ¥{{ plan.cost }}</p>
                      <p>🚶 步行: {{ plan.walkingDistance }}米</p>
                      <p>📏 距离: {{ plan.distance }}米</p>
                    </div>
                    <div class="plan-steps">
                      <div
                        v-for="(step, stepIndex) in plan.steps"
                        :key="stepIndex"
                        class="plan-step"
                      >
                        <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                        <span class="step-text">{{ step.instruction }}</span>
                      </div>
                    </div>
                  </el-card>
                </div>
                <div v-else class="no-result">暂无公交方案</div>
              </el-tab-pane>

              <el-tab-pane label="🚗 驾车" name="driving" :disabled="!routeResult.driving">
                <div v-if="routeResult.driving" class="route-options">
                  <el-card
                    v-for="(plan, index) in routeResult.driving.plans"
                    :key="index"
                    class="route-plan-card"
                    :class="{ active: selectedPlanIndex === index }"
                    @click="selectedPlanIndex = index"
                  >
                    <div class="plan-header">
                      <span class="plan-title">方案 {{ index + 1 }}</span>
                      <el-tag type="success">{{ plan.duration }}分钟</el-tag>
                    </div>
                    <div class="plan-details">
                      <p>💰 费用: ¥{{ plan.cost }}</p>
                      <p>🚶 步行: {{ plan.walkingDistance }}米</p>
                      <p>📏 距离: {{ plan.distance }}米</p>
                    </div>
                    <div class="plan-steps">
                      <div
                        v-for="(step, stepIndex) in plan.steps"
                        :key="stepIndex"
                        class="plan-step"
                      >
                        <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                        <span class="step-text">{{ step.instruction }}</span>
                      </div>
                    </div>
                  </el-card>
                </div>
                <div v-else class="no-result">暂无驾车方案</div>
              </el-tab-pane>

              <el-tab-pane label="🚶 步行" name="walking" :disabled="!routeResult.walking">
                <div v-if="routeResult.walking" class="route-options">
                  <el-card
                    v-for="(plan, index) in routeResult.walking.plans"
                    :key="index"
                    class="route-plan-card"
                    :class="{ active: selectedPlanIndex === index }"
                    @click="selectedPlanIndex = index"
                  >
                    <div class="plan-header">
                      <span class="plan-title">方案 {{ index + 1 }}</span>
                      <el-tag type="success">{{ plan.duration }}分钟</el-tag>
                    </div>
                    <div class="plan-details">
                      <p>💰 费用: ¥{{ plan.cost }}</p>
                      <p>🚶 步行: {{ plan.walkingDistance }}米</p>
                      <p>📏 距离: {{ plan.distance }}米</p>
                    </div>
                    <div class="plan-steps">
                      <div
                        v-for="(step, stepIndex) in plan.steps"
                        :key="stepIndex"
                        class="plan-step"
                      >
                        <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                        <span class="step-text">{{ step.instruction }}</span>
                      </div>
                    </div>
                  </el-card>
                </div>
                <div v-else class="no-result">暂无步行方案</div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- 保存按钮 -->
          <div class="save-actions">
            <el-button
              type="success"
              @click="saveRouteToItinerary"
              :disabled="!routeResult[selectedTransportMode]"
            >
              💾 保存到行程
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 时间编辑器模态框 -->
    <el-dialog
  v-model="timeEditorVisible"
  title="🕐 设置时间"
  width="400px"
  :before-close="handleTimeEditorClose"
>
  <div class="time-editor-dialog">
    <div class="time-inputs">
      <div class="time-input-group">
        <label>开始时间</label>
        <el-time-select
          v-model="timeEditingData.startTime"
          placeholder="选择开始时间"
          :max-time="timeEditingData.endTime"
          start="06:00"
          step="00:15"
          end="23:45"
          style="width: 100%"
        />
      </div>

      <div class="time-input-group">
        <label>结束时间</label>
        <el-time-select
          v-model="timeEditingData.endTime"
          placeholder="选择结束时间"
          :min-time="timeEditingData.startTime"
          start="06:00"
          step="00:15"
          end="23:45"
          style="width: 100%"
        />
      </div>
    </div>

    <div class="time-preview">
      <p class="preview-text">
        时间段：<span class="preview-time">{{ formatTimeRange() }}</span>
      </p>
      <p class="duration-text" v-if="timeEditingData.startTime && timeEditingData.endTime">
        时长：<span class="duration">{{ calculateDuration() }}</span>
      </p>
    </div>

    <div class="quick-times" v-if="!timeEditingData.startTime && !timeEditingData.endTime">
      <p class="quick-title">快速选择：</p>
      <div class="quick-buttons">
        <el-button
          v-for="timeSlot in quickTimeSlots"
          :key="timeSlot.label"
          size="small"
          @click="setQuickTime(timeSlot)"
        >
          {{ timeSlot.label }}
        </el-button>
      </div>
    </div>
  </div>

  <template #footer>
    <el-button @click="handleTimeEditorClose">取消</el-button>
    <el-button
      type="primary"
      :disabled="!timeEditingData.startTime || !timeEditingData.endTime"
      @click="saveTime"
    >
      保存时间
    </el-button>
  </template>
</el-dialog>

    <!-- 路线详情模态框 -->
    <el-dialog
      v-model="routeDetailVisible"
      title="🗺️ 路线详情"
      width="600px"
    >
      <div class="route-detail-dialog" v-if="selectedRouteItem">
        <div class="route-overview">
          <h4>📍 {{ selectedRouteItem.startPoint }} → 🎯 {{ selectedRouteItem.endPoint }}</h4>
          <div class="route-meta">
            <el-tag type="success">{{ selectedRouteItem.duration }}</el-tag>
            <el-tag type="info">{{ selectedRouteItem.distance }}</el-tag>
            <el-tag type="warning">
              {{ selectedRouteItem.transportMode === 'transit' ? '公交' : selectedRouteItem.transportMode === 'driving' ? '驾车' : '步行' }}
            </el-tag>
            <el-tag v-if="selectedRouteItem.cost && selectedRouteItem.cost !== '0'" type="danger">
              💰 ¥{{ selectedRouteItem.cost }}
            </el-tag>
          </div>
        </div>

        <div class="route-steps">
          <h5>📋 行程步骤：</h5>
          <div class="steps-container">
            <div
              v-for="(step, index) in selectedRouteItem.steps"
              :key="index"
              class="route-step"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                <span class="step-text">{{ step.instruction }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="routeDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, defineEmits, defineExpose, inject } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sortable from 'sortablejs'
import {
  Delete,
  Location,
  Food,
  OfficeBuilding,
  Road,
  Plus,
  Edit,
  ArrowUp,
  ArrowDown,
  MapLocation,
  More,
  Sort,
  Close  // 添加这行
} from '@element-plus/icons-vue'

// 注入地图引用
const mapRef = inject('mapRef')

// 行程数据 - 默认包含第一天
const itinerary = reactive([{
  day: 1,
  date: new Date(),
  items: []
}])
const activeDay = ref('day-1')

// 路径规划相关状态
const routePlanningVisible = ref(false)
const planningLoading = ref(false)
const routeResult = ref({
  transit: null,
  driving: null,
  walking: null
})
const selectedPlanIndex = ref(0)
const selectedTransportMode = ref('transit')
const routePlanningData = ref({
  startPoint: '',
  endPoint: '',
  startPosition: null,
  endPosition: null,
  dayIndex: 0
})
// 在现有的响应式数据后面添加
const noteEditorVisible = ref(false)
const noteEditingData = ref({
  dayIndex: 0,
  itemIndex: 0,
  itemName: '',
  itemType: '',
  note: ''
})

// 添加备注方法
const addNote = (dayNumber, itemIndex) => {
  const dayIndex = itinerary.findIndex(d => d.day === dayNumber)
  if (dayIndex === -1) return

  const item = itinerary[dayIndex].items[itemIndex]

  noteEditingData.value = {
    dayIndex,
    itemIndex,
    itemName: item.name,
    itemType: item.type,
    note: item.note || '' // 如果已有备注，显示原有内容
  }

  noteEditorVisible.value = true
}

// 保存备注
const saveNote = () => {
  const { dayIndex, itemIndex, note } = noteEditingData.value

  if (itinerary[dayIndex] && itinerary[dayIndex].items[itemIndex]) {
    itinerary[dayIndex].items[itemIndex].note = note.trim()

    ElMessage.success('备注保存成功')
    noteEditorVisible.value = false
  }
}

// 关闭备注编辑器
const handleNoteEditorClose = () => {
  noteEditorVisible.value = false
  // 重置数据
  setTimeout(() => {
    noteEditingData.value = {
      dayIndex: 0,
      itemIndex: 0,
      itemName: '',
      itemType: '',
      note: ''
    }
  }, 300)
}

// 获取项目类型文本
const getItemTypeText = (type) => {
  const typeMap = {
    'attraction': '景点',
    'restaurant': '餐厅',
    'hotel': '酒店',
    'route': '路程',
    'route-planning': '行程规划'
  }
  return typeMap[type] || '活动'
}
// 在现有的响应式数据后面添加
const showEditButton = ref(null) // 跟踪显示编辑按钮的项目ID
const timeEditorVisible = ref(false)
const timeEditingData = ref({
  dayIndex: 0,
  itemIndex: 0,
  startTime: '',
  endTime: ''
})

// 快速时间段选项
const quickTimeSlots = [
  { label: '上午 (09:00-12:00)', start: '09:00', end: '12:00' },
  { label: '中午 (12:00-14:00)', start: '12:00', end: '14:00' },
  { label: '下午 (14:00-18:00)', start: '14:00', end: '18:00' },
  { label: '晚上 (18:00-21:00)', start: '18:00', end: '21:00' }
]

// 格式化时间显示
const formatTimeDisplay = (item) => {
  if (item.startTime && item.endTime) {
    return `${item.startTime}-${item.endTime}`
  }
  return '点击设置时间'
}



// 路线详情相关状态
const routeDetailVisible = ref(false)
const selectedRouteItem = ref(null)

// 拖拽相关状态
const draggingItemId = ref(null)
let sortableInstances = new Map()

// 计算当前天的所有可用地点 - 过滤掉路径规划项目
const availableLocations = computed(() => {
  const dayMatch = activeDay.value.match(/day-(\d+)/)
  if (!dayMatch) return []

  const dayIndex = parseInt(dayMatch[1]) - 1
  const currentDay = itinerary[dayIndex]

  if (!currentDay || !currentDay.items) return []

  return currentDay.items
    .filter(item =>
      item.name &&
      item.name.trim() &&
      item.type !== 'route-planning'
    )
    .map(item => ({
      id: item.id,
      name: item.name,
      address: item.details,
      type: item.type
    }))
})

// 公共函数：选择天数
const selectDay = async (title = '选择天数') => {
  if (itinerary.length === 0) {
    addDay()
  }

  const dayMatch = activeDay.value.match(/day-(\d+)/)
  if (dayMatch) {
    return parseInt(dayMatch[1]) - 1
  }

  return itinerary.length - 1
}

// 显示当天的所有活动标记
const showDayActivitiesOnMap = (dayIndex) => {
  if (!mapRef?.value) return

  const day = itinerary[dayIndex]
  if (!day || !day.items.length) return

  const activities = day.items.filter(item =>
    item.lng && item.lat && item.type !== 'route-planning'
  )

  if (activities.length > 0) {
    mapRef.value.showMultipleActivities(activities)
    ElMessage.success(`在地图上显示了 ${activities.length} 个活动`)
  } else {
    ElMessage.warning('该天没有可在地图显示的活动')
  }
}

// 显示单个活动
const showActivityOnMap = (activity) => {
  if (!mapRef?.value) return
  mapRef.value.showActivityOnMap(activity)
}

// 清除所有标记
const clearMapMarkers = () => {
  if (!mapRef?.value) return
  mapRef.value.removeAllMarkers()
}










// 添加新的一天
const addDay = () => {
  const newDayNumber = itinerary.length + 1

  let newDate = new Date()
  if (itinerary.length > 0) {
    const lastDay = itinerary[itinerary.length - 1]
    newDate = new Date(lastDay.date)
    newDate.setDate(newDate.getDate() + 1)
  }

  const newDay = {
    day: newDayNumber,
    date: newDate,
    items: []
  }

  itinerary.push(newDay)
  activeDay.value = `day-${newDayNumber}`

  ElMessage.success(`已添加第 ${newDayNumber} 天`)
}

// 删除一天
const removeDay = async (index) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除第 ${itinerary[index].day} 天的行程吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    itinerary.splice(index, 1)

    if (itinerary.length > 0) {
      activeDay.value = `day-${itinerary[itinerary.length - 1].day}`
    }

    ElMessage.success('删除成功')
  } catch {
    // 用户取消删除
  }
}

// 处理日期变化
const handleDateChange = (newDate, dayIndex) => {
  if (!newDate) return

  itinerary[dayIndex].date = newDate

  for (let i = dayIndex + 1; i < itinerary.length; i++) {
    const prevDate = new Date(itinerary[i - 1].date)
    const nextDate = new Date(prevDate)
    nextDate.setDate(nextDate.getDate() + 1)
    itinerary[i].date = nextDate
  }
}

// 标签切换
const handleTabClick = (tab) => {
  console.log('切换到:', tab.props.name)
}

// 初始化拖拽
const initSortable = (dayIndex, container) => {
  console.log(`🔄 初始化拖拽: 第${dayIndex + 1}天`, container)

  if (!container) {
    console.error('❌ 容器为空，无法初始化拖拽')
    return
  }

  // 检查是否已经存在实例
  const existingInstance = sortableInstances.get(dayIndex)
  if (existingInstance) {
    console.log(`⚠️ 第${dayIndex + 1}天已存在拖拽实例，先销毁`)
    try {
      existingInstance.destroy()
    } catch (error) {
      console.warn(`销毁已存在实例时出错:`, error)
    }
  }

  try {
    const sortable = Sortable.create(container, {
      animation: 150,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      handle: '.drag-handle',
      filter: '.add-item-section, .day-stats',

      onStart: (evt) => {
        console.log('🚀 开始拖拽:', evt.oldIndex, evt.item.dataset.itemId)
        draggingItemId.value = evt.item.dataset.itemId
      },

      onEnd: (evt) => {
        console.log('🏁 结束拖拽:', evt.oldIndex, '->', evt.newIndex)
        draggingItemId.value = null

        const { oldIndex, newIndex } = evt

        if (oldIndex !== newIndex) {
          console.log(`🔄 移动项目: 从${oldIndex}到${newIndex}`)
          moveItemByDrag(dayIndex, oldIndex, newIndex)
        } else {
          console.log('📍 位置未改变')
        }
      },

      onChoose: (evt) => {
        console.log('🎯 选择项目:', evt.oldIndex)
      }
    })

    sortableInstances.set(dayIndex, sortable)
    console.log(`✅ 第${dayIndex + 1}天拖拽初始化成功`)

  } catch (error) {
    console.error('❌ 拖拽初始化失败:', error)
  }
}

// 修改 onMounted 中的选择器逻辑
onMounted(() => {
  console.log('🚀 ItineraryPanel 挂载，准备初始化拖拽')

  nextTick(() => {
    console.log('⏰ 等待DOM渲染完成')

    setTimeout(() => {
      console.log('🔄 开始初始化所有天的拖拽功能')
      console.log('📋 行程天数:', itinerary.length)

      itinerary.forEach((day, index) => {
        // 使用更精确的选择器
        const selector = `.items-container.day-${index}`
        console.log(`🔍 查找容器: ${selector}`)
        const container = document.querySelector(selector)

        if (container) {
          console.log(`✅ 找到第${index + 1}天的容器`, container)
          console.log(`📦 容器内项目数量:`, container.children.length)
          initSortable(index, container)
        } else {
          console.error(`❌ 未找到第${index + 1}天的容器`)

          // 延迟重试
          setTimeout(() => {
            const retryContainer = document.querySelector(selector)
            if (retryContainer) {
              console.log(`🔄 重试找到第${index + 1}天的容器`)
              initSortable(index, retryContainer)
            }
          }, 300)
        }
      })
    }, 500)
  })
})

// 通过拖拽移动项目
const moveItemByDrag = (dayIndex, fromIndex, toIndex) => {
  const items = itinerary[dayIndex].items
  const [movedItem] = items.splice(fromIndex, 1)
  items.splice(toIndex, 0, movedItem)
  ElMessage.success('顺序已更新')
}

// 组件挂载时初始化拖拽
onMounted(() => {
  console.log('🚀 ItineraryPanel 挂载，准备初始化拖拽')

  nextTick(() => {
    console.log('⏰ 等待DOM渲染完成')

    setTimeout(() => {
      console.log('🔄 开始初始化所有天的拖拽功能')
      console.log('📋 行程天数:', itinerary.length)

      itinerary.forEach((day, index) => {
        const selector = `.day-${index} .items-container`
        console.log(`🔍 查找容器: ${selector}`)
        const container = document.querySelector(selector)

        if (container) {
          console.log(`✅ 找到第${index + 1}天的容器`, container)
          console.log(`📦 容器内项目数量:`, container.children.length)
          initSortable(index, container)
        } else {
          console.error(`❌ 未找到第${index + 1}天的容器`)
          // 尝试其他选择器
          const alternativeSelectors = [
            `.items-container`,
            `[data-day="${index}"] .items-container`,
            `.el-tab-pane:nth-child(${index + 1}) .items-container`
          ]

          alternativeSelectors.forEach(altSelector => {
            const altContainer = document.querySelector(altSelector)
            if (altContainer) {
              console.log(`🔧 使用备选选择器找到容器: ${altSelector}`)
              initSortable(index, altContainer)
            }
          })
        }
      })
    }, 500) // 增加延迟确保DOM完全渲染
  })
})

// 组件卸载时销毁所有实例
onUnmounted(() => {
  sortableInstances.forEach(instance => {
    instance.destroy()
  })
  sortableInstances.clear()
})
// 处理项目点击事件
const handleItemClick = (item, event) => {
  // 检查点击的是否是时间区域
  const isTimeArea = event.target.closest('.time-display-container') ||
                    event.target.closest('.edit-time-btn') ||
                    event.target.classList.contains('time-display')

  if (isTimeArea) {
    // 如果是时间区域，不执行任何操作（因为时间区域已经有独立的事件处理）
    return
  }

  // 如果不是时间区域，执行原来的查看操作
  viewOnMap(item)
}

// 修改原有的 viewOnMap 函数，确保它不会在时间编辑时被调用
const viewOnMap = (item) => {
  // 如果正在编辑时间，不执行地图查看
  if (timeEditorVisible.value) {
    return
  }

  if (item.type === 'route-planning') {
    showRouteDetail(item)
  } else {
    ElMessage.info(`在地图上查看: ${item.name}`)

    if (mapRef?.value?.showActivityOnMap) {
      const activityData = {
        name: item.name,
        lng: item.lng || item.rawPoiData?.lng || item.rawPoiData?.location?.lng,
        lat: item.lat || item.rawPoiData?.lat || item.rawPoiData?.location?.lat,
        details: item.details,
        address: item.address
      }
      mapRef.value.showActivityOnMap(activityData)
    } else {
      console.error('❌ 地图组件未就绪')
    }
  }
}


// 显示路线详情
const showRouteDetail = (routeItem) => {
  selectedRouteItem.value = routeItem
  routeDetailVisible.value = true
}

// 打开路径规划模态框
const openRoutePlanning = async () => {
  try {
    const dayIndex = await selectDay()
    routePlanningData.value.dayIndex = dayIndex
    routePlanningVisible.value = true
  } catch (error) {
    if (error !== 'cancel') {
      console.log('用户取消选择')
    }
  }
}


// 修改 handlePlanRoute 方法，移除 apiKey 参数
const handlePlanRoute = async () => {
  planningLoading.value = true
  routeResult.value = { transit: null, driving: null, walking: null }

  try {
    const { startPoint, endPoint } = routePlanningData.value

    // 从可用地点中获取坐标信息
    const startLocation = getLocationCoordinates(startPoint)
    const endLocation = getLocationCoordinates(endPoint)

    if (!startLocation || !endLocation) {
      ElMessage.error('无法获取地点坐标信息')
      return
    }

    const origin = `${startLocation.lng},${startLocation.lat}`
    const destination = `${endLocation.lng},${endLocation.lat}`

    // 并行调用所有交通方式的API（现在调用自己的后端）
    const [transitResult, drivingResult, walkingResult] = await Promise.all([
      fetchTransitRoute(origin, destination),
      fetchDrivingRoute(origin, destination),
      fetchWalkingRoute(origin, destination)
    ])

    routeResult.value = {
      transit: transitResult,
      driving: drivingResult,
      walking: walkingResult
    }

    ElMessage.success('路线规划完成！请选择交通方式查看详情')

  } catch (error) {
    ElMessage.error('路线规划失败: ' + error.message)
  } finally {
    planningLoading.value = false
  }
}

// 根据地点名称获取坐标
const getLocationCoordinates = (locationName) => {
  const location = availableLocations.value.find(loc => loc.name === locationName)
  if (!location) return null

  const dayMatch = activeDay.value.match(/day-(\d+)/)
  if (!dayMatch) return null

  const dayIndex = parseInt(dayMatch[1]) - 1
  const currentDay = itinerary[dayIndex]
  const item = currentDay.items.find(item => item.id === location.id)

  if (item && item.lng && item.lat) {
    return { lng: item.lng, lat: item.lat }
  }

  return null
}

// 替换原来的 fetchTransitRoute、fetchDrivingRoute、fetchWalkingRoute 方法
const fetchTransitRoute = async (apiKey, origin, destination) => {
  try {
    const response = await fetch('/api/route/transit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        origin: origin,
        destination: destination
      })
    })

    const data = await response.json()
    return data.success ? data.data : null
  } catch {
    return null
  }
}

const fetchDrivingRoute = async (apiKey, origin, destination) => {
  try {
    const response = await fetch('/api/route/driving', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        origin: origin,
        destination: destination
      })
    })

    const data = await response.json()
    return data.success ? data.data : null
  } catch {
    return null
  }
}

const fetchWalkingRoute = async (apiKey, origin, destination) => {
  try {
    const response = await fetch('/api/route/walking', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        origin: origin,
        destination: destination
      })
    })

    const data = await response.json()
    return data.success ? data.data : null
  } catch {
    return null
  }
}

// 格式化路线结果
const formatRouteResult = (data, transportMode) => {
  if (transportMode === 'transit') {
    const transits = data.route.transits || []
    return {
      plans: transits.map((plan, index) => ({
        id: index,
        cost: plan.cost || '0',
        duration: Math.floor((plan.duration || 0) / 60),
        walkingDistance: plan.walking_distance || 0,
        distance: plan.distance || 0,
        steps: formatTransitSteps(plan.segments || [])
      }))
    }
  } else if (transportMode === 'driving') {
    const paths = data.route.paths || []
    return {
      plans: paths.map((path, index) => ({
        id: index,
        cost: '0',
        duration: Math.floor((path.duration || 0) / 60),
        walkingDistance: 0,
        distance: path.distance || 0,
        steps: formatDrivingSteps(path.steps || [])
      }))
    }
  } else {
    const paths = data.route.paths || []
    return {
      plans: paths.map((path, index) => ({
        id: index,
        cost: '0',
        duration: Math.floor((path.duration || 0) / 60),
        walkingDistance: path.distance || 0,
        distance: path.distance || 0,
        steps: formatWalkingSteps(path.steps || [])
      }))
    }
  }
}

// 格式化步骤
const formatTransitSteps = (segments) => {
  const steps = []
  segments.forEach(segment => {
    const walking = segment.walking
    if (walking && walking.distance) {
      steps.push({
        type: 'walking',
        instruction: `🚶 步行 ${walking.distance} 米`
      })
    }

    const bus = segment.bus
    if (bus && bus.buslines) {
      bus.buslines.forEach(line => {
        const name = line.name || ""
        const dep = line.departure_stop?.name || ""
        const arr = line.arrival_stop?.name || ""
        steps.push({
          type: 'bus',
          instruction: `🚌 乘坐 ${name}：${dep} → ${arr}`
        })
      })
    }
  })
  return steps
}

const formatDrivingSteps = (steps) => {
  return steps.map(step => ({
    type: 'driving',
    instruction: `🚗 ${step.instruction} (${step.distance}米)`
  }))
}

const formatWalkingSteps = (steps) => {
  return steps.map(step => ({
    type: 'walking',
    instruction: `🚶 ${step.instruction} (${step.distance}米)`
  }))
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

const saveRouteToItinerary = () => {
  if (!routeResult.value) return

  const currentResult = routeResult.value[selectedTransportMode.value]
  if (!currentResult || currentResult.plans.length === 0) return

  const selectedPlan = currentResult.plans[selectedPlanIndex.value]
  const dayIndex = routePlanningData.value.dayIndex

  const routeItem = {
    id: 'route_planning_' + Date.now(),
    type: 'route-planning',
    name: `从${routePlanningData.value.startPoint}到${routePlanningData.value.endPoint}`,
    startPoint: routePlanningData.value.startPoint,
    endPoint: routePlanningData.value.endPoint,
    transportMode: selectedTransportMode.value,
    duration: selectedPlan.duration + '分钟',
    distance: selectedPlan.distance + '米',
    cost: selectedPlan.cost,
    steps: selectedPlan.steps,
    time: '',
    details: `${selectedTransportMode.value === 'transit' ? '公交' : selectedTransportMode.value === 'driving' ? '驾车' : '步行'}路线`,
    editing: false
  }

  itinerary[dayIndex].items.push(routeItem)
  routePlanningVisible.value = false
  ElMessage.success('行程已添加到计划中')
}

const handleRoutePlanningClose = () => {
  routePlanningVisible.value = false
  routeResult.value = { transit: null, driving: null, walking: null }
  selectedTransportMode.value = 'transit'
  routePlanningData.value = {
    startPoint: '',
    endPoint: '',
    startPosition: null,
    endPosition: null,
    dayIndex: 0
  }
}

// 打开时间编辑器
const openTimeEditor = (dayNumber, itemIndex) => {
  const dayIndex = itinerary.findIndex(d => d.day === dayNumber)
  if (dayIndex === -1) return

  const item = itinerary[dayIndex].items[itemIndex]

  timeEditingData.value = {
    dayIndex,
    itemIndex,
    startTime: item.startTime || '',
    endTime: item.endTime || ''
  }

  timeEditorVisible.value = true
}

// 保存时间
const saveTime = () => {
  const { dayIndex, itemIndex, startTime, endTime } = timeEditingData.value

  if (itinerary[dayIndex] && itinerary[dayIndex].items[itemIndex]) {
    itinerary[dayIndex].items[itemIndex].startTime = startTime
    itinerary[dayIndex].items[itemIndex].endTime = endTime
    itinerary[dayIndex].items[itemIndex].time = `${startTime}-${endTime}`

    ElMessage.success('时间设置成功')
    timeEditorVisible.value = false
  }
}

// 格式化时间范围显示
const formatTimeRange = () => {
  const { startTime, endTime } = timeEditingData.value
  if (startTime && endTime) {
    return `${startTime} - ${endTime}`
  }
  return '请选择时间段'
}

// 计算时长
const calculateDuration = () => {
  const { startTime, endTime } = timeEditingData.value
  if (!startTime || !endTime) return ''

  const start = new Date(`2000/01/01 ${startTime}`)
  const end = new Date(`2000/01/01 ${endTime}`)
  const duration = (end - start) / (1000 * 60) // 分钟

  if (duration < 60) {
    return `${duration}分钟`
  } else {
    const hours = Math.floor(duration / 60)
    const minutes = duration % 60
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
}

// 设置快速时间
const setQuickTime = (timeSlot) => {
  timeEditingData.value.startTime = timeSlot.start
  timeEditingData.value.endTime = timeSlot.end
}

// 关闭时间编辑器
const handleTimeEditorClose = () => {
  timeEditorVisible.value = false
  // 重置数据
  setTimeout(() => {
    timeEditingData.value = {
      dayIndex: 0,
      itemIndex: 0,
      startTime: '',
      endTime: ''
    }
  }, 300)
}

// 修改原有的 editItem 方法（可选，可以保留或移除）
const editItem = (dayNumber, itemIndex) => {
  // 现在可以改为调用添加备注，或者保留原有的编辑名称功能
  // 这里我建议保留，让用户可以选择编辑名称或添加备注
  const day = itinerary.find(d => d.day === dayNumber)
  if (day && day.items[itemIndex]) {
    ElMessageBox.prompt('请输入新的名称', '编辑项目名称', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: day.items[itemIndex].name
    }).then(({ value }) => {
      if (value && value.trim()) {
        day.items[itemIndex].name = value.trim()
        ElMessage.success('更新成功')
      }
    }).catch(() => {
      // 取消编辑
    })
  }
}



// 删除项目
const deleteItem = async (dayIndex, itemIndex) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个项目吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    itinerary[dayIndex].items.splice(itemIndex, 1)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消删除
  }
}

// 获取统计信息
const getStats = (day) => {
  const attractions = day.items.filter(item => item.type === 'attraction').length
  const restaurants = day.items.filter(item => item.type === 'restaurant').length
  const hotels = day.items.filter(item => item.type === 'hotel').length
  const routes = day.items.filter(item => item.type === 'route').length
  const routePlannings = day.items.filter(item => item.type === 'route-planning').length

  const parts = []
  if (attractions > 0) parts.push(`${attractions}个景点`)
  if (restaurants > 0) parts.push(`${restaurants}个餐厅`)
  if (hotels > 0) parts.push(`${hotels}个酒店`)
  if (routes > 0) parts.push(`${routes}段路程`)
  if (routePlannings > 0) parts.push(`${routePlannings}个行程`)

  return parts.join(' · ') || '暂无活动'
}

// 图标和样式辅助函数
const getItemIcon = (type) => {
  const icons = {
    attraction: Location,
    restaurant: Food,
    hotel: OfficeBuilding,
    route: Road,
    'route-planning': MapLocation
  }
  return icons[type] || Location
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

const getPoiTypeClass = (poiTypeString) => {
  if (poiTypeString.includes('酒店') || poiTypeString.includes('住宿')) return 'hotel'
  if (poiTypeString.includes('餐饮') || poiTypeString.includes('饭店')) return 'restaurant'
  if (poiTypeString.includes('景点') || poiTypeString.includes('风景')) return 'attraction'
  return 'attraction'
}

// 暴露给父组件的方法 - 添加POI到行程
const promptAndAddPoi = async (poi) => {
  console.log('🎯 添加POI到行程:', poi)

  try {
    const dayIndex = await selectDay()
    const dayNumber = dayIndex + 1

    const itemType = getPoiTypeClass(poi.type)
    const newPoiItem = {
      id: Date.now() + Math.random(),
      type: itemType,
      name: poi.name,
      time: '', // 保持兼容性，格式为 "开始时间-结束时间"
      startTime: '', // 新增：开始时间，格式 "HH:mm"
      endTime: '',   // 新增：结束时间，格式 "HH:mm"
      duration: '',  // 新增：时长，自动计算
      details: poi.address || poi.details || '',
      address: poi.address || '',
      lat: poi.lat || (poi.location ? poi.location.lat : null),
      lng: poi.lng || (poi.location ? poi.location.lng : null),
      // 保留原始POI数据以便后续使用
      rawPoiData: poi,
      // 其他可能需要的字段
      editing: false,
      // 如果是路径规划项目，添加额外字段
      ...(itemType === 'route-planning' ? {
        startPoint: poi.startPoint || '',
        endPoint: poi.endPoint || '',
        transportMode: poi.transportMode || '',
        steps: poi.steps || [],
        cost: poi.cost || '0'
      } : {})
    }

    // 如果有预定义的时间信息，设置时间
    if (poi.suggestedTime) {
      newPoiItem.startTime = poi.suggestedTime.start
      newPoiItem.endTime = poi.suggestedTime.end
      newPoiItem.time = `${poi.suggestedTime.start}-${poi.suggestedTime.end}`
      newPoiItem.duration = calculateTimeDuration(poi.suggestedTime.start, poi.suggestedTime.end)
    }

    itinerary[dayIndex].items.push(newPoiItem)

    // 添加成功后，如果需要可以自动打开时间编辑器
    if (!poi.suggestedTime) {
      // 可以添加一个选项让用户选择是否立即设置时间
      setTimeout(() => {
        const addedItemIndex = itinerary[dayIndex].items.length - 1
        ElMessage.success({
          message: `成功将 "${poi.name}" 添加到第 ${dayNumber} 天`,
          duration: 3000,
          showClose: true,
          onClick: () => {
            openTimeEditor(dayNumber, addedItemIndex)
          }
        })
      }, 100)
    } else {
      ElMessage.success(`成功将 "${poi.name}" 添加到第 ${dayNumber} 天`)
    }

    // 滚动到新添加的项目
    nextTick(() => {
      const newItemElement = document.querySelector(`[data-item-id="${newPoiItem.id}"]`)
      if (newItemElement) {
        newItemElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        // 添加高亮效果
        newItemElement.classList.add('new-item-highlight')
        setTimeout(() => {
          newItemElement.classList.remove('new-item-highlight')
        }, 2000)
      }
    })

  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 添加POI失败:', error)
      ElMessage.error(`添加行程失败: ${error.message || '未知错误'}`)
    }
  }
}

// 计算时间时长的辅助函数
const calculateTimeDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return ''

  try {
    const start = new Date(`2000/01/01 ${startTime}`)
    const end = new Date(`2000/01/01 ${endTime}`)
    const duration = (end - start) / (1000 * 60) // 分钟

    if (duration <= 0) return '时间无效'

    if (duration < 60) {
      return `${duration}分钟`
    } else {
      const hours = Math.floor(duration / 60)
      const minutes = duration % 60
      return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
    }
  } catch {
    return '计算失败'
  }
}

// 添加排序方法 - 所有项目一起排序
const sortDayItems = (dayIndex) => {
  const day = itinerary[dayIndex]
  if (!day || !day.items || day.items.length === 0) {
    ElMessage.warning('该天没有可排序的项目')
    return
  }

  try {
    // 为所有项目计算排序权重
    const itemsWithWeight = day.items.map(item => {
      let weight = 0
      let sortableTime = ''

      if (item.type === 'route-planning') {
        // 路径规划项目：使用起点时间或默认权重
        if (item.startTime) {
          // 如果有设置时间，按时间排序
          sortableTime = item.startTime
          weight = timeToMinutes(item.startTime)
        } else {
          // 如果没有设置时间，放在有时间的项目之后，无时间的项目之前
          weight = 2000 // 中间权重
        }
      } else {
        // 普通活动项目
        if (item.startTime && item.endTime) {
          // 有时间的项目按时间排序
          sortableTime = item.startTime
          weight = timeToMinutes(item.startTime)
        } else {
          // 无时间的项目放在最后
          weight = 3000
        }
      }

      return {
        ...item,
        _sortWeight: weight,
        _sortableTime: sortableTime
      }
    })

    // 按权重排序
    itemsWithWeight.sort((a, b) => a._sortWeight - b._sortWeight)

    // 移除临时排序字段
    const sortedItems = itemsWithWeight.map(({ _sortWeight, _sortableTime, ...item }) => item)

    // 更新天的项目
    day.items = sortedItems

    ElMessage.success('行程和活动已按时间排序')

    // 重新初始化拖拽
    setTimeout(() => {
      reinitSortable(dayIndex)
    }, 100)

  } catch (error) {
    console.error('排序过程中出错:', error)
    ElMessage.error('排序失败，请重试')
  }
}

// 将时间字符串转换为分钟数（用于排序）
const timeToMinutes = (timeStr) => {
  if (!timeStr) return 9999 // 无时间的项目排在后面

  const [hours, minutes] = timeStr.split(':').map(Number)
  return hours * 60 + minutes
}

// 智能安排无时间的项目
const arrangeItemsWithoutTime = (itemsWithTime, itemsWithoutTime) => {
  if (itemsWithoutTime.length === 0) return []

  const arrangedItems = []
  const timeSlots = []

  // 分析已有项目的时间段，找出空闲时段
  if (itemsWithTime.length > 0) {
    // 按时间顺序分析
    itemsWithTime.sort((a, b) => timeToMinutes(a.startTime) - timeToMinutes(b.startTime))

    // 检查早上时段（9:00之前）
    const firstItem = itemsWithTime[0]
    if (timeToMinutes(firstItem.startTime) > timeToMinutes('09:00')) {
      timeSlots.push({
        start: '09:00',
        end: firstItem.startTime,
        duration: timeToMinutes(firstItem.startTime) - timeToMinutes('09:00')
      })
    }

    // 检查项目之间的间隙
    for (let i = 0; i < itemsWithTime.length - 1; i++) {
      const current = itemsWithTime[i]
      const next = itemsWithTime[i + 1]

      const gap = timeToMinutes(next.startTime) - timeToMinutes(current.endTime)
      if (gap >= 30) { // 至少30分钟的空隙才安排
        timeSlots.push({
          start: current.endTime,
          end: next.startTime,
          duration: gap
        })
      }
    }

    // 检查晚上时段（最后一个项目之后）
    const lastItem = itemsWithTime[itemsWithTime.length - 1]
    if (timeToMinutes(lastItem.endTime) < timeToMinutes('21:00')) {
      timeSlots.push({
        start: lastItem.endTime,
        end: '21:00',
        duration: timeToMinutes('21:00') - timeToMinutes(lastItem.endTime)
      })
    }
  } else {
    // 如果没有有时间的项目，提供默认时间段
    timeSlots.push({
      start: '09:00',
      end: '18:00',
      duration: 9 * 60 // 9小时
    })
  }

  // 为无时间项目分配时间段
  itemsWithoutTime.forEach((item, index) => {
    if (index < timeSlots.length) {
      const slot = timeSlots[index]
      // 为项目分配1.5小时的时间段
      const duration = 90 // 1.5小时

      if (slot.duration >= duration) {
        item.startTime = slot.start
        const startMinutes = timeToMinutes(slot.start)
        item.endTime = minutesToTime(startMinutes + duration)
        item.time = `${item.startTime}-${item.endTime}`
        item.duration = '1.5小时'
      }
    }

    arrangedItems.push(item)
  })

  return arrangedItems
}

// 将分钟数转换为时间字符串
const minutesToTime = (totalMinutes) => {
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
}

// 重新初始化拖拽
const reinitSortable = (dayIndex) => {
  // 安全地销毁旧的实例
  const oldInstance = sortableInstances.get(dayIndex)
  if (oldInstance && typeof oldInstance.destroy === 'function') {
    try {
      oldInstance.destroy()
    } catch (error) {
      console.warn(`销毁第${dayIndex + 1}天的拖拽实例时出错:`, error)
    }
  }

  // 从 Map 中移除旧实例
  sortableInstances.delete(dayIndex)

  // 重新初始化
  nextTick(() => {
    setTimeout(() => {
      const selector = `.day-${dayIndex} .items-container`
      const container = document.querySelector(selector)

      if (container) {
        console.log(`🔄 重新初始化第${dayIndex + 1}天的拖拽`)
        initSortable(dayIndex, container)
      } else {
        console.error(`❌ 未找到第${dayIndex + 1}天的容器`)
        // 尝试其他可能的选择器
        const alternativeSelectors = [
          `.el-tab-pane:nth-child(${dayIndex + 1}) .items-container`,
          `[data-day="${dayIndex}"] .items-container`,
          `.items-container.day-${dayIndex}`
        ]

        for (const altSelector of alternativeSelectors) {
          const altContainer = document.querySelector(altSelector)
          if (altContainer) {
            console.log(`🔧 使用备选选择器找到容器: ${altSelector}`)
            initSortable(dayIndex, altContainer)
            break
          }
        }
      }
    }, 150) // 稍微增加延迟确保 DOM 更新完成
  })
}

// 在 ItineraryPanel.vue 中添加
const loadItineraryData = (itineraryData) => {
  console.log('📥 ItineraryPanel 接收到行程数据:', itineraryData)

  if (!itineraryData || !Array.isArray(itineraryData)) {
    console.error('❌ 无效的行程数据:', itineraryData)
    ElMessage.error('行程数据格式错误')
    return
  }

  try {
    // 清空现有数据
    itinerary.length = 0

    // 添加新的行程数据
    itineraryData.forEach(dayData => {
      const newDay = {
        day: dayData.day || itinerary.length + 1,
        date: dayData.date ? new Date(dayData.date) : new Date(),
        items: dayData.items || []
      }
      itinerary.push(newDay)
    })

    // 设置活动标签为第一天
    if (itinerary.length > 0) {
      activeDay.value = `day-${itinerary[0].day}`
    }

    console.log('✅ 行程数据加载成功，总天数:', itinerary.length)
    ElMessage.success('行程数据加载完成')

  } catch (error) {
    console.error('❌ 加载行程数据失败:', error)
    ElMessage.error('加载行程数据失败')
  }
}

// 暴露方法
defineExpose({
  promptAndAddPoi,
  sortDayItems,
  showDayActivitiesOnMap,
  clearMapMarkers,
  loadItineraryData,
  // 新增：获取行程数据的方法
  getItineraryData: () => {
    return itinerary
  },

})
</script>

<style scoped>

/* 备注编辑器样式 */
.note-editor-dialog {
  padding: 10px 0;
}

.note-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.note-header h4 {
  margin: 0 0 5px 0;
  font-size: 16px;
  color: #303133;
}

.item-type {
  margin: 0;
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.note-input-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #303133;
}

.note-input-section .el-textarea {
  margin-bottom: 20px;
}

:deep(.note-input-section .el-textarea__inner) {
  font-size: 14px;
  line-height: 1.5;
  padding: 12px;
  border-radius: 6px;
  resize: none;
}

:deep(.note-input-section .el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 备注按钮样式 */
.item-actions .el-button--info {
  color: #909399;
}

.item-actions .el-button--info:hover {
  color: #a6a9ad;
}

/* 在项目详情中显示备注的样式（可选） */
.item-details .item-note {
  margin: 4px 0 0 0;
  font-size: 11px;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 2px 6px;
  border-radius: 3px;
  border-left: 2px solid #e6a23c;
}

/* 排序按钮样式 */
.sort-btn {
  margin-left: 8px;
  color: #409eff;
  font-size: 12px;
}

.sort-btn:hover {
  color: #67c8ff;
}

/* 日期信息区域布局调整 */
.day-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .day-info {
    flex-wrap: wrap;
    gap: 4px;
  }

  .sort-btn {
    margin-left: 4px;
  }
}


/* 拖拽手柄样式 */
.drag-handle {
  cursor: grab;
  padding: 8px 4px;
  margin-right: 8px;
  color: #c0c4cc;
  font-size: 12px;
  user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

/* 拖拽状态样式 */
.itinerary-item.dragging {
  opacity: 0.5;
  background: #f0f7ff;
}

/* Sortable.js 相关样式 */
.sortable-ghost {
  opacity: 0.4;
  background: #cce5ff;
}

.sortable-chosen {
  background: #f0f7ff;
}

.sortable-drag {
  opacity: 0.8;
  transform: rotate(5deg);
}

.itinerary-panel {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.days-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
}

:deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 标签样式 */
.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-day-icon {
  color: #409eff;
  cursor: pointer;
  transition: color 0.3s;
}

.add-day-icon:hover {
  color: #67c8ff;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  margin-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.day-info {
  display: flex;
  align-items: center;
}

.day-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.day-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.items-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.itinerary-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 8px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.itinerary-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.item-icon {
  margin-right: 12px;
  flex-shrink: 0;
}

.item-details {
  flex: 1;
  min-width: 0;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.item-name {
  font-weight: bold;
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.item-address {
  margin: 0;
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-actions {
  display: flex;
  gap: 4px;
  margin-left: 10px;
  align-items: center;
}

.move-buttons {
  display: flex;
  flex-direction: column;
  margin-left: 5px;
}

.add-item-section {
  padding: 20px 0;
  text-align: center;
  border-top: 1px dashed #e4e7ed;
  margin-top: 10px;
}

.add-item-btn {
  width: 120px;
}

.day-stats {
  padding: 10px 0;
  text-align: center;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 类型颜色 - 这是你缺少的关键部分 */
.type-attraction {
  border-left-color: #409eff;
  background: linear-gradient(to right, rgba(64, 158, 255, 0.05), white);
}

.type-restaurant {
  border-left-color: #e6a23c;
  background: linear-gradient(to right, rgba(230, 162, 60, 0.05), white);
}

.type-hotel {
  border-left-color: #67c23a;
  background: linear-gradient(to right, rgba(103, 194, 58, 0.05), white);
}

.type-route {
  border-left-color: #909399;
  background: linear-gradient(to right, rgba(144, 147, 153, 0.05), white);
}

.type-route-planning {
  border-left-color: #ff6b6b;
  background: linear-gradient(to right, rgba(255, 107, 107, 0.05), white);
}

/* 图标颜色 */
.type-attraction .item-icon {
  color: #409eff;
}

.type-restaurant .item-icon {
  color: #e6a23c;
}

.type-hotel .item-icon {
  color: #67c23a;
}

.type-route .item-icon {
  color: #909399;
}

.type-route-planning .item-icon {
  color: #ff6b6b;
}

/* 新添加项目的高亮效果 */
.new-item-highlight {
  animation: highlight-pulse 2s ease-in-out;
}

@keyframes highlight-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.7);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(64, 158, 255, 0);
  }
  100% {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
}

/* 路径规划模态框样式 */
.route-planning-dialog {
  max-height: 60vh;
  overflow-y: auto;
}

.route-inputs {
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 15px;
}

.input-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #303133;
}

.transport-mode {
  margin-bottom: 20px;
  text-align: center;
}

.route-result {
  margin-top: 20px;
}

.route-options {
  max-height: 300px;
  overflow-y: auto;
}

.route-plan-card {
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.route-plan-card.active {
  border-color: #409eff;
  background: #f0f7ff;
}

.route-plan-card:hover {
  border-color: #409eff;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.plan-title {
  font-weight: bold;
  font-size: 14px;
}

.plan-details {
  margin-bottom: 10px;
}

.plan-details p {
  margin: 2px 0;
  font-size: 12px;
  color: #666;
}

.plan-steps {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.plan-step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 5px;
  font-size: 12px;
}

.step-icon {
  margin-right: 8px;
  flex-shrink: 0;
}

.step-text {
  flex: 1;
  line-height: 1.4;
}

.plan-actions {
  margin-top: 20px;
  text-align: center;
}

.save-actions {
  margin-top: 20px;
  text-align: center;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

/* 路线详情样式 */
.route-detail-dialog {
  max-height: 60vh;
  overflow-y: auto;
}

.route-overview {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.route-overview h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.route-meta {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.route-steps h5 {
  margin-bottom: 15px;
  font-size: 14px;
  color: #303133;
}

.steps-container {
  max-height: 300px;
  overflow-y: auto;
}

.route-step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.step-number {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-right: 12px;
  flex-shrink: 0;
}

.step-content {
  display: flex;
  align-items: flex-start;
  flex: 1;
}

.step-content .step-icon {
  margin-right: 8px;
  margin-top: 2px;
}

.step-content .step-text {
  line-height: 1.4;
  font-size: 13px;
}

/* 时间显示容器样式 */
.time-display-container {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  pointer-events: none; /* 让容器不阻止事件 */
}

.time-display {
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 100px;
  text-align: center;
  pointer-events: auto; /* 只有时间显示本身可以点击 */
}

.time-display:hover {
  background: #e4e7ed;
  color: #606266;
}

.edit-time-btn {
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: auto; /* 编辑按钮可以点击 */
}

.time-display-container:hover .edit-time-btn {
  opacity: 1;
}

/* 时间编辑器样式 */
.time-editor-dialog {
  padding: 10px 0;
}

.time-inputs {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.time-input-group {
  flex: 1;
}

.time-input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #303133;
}

.time-preview {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 20px;
  text-align: center;
}

.preview-text {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.preview-time {
  font-weight: bold;
  color: #409eff;
  font-size: 16px;
}

.duration-text {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.duration {
  font-weight: bold;
  color: #67c23a;
}

.quick-times {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.quick-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.quick-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.quick-buttons .el-button {
  font-size: 12px;
  padding: 8px 4px;
}

/* 无结果提示 */
.no-result {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-style: italic;
}

/* 移动按钮样式 */
.move-buttons .el-button {
  padding: 2px 4px;
  height: auto;
  min-height: auto;
}

/* 确保项目详情区域正确响应点击 */
.item-details {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

/* 但排除时间区域的点击 */
.item-details .time-display-container,
.item-details .time-display,
.item-details .edit-time-btn {
  cursor: default;
}

.item-details .time-display {
  cursor: pointer;
}

.item-details .edit-time-btn {
  cursor: pointer;
}

/* 标签页内的运输方式标签页 */
.transport-tabs {
  margin-top: 15px;
}

:deep(.transport-tabs .el-tabs__header) {
  margin-bottom: 15px;
}

:deep(.transport-tabs .el-tabs__item) {
  padding: 0 16px;
}

:deep(.transport-tabs .el-tabs__item.is-disabled) {
  color: #c0c4cc;
  cursor: not-allowed;
}
</style>
