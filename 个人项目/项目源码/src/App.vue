<template>
  <div class="app">
    <!-- 登录表单弹窗 -->
    <div v-if="showLoginForm" class="login-modal">
      <LoginForm
        @login-success="handleLoginSuccess"
        @close="showLoginForm = false"
      />
    </div>

    <!-- 创建新计划模态框 - 简化版 -->
<el-dialog
  v-model="createPlanVisible"
  title="🆕 创建新旅行计划"
  width="500px"
  :before-close="handleCreatePlanClose"
>
  <div class="create-plan-dialog">
    <div class="form-group">
      <label>计划名称：</label>
      <el-input
        v-model="newPlanData.title"
        placeholder="例如：上海三日游、北京文化之旅"
        maxlength="50"
        show-word-limit
      />
    </div>
    <div class="form-group">
      <label>计划描述：</label>
      <el-input
        v-model="newPlanData.description"
        type="textarea"
        :rows="3"
        placeholder="简单描述您的旅行计划（可选）..."
        maxlength="200"
        show-word-limit
      />
    </div>
    <div class="plan-tip">
      <p>💡 提示：天数可以在行程面板中动态添加</p>
    </div>
  </div>

  <template #footer>
    <el-button @click="handleCreatePlanClose">取消</el-button>
    <el-button
      type="primary"
      :disabled="!newPlanData.title.trim()"
      @click="createNewPlan"
    >
      创建并开始规划
    </el-button>
  </template>
</el-dialog>

    <!-- 行程管理模态框 -->
    <el-dialog
      v-model="travelPlansVisible"
      title="📋 我的旅行计划"
      width="900px"
      :before-close="handleTravelPlansClose"
    >
      <TravelPlans
        v-if="travelPlansVisible"
        @view-plan="handleViewPlan"
        @continue-editing="handleContinueEditing"
        @create-new="showCreatePlan"
        @close="travelPlansVisible = false"
      />
    </el-dialog>

    <!-- 主应用内容 -->
    <div v-if="user" class="main-layout">
      <!-- 顶部导航栏 -->
      <div class="app-header">
        <h1>{{ currentPlan?.title || '旅行规划应用' }}</h1>
        <div class="user-info">
          <span>欢迎, {{ user.username }}!</span>
          <!-- 修改：显示当前计划信息 -->
          <el-button
            v-if="currentPlan"
            type="success"
            :icon="DocumentAdd"
            @click="saveCurrentPlan"
            :loading="saving"
          >
            保存计划
          </el-button>
          <el-button
            @click="showTravelPlans"
            type="primary"
            link
            class="plans-btn"
          >
            📋 我的旅行计划
          </el-button>
          <button @click="logout" class="logout-btn">退出登录</button>
        </div>
      </div>

      <!-- 规划界面 -->
      <div v-if="currentPlan" class="main-content">
        <ControlPanel
          class="control-panel"
          @search-place="handleSearchPlace"
          @plan-route="handlePlanRoute"
          @add-to-itinerary="handleAddToItinerary"
          @refresh-pois="handleRefreshPois"
          @category-change="handleCategoryChange"
          :weather-data="weatherData"
          :discovered-pois="discoveredPois"
        />

        <div class="content-area">
          <MapContainer
            ref="mapRef"
            class="map-container"
            @location-click="handleLocationClick"
            @weather-data="handleWeatherData"
            @location-details="handleLocationDetails"
            @pois-found="handlePoisFound"
            @poi-marker-click="handleAddPoiFromMap"
          />
          <ItineraryPanel
            ref="itineraryRef"
            class="itinerary-panel"
            :initial-days="currentPlan.days"
            @save="handleSaveItinerary"
          />
        </div>
      </div>

      <!-- 没有选择计划时的欢迎页面 -->
      <div v-else class="welcome-page">
        <div class="welcome-content">
          <h1>🌍 旅行规划助手</h1>
          <p>开始规划您的完美旅程</p>
          <div class="welcome-features">
            <div class="feature">
              <span class="icon">🗺️</span>
              <h3>智能地图</h3>
              <p>探索目的地，发现周边景点</p>
            </div>
            <div class="feature">
              <span class="icon">📝</span>
              <h3>行程规划</h3>
              <p>轻松规划您的旅行路线</p>
            </div>
            <div class="feature">
              <span class="icon">🌤️</span>
              <h3>实时天气</h3>
              <p>获取目的地天气信息</p>
            </div>
            <div class="feature">
              <span class="icon">💾</span>
              <h3>行程保存</h3>
              <p>保存和查看旅行计划</p>
            </div>
          </div>
          <div class="action-buttons">
            <el-button
              type="primary"
              size="large"
              :icon="DocumentAdd"
              @click="showCreatePlan"
            >
              创建新旅行计划
            </el-button>
            <el-button
              type="success"
              size="large"
              :icon="Collection"
              @click="showTravelPlans"
            >
              查看已有计划
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 未登录时的欢迎页面 -->
    <div v-else class="welcome-page">
      <div class="welcome-content">
        <h1>🌍 旅行规划助手</h1>
        <p>探索世界，规划完美旅程</p>
        <button @click="showLoginForm = true" class="login-btn">开始使用</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, provide, reactive } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import MapContainer from './components/MapContainer.vue'
