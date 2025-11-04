<template>
  <div class="travel-plans">
    <!-- 头部操作栏 -->
    <div class="plans-header">
      <div class="header-left">
        <h3>我的旅行计划</h3>
        <p class="subtitle">管理您保存的所有行程计划</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Refresh"
          @click="loadPlans"
          :loading="loading"
        >
          刷新
        </el-button>
        <el-button
          type="success"
          :icon="DocumentAdd"
          @click="saveCurrentPlan"
          :disabled="!hasCurrentPlan"
        >
          保存当前行程
        </el-button>
      </div>
    </div>

    <!-- 行程列表 -->
    <div class="plans-list" v-if="travelPlans.length > 0">
      <el-table
        :data="travelPlans"
        style="width: 100%"
        :loading="loading"
        empty-text="暂无行程计划"
      >
        <el-table-column prop="title" label="行程标题" min-width="200">
          <template #default="{ row }">
            <div class="plan-title">
              <span class="title-text">{{ row.title }}</span>
              <el-tag v-if="row.is_current" type="success" size="small">当前</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="days_count" label="天数" width="80">
          <template #default="{ row }">
            <span class="days-count">{{ row.days_count }}天</span>
          </template>
        </el-table-column>

        <el-table-column prop="activities_count" label="活动数" width="100">
          <template #default="{ row }">
            <span class="activities-count">{{ row.activities_count }}个活动</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <span class="create-time">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="primary"
                link
                :icon="View"
                @click="viewPlan(row)"
                title="查看行程详情"
              >
                查看
              </el-button>
              <!-- 新增：继续编辑按钮 -->
              <el-button
                type="warning"
                link
                :icon="EditPen"
                @click="continueEditing(row)"
                title="继续编辑此行程"
              >
                继续编辑
              </el-button>
              <el-button
                type="success"
                link
                :icon="Download"
                @click="downloadPlan(row)"
                title="下载Word文档"
              >
                下载
              </el-button>
              <el-button
                type="info"
                link
                :icon="Edit"
                @click="editPlanTitle(row)"
                title="编辑标题"
              >
                重命名
              </el-button>
              <el-button
                type="danger"
                link
                :icon="Delete"
                @click="deletePlan(row)"
                title="删除行程"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="暂无旅行计划" :image-size="150">
        <template #description>
          <p>您还没有保存任何旅行计划</p>
          <p class="empty-tip">在行程面板中点击"保存行程"来创建您的第一个旅行计划</p>
        </template>
        <el-button
          type="primary"
          :icon="DocumentAdd"
          @click="saveCurrentPlan"
          :disabled="!hasCurrentPlan"
        >
          立即保存当前行程
        </el-button>
      </el-empty>
    </div>

    <!-- 行程详情模态框 -->
    <el-dialog
      v-model="planDetailVisible"
      :title="`📋 ${selectedPlan?.title}`"
      width="800px"
      :before-close="handlePlanDetailClose"
    >
      <PlanDetail
        v-if="selectedPlan"
        :plan="selectedPlan"
        @close="planDetailVisible = false"
      />
    </el-dialog>

    <!-- 保存行程模态框 -->
    <el-dialog
      v-model="savePlanVisible"
      title="💾 保存行程计划"
      width="500px"
      :before-close="handleSavePlanClose"
    >
      <div class="save-plan-dialog">
        <div class="form-group">
          <label>行程标题：</label>
          <el-input
            v-model="savePlanData.title"
            placeholder="请输入行程标题，如'上海三日游'"
            maxlength="50"
            show-word-limit
          />
        </div>

        <div class="plan-preview">
          <h4>行程概览：</h4>
          <div class="preview-content">
            <p>📅 天数：{{ currentPlanData.days_count }}天</p>
            <p>🎯 活动数：{{ currentPlanData.activities_count }}个</p>
            <p>🕒 创建时间：{{ currentPlanData.created_at }}</p>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleSavePlanClose">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="!savePlanData.title.trim()"
          @click="confirmSavePlan"
        >
          {{ saving ? '保存中...' : '保存行程' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, inject } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  DocumentAdd,
  View,
  Download,
  Edit,
  Delete,
  EditPen // 新增编辑图标
} from '@element-plus/icons-vue'
import PlanDetail from './PlanDetail.vue'