import ItineraryPanel from './components/ItineraryPanel.vue'
import LoginForm from './components/LoginForm.vue'
import TravelPlans from './components/TravelPlans.vue'
import { ElMessage } from 'element-plus'
import { DocumentAdd, Collection } from '@element-plus/icons-vue'

// 响应式数据
const weatherData = ref(null)
const mapRef = ref(null)
const discoveredPois = ref([])
const itineraryRef = ref(null)
const user = ref(null)
const showLoginForm = ref(false)
const travelPlansVisible = ref(false)
const createPlanVisible = ref(false)
const currentPlan = ref(null)
const saving = ref(false)

// 新计划数据
const newPlanData = reactive({
  title: '',
  description: '',
  days: 1
})

// 提供依赖注入
provide('mapRef', mapRef)
provide('itineraryRef', itineraryRef)

// 检查登录状态
onMounted(() => {
  console.log('🚀 App.vue 已挂载')
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    user.value = JSON.parse(savedUser)
    console.log('✅ 用户已登录:', user.value.username)
  } else {
    console.log('❌ 用户未登录')
  }
})

// 计划管理方法
const showCreatePlan = () => {
  createPlanVisible.value = true
}

const showTravelPlans = () => {
  travelPlansVisible.value = true
}

const createNewPlan = () => {
  if (!newPlanData.title.trim()) {
    ElMessage.warning('请输入计划名称')
    return
  }

  currentPlan.value = {
    id: 'temp_' + Date.now(),
    title: newPlanData.title.trim(),
    description: newPlanData.description.trim(),
    days: newPlanData.days,
    created_at: new Date().toISOString(),
    itinerary: [] // 初始为空行程
  }

  createPlanVisible.value = false
  resetNewPlanData()
  ElMessage.success(`开始规划 "${currentPlan.value.title}"`)
}

const handleCreatePlanClose = () => {
  createPlanVisible.value = false
  resetNewPlanData()
}

const resetNewPlanData = () => {
  newPlanData.title = ''
  newPlanData.description = ''
  newPlanData.days = 1
}

const handleTravelPlansClose = () => {
  travelPlansVisible.value = false
}

const handleViewPlan = (plan) => {
  // 加载选中的计划到当前界面
  currentPlan.value = {
    ...plan,
    isExisting: true // 标记为已保存的计划
  }
  travelPlansVisible.value = false
  ElMessage.success(`已加载计划: ${plan.title}`)
}

const handleContinueEditing = (planData) => {
  console.log('🚀 App.vue 接收到继续编辑请求，完整数据:', planData)
  console.log('📋 itinerary 数据类型:', typeof planData.itinerary)
  console.log('📋 itinerary 数据内容:', planData.itinerary)

  // 检查 itinerary 数据
  if (planData.itinerary) {
    if (typeof planData.itinerary === 'string') {
      console.log('⚠️ itinerary 是字符串，需要解析')
      try {
        planData.itinerary = JSON.parse(planData.itinerary)
        console.log('✅ 解析后的 itinerary:', planData.itinerary)
      } catch (e) {
        console.error('❌ 解析 itinerary 失败:', e)
      }
    } else if (Array.isArray(planData.itinerary)) {
      console.log('✅ itinerary 已经是数组格式')
      console.log('📊 天数:', planData.itinerary.length)
      planData.itinerary.forEach((day, index) => {
        console.log(`第${index + 1}天:`, {
          项目数量: day.items?.length || 0,
          日期: day.date,
          项目: day.items?.map(item => ({
            名称: item.name,
            类型: item.type,
            时间: item.time
          }))
        })
      })
    }
  } else {
    console.log('❌ itinerary 数据为空')
  }

  // 设置当前计划
  currentPlan.value = {
    ...planData,
    isExisting: true,
    isLoadedFromContinue: true
  }

  travelPlansVisible.value = false

  // 等待下一个 tick 确保 ItineraryPanel 已渲染
  setTimeout(() => {
    console.log('🔄 准备调用 ItineraryPanel 的 loadItineraryData 方法')
    console.log('🔍 itineraryRef.value:', itineraryRef.value)

    if (itineraryRef.value) {
      console.log('🔍 itineraryRef 的方法:', Object.keys(itineraryRef.value))

      if (typeof itineraryRef.value.loadItineraryData === 'function') {
        console.log('✅ 调用 loadItineraryData')
        itineraryRef.value.loadItineraryData(planData.itinerary)
        ElMessage.success(`已加载行程"${planData.title}"，可以继续编辑了！`)
      } else {
        console.error('❌ ItineraryPanel 的 loadItineraryData 方法不可用')
        // 尝试其他方法
        if (typeof itineraryRef.value.setItineraryData === 'function') {
          console.log('✅ 使用 setItineraryData 方法')
          itineraryRef.value.setItineraryData(planData.itinerary)
        } else {
          console.error('❌ 没有可用的数据加载方法')
          ElMessage.warning('加载行程数据失败，请刷新页面重试')
        }
      }
    } else {
      console.error('❌ itineraryRef 为空')
      ElMessage.warning('行程面板未就绪，请稍后重试')
    }
  }, 100)
}

const saveCurrentPlan = async () => {
  if (saving.value) return

  if (!currentPlan.value || !itineraryRef.value) {
    ElMessage.warning('没有可保存的行程数据')
    return
  }

  saving.value = true

  try {
    const token = localStorage.getItem('token')
    if (!token) {
      ElMessage.warning('请先登录')
      return
    }

    // 获取行程数据
    let itineraryData = []
    if (typeof itineraryRef.value.getItineraryData === 'function') {
      itineraryData = itineraryRef.value.getItineraryData()
    } else {
      itineraryData = itineraryRef.value.itinerary || []
    }

    const planData = {
      title: currentPlan.value.title,
      description: currentPlan.value.description || '',
      itinerary: itineraryData,
      days_count: itineraryData.length,
      activities_count: itineraryData.reduce((total, day) => total + (day.items?.length || 0), 0)
    }

    console.log('💾 保存行程数据:', {
      模式: currentPlan.value.isExisting ? '更新现有' : '创建新',
      计划ID: currentPlan.value.id,
      标题: planData.title,
      天数: planData.days_count,
      活动数: planData.activities_count
    })

    let response
    let url
    let method

    // 关键逻辑：如果是再次编辑的行程，就更新原计划
    if (currentPlan.value.isExisting && currentPlan.value.id) {
      // 更新现有计划
      url = `http://localhost:5000/api/plans/${currentPlan.value.id}`
      method = 'PUT'
      console.log(`🔄 更新现有计划 ID: ${currentPlan.value.id}`)
    } else {
      // 创建新计划
      url = 'http://localhost:5000/api/plans/save'
      method = 'POST'
      console.log('🆕 创建新计划')
    }

    response = await fetch(url, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(planData)
    })

    if (response.ok) {
      const result = await response.json()

      if (method === 'PUT') {
        ElMessage.success('行程更新成功！')
      } else {
        ElMessage.success('行程保存成功！')
        // 如果是新建，更新ID
        if (result.plan_id) {
          currentPlan.value.id = result.plan_id
          currentPlan.value.isExisting = true
        }
      }

    } else {
      throw new Error(`保存失败: ${response.status}`)
    }
  } catch (error) {
    console.error('保存行程失败:', error)
    ElMessage.error('保存行程失败，请重试')
  } finally {
    saving.value = false
  }
}

const handleSaveItinerary = (itineraryData) => {
  // 当 ItineraryPanel 保存时调用
  console.log('行程数据已更新:', itineraryData)
  if (currentPlan.value) {
    currentPlan.value.itinerary = itineraryData
  }
}

// 登录相关方法
const handleLoginSuccess = (userData) => {
  user.value = userData
  showLoginForm.value = false
  ElMessage.success(`欢迎回来，${userData.username}！`)
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  currentPlan.value = null
  ElMessage.info('已退出登录')
}

// 原有的事件处理函数保持不变...
const handleLocationClick = (locationInfo) => {
  console.log('🗺️ 地图点击:', locationInfo)
}

// 处理天气数据
const handleWeatherData = (data) => {
  console.log('🌤️ App.vue 接收到天气数据:', data)
  console.log('🌤️ App.vue 数据详情:', {
    city: data.city,
    weather: data.weather,
    temperature: data.temperature,
    humidity: data.humidity,
    wind: data.wind,
    reportTime: data.reportTime
  })
  weatherData.value = data
  console.log('🌤️ App.vue weatherData 更新后:', weatherData.value)
}