// 注入行程面板引用和事件发射器
const itineraryRef = inject('itineraryRef', ref(null))
const emit = defineEmits(['continue-editing'])

// 响应式数据
const travelPlans = ref([])
const loading = ref(false)
const saving = ref(false)
const planDetailVisible = ref(false)
const savePlanVisible = ref(false)
const selectedPlan = ref(null)

// 保存行程数据
const savePlanData = reactive({
  title: '',
  description: ''
})

// 计算属性
const hasCurrentPlan = computed(() => {
  if (!itineraryRef?.value) return false
  try {
    let itineraryData = []
    if (typeof itineraryRef.value.getItineraryData === 'function') {
      itineraryData = itineraryRef.value.getItineraryData()
    } else {
      itineraryData = itineraryRef.value.itinerary || []
    }
    return itineraryData.length > 0
  } catch (error) {
    console.warn('访问行程数据失败:', error)
    return false
  }
})

const currentPlanData = computed(() => {
  let daysCount = 0
  let activitiesCount = 0

  if (itineraryRef?.value) {
    try {
      let itineraryData = []
      if (typeof itineraryRef.value.getItineraryData === 'function') {
        itineraryData = itineraryRef.value.getItineraryData()
      } else {
        itineraryData = itineraryRef.value.itinerary || []
      }

      daysCount = itineraryData.length
      activitiesCount = itineraryData.reduce((total, day) => total + (day.items?.length || 0), 0)
    } catch (error) {
      console.warn('计算行程数据失败:', error)
    }
  }

  return {
    days_count: daysCount,
    activities_count: activitiesCount,
    created_at: new Date().toLocaleString()
  }
})

// 生命周期
onMounted(() => {
  console.log('🚀 TravelPlans 组件已挂载')
  loadPlans()
})

// 方法
const loadPlans = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    console.log('🔑 当前token:', token)

    if (!token) {
      throw new Error('用户未登录')
    }

    const response = await fetch('http://localhost:5000/api/plans', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('📡 响应状态:', response.status)

    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      return
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    console.log('📋 获取到的行程数据:', data)
    travelPlans.value = data.plans || []
    console.log('✅ 行程数据已加载:', travelPlans.value.length, '个行程')

  } catch (error) {
    console.error('❌ 加载行程失败:', error)
    ElMessage.error('加载行程失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 新增：继续编辑功能
const continueEditing = async (plan) => {
  try {
    loading.value = true
    console.log('🚀 开始加载行程用于编辑:', plan.id)

    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:5000/api/plans/${plan.id}/load`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('📡 加载行程响应状态:', response.status)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    console.log('✅ 成功加载行程数据:', data)

    if (data.plan) {
      // 发射事件给父组件，传递完整的行程数据
      emit('continue-editing', data.plan)
      ElMessage.success(`已加载行程"${plan.title}"，可以继续编辑了！`)
    } else {
      throw new Error('未获取到行程数据')
    }

  } catch (error) {
    console.error('❌ 加载行程失败:', error)
    ElMessage.error('加载行程失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const saveCurrentPlan = () => {
  if (!hasCurrentPlan.value) {
    ElMessage.warning('当前没有可保存的行程')
    return
  }

  // 生成默认标题
  const dayText = currentPlanData.value.days_count > 1 ?
    `${currentPlanData.value.days_count}天` : '一日'
  savePlanData.title = `${dayText}旅行计划`

  savePlanVisible.value = true
}

const confirmSavePlan = async () => {
  if (!savePlanData.title.trim()) {
    ElMessage.warning('请输入行程标题')
    return
  }

  saving.value = true
  try {
    const token = localStorage.getItem('token')

    // 安全地获取行程数据
    let itineraryData = []
    if (itineraryRef?.value) {
      if (typeof itineraryRef.value.getItineraryData === 'function') {
        itineraryData = itineraryRef.value.getItineraryData()
      } else {
        itineraryData = itineraryRef.value.itinerary || []
      }
    }

    const planData = {
      title: savePlanData.title.trim(),
      description: savePlanData.description.trim(),
      itinerary: itineraryData,
      days_count: currentPlanData.value.days_count,
      activities_count: currentPlanData.value.activities_count
    }

    console.log('📤 发送的行程数据:', planData)

    const response = await fetch('http://localhost:5000/api/plans/save', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(planData)
    })

    console.log('📡 保存响应状态:', response.status)

    if (response.ok) {
      const result = await response.json()
      console.log('✅ 保存成功响应:', result)
      ElMessage.success('行程保存成功！')
      savePlanVisible.value = false
      resetSaveForm()
      loadPlans()
    } else {
      const errorText = await response.text()
      console.error('❌ 保存失败响应:', errorText)
      throw new Error(`保存失败: ${response.status}`)
    }
  } catch (error) {
    console.error('❌ 保存行程失败:', error)
    ElMessage.error('保存行程失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const viewPlan = (plan) => {
  selectedPlan.value = plan
  planDetailVisible.value = true
}

const downloadPlan = async (plan) => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.error('请先登录')
      return
    }

    console.log('开始下载行程:', plan.id)

    const response = await fetch(`http://localhost:5000/api/plans/${plan.id}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('响应状态:', response.status)

    if (response.ok) {
      const blob = await response.blob()
      console.log('Blob大小:', blob.size)

      if (blob.size === 0) {
        throw new Error('文件为空')
      }

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${plan.title}.docx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('下载成功！')
    } else {
      const errorText = await response.text()
      console.error('下载失败响应:', errorText)
      throw new Error(`下载失败: ${response.status} ${response.statusText}`)
    }
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(`下载失败: ${error.message}`)
  }
}

const editPlanTitle = async (plan) => {
  try {
    const { value: newTitle } = await ElMessageBox.prompt(
      '请输入新的行程标题',
      '重命名行程',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: plan.title,
        inputValidator: (value) => {
          if (!value || !value.trim()) {
            return '标题不能为空'
          }
          return true
        }
      }
    )

    if (newTitle && newTitle.trim()) {
      // 调用API更新标题
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:5000/api/plans/${plan.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: newTitle.trim() })
      })

      if (response.ok) {
        ElMessage.success('重命名成功！')
        loadPlans()
      } else {
        throw new Error('重命名失败')
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重命名失败:', error)
      ElMessage.error('重命名失败')
    }
  }
}

const deletePlan = async (plan) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除行程"${plan.title}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    // 调用API删除
    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:5000/api/plans/${plan.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      ElMessage.success('删除成功！')
      loadPlans()
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败，请重试')
    }
  }
}

const handlePlanDetailClose = () => {
  planDetailVisible.value = false
  selectedPlan.value = null
}

const handleSavePlanClose = () => {
  savePlanVisible.value = false
  resetSaveForm()
}

const resetSaveForm = () => {
  savePlanData.title = ''
  savePlanData.description = ''
}

const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}
</script>



<style scoped>
.travel-plans {
  padding: 0;
}

.plans-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 0 4px;
}

.header-left h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.plans-list {
  margin-top: 16px;
}

.plan-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-weight: 500;
}

.days-count {
  color: #409eff;
  font-weight: 500;
}

.activities-count {
  color: #67c23a;
  font-weight: 500;
}

.create-time {
  color: #909399;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.empty-tip {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}

/* 保存行程对话框样式 */
.save-plan-dialog {
  padding: 8px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #303133;
}

.plan-preview {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.plan-preview h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.preview-content p {
  margin: 6px 0;
  font-size: 13px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .plans-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
}

/* 原有样式保持不变，只添加新样式 */
.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }
}
</style>