const handleLocationDetails = (details) => {
  console.log('📍 位置详情:', details)
}

const handlePoisFound = (pois) => {
  console.log(`🔍 发现 ${pois.length} 个可视区域 POI`)
  discoveredPois.value = pois
}

const handleAddPoiFromMap = (poiInfo) => {
  console.log('🎯 POI标记被点击:', poiInfo.name)
  if (itineraryRef.value?.promptAndAddPoi) {
    itineraryRef.value.promptAndAddPoi(poiInfo)
  } else {
    console.error('❌ ItineraryPanel 未就绪')
    ElMessage.error('行程面板未准备好，请稍后重试')
  }
}

const handleAddToItinerary = (poiInfo) => {
  console.log('➕ 从ControlPanel添加POI到行程:', poiInfo)
  if (itineraryRef.value?.promptAndAddPoi) {
    itineraryRef.value.promptAndAddPoi(poiInfo)
  } else {
    console.error('❌ ItineraryPanel 未就绪')
    ElMessage.error('行程面板未准备好，请稍后重试')
  }
}

const handleSearchPlace = (keyword) => {
  if (mapRef.value) {
    mapRef.value.searchPlace(keyword)
  }
}

const handlePlanRoute = (points) => {
  if (mapRef.value) {
    mapRef.value.planRoute(points.start, points.end)
  }
}

const handleRefreshPois = () => {
  console.log('🔄 刷新POI')
  if (mapRef.value?.refreshPois) {
    mapRef.value.refreshPois()
  } else {
    console.log('⚠️ refreshPois 方法不存在，使用默认搜索')
    if (mapRef.value) {
      mapRef.value.searchVisiblePois?.()
    }
  }
}

const handleCategoryChange = (category) => {
  console.log('🔍 切换搜索类别:', category)
  if (mapRef.value?.changeSearchCategory) {
    mapRef.value.changeSearchCategory(category)
  } else {
    console.log('⚠️ changeSearchCategory 方法不存在')
    ElMessage.info('类别筛选功能正在开发中')
  }
}
</script>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 登录模态框 */
.login-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

/* 顶部导航栏 */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info span {
  color: #666;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.logout-btn:hover {
  background: #ff3742;
}

/* 主内容布局 */
.main-content {
  flex: 1;
  display: flex;
  height: calc(100vh - 80px); /* 减去头部高度 */
}

/* 原有样式保持不变 */
.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.control-panel {
  width: 320px;
  background: #f8f9fa;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: row; /* 横向排列 */
}

.map-container {
  flex: 1; /* 地图占据剩余空间 */
  min-height: 400px;
  position: relative;
}

.itinerary-panel {
  width: 400px; /* 固定宽度 */
  min-height: 300px;
  border-left: 1px solid #ddd;
  overflow-y: auto;
  background: white;
}

/* 欢迎页面样式 */
.welcome-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.welcome-content {
  text-align: center;
  color: white;
  max-width: 600px;
  padding: 2rem;
}

.welcome-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.welcome-content p {
  font-size: 1.2rem;
  margin-bottom: 3rem;
  opacity: 0.9;
}

.welcome-features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-bottom: 3rem;
}

.feature {
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.feature .icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 1rem;
}

.feature h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
}

.feature p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
}

.login-btn {
  padding: 1rem 3rem;
  font-size: 1.2rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

.plans-btn {
  color: #409eff;
  font-weight: 500;
}

.plans-btn:hover {
  color: #67c8ff;
}

/* 调整欢迎页面的网格布局 */
.welcome-features {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 改为4列 */
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.feature {
  padding: 1.2rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.feature .icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.8rem;
}

.feature h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}

.feature p {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.8;
}

/* 其他原有样式保持不变 */
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.login-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info span {
  color: #666;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.logout-btn:hover {
  background: #ff3742;
}

.main-content {
  flex: 1;
  display: flex;
  height: calc(100vh - 80px);
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.control-panel {
  width: 320px;
  background: #f8f9fa;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: row;
}

.map-container {
  flex: 1;
  min-height: 400px;
  position: relative;
}

.itinerary-panel {
  width: 400px;
  min-height: 300px;
  border-left: 1px solid #ddd;
  overflow-y: auto;
  background: white;
}

.welcome-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.welcome-content {
  text-align: center;
  color: white;
  max-width: 800px;
  padding: 2rem;
}

.welcome-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.welcome-content p {
  font-size: 1.2rem;
  margin-bottom: 3rem;
  opacity: 0.9;
}

.login-btn {
  padding: 1rem 3rem;
  font-size: 1.2rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}
</style>
