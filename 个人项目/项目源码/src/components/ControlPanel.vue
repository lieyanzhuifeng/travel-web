<template>
  <div class="control-panel">
    <!-- 景点搜索 -->
    <div class="search-section">
      <h3>🔍 景点简介</h3>
      <el-input
        v-model="searchKeyword"
        placeholder="输入景点名称..."
        @keyup.enter="handleSearch"
        clearable
      >
        <template #append>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 景点简介弹窗 -->
    <el-dialog
      v-model="showIntroDialog"
      :title="`📖 ${currentPlace} 简介`"
      width="600px"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
    >
      <!-- 加载状态 -->
      <div v-if="isLoadingIntro" class="loading-section">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 简介内容 -->
      <div v-else-if="briefIntro" class="brief-intro-content" v-html="briefIntro"></div>

      <!-- 无数据状态 -->
      <div v-else class="no-intro">
        <el-empty description="暂无该景点简介信息" :image-size="80" />
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showIntroDialog = false">关闭</el-button>
          <el-button
            type="primary"
            :icon="CopyDocument"
            @click="copyBriefIntro"
            :disabled="!briefIntro"
          >
            复制简介
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 在景点搜索下面添加地点搜索 -->
    <el-divider />
    <div class="location-search-section">
      <h3>🗺️ 地点搜索</h3>
      <el-input
        v-model="locationKeyword"
        placeholder="输入省份、城市或具体地点..."
        @keyup.enter="searchLocation"
        clearable
      >
        <template #append>
          <el-button @click="searchLocation">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>

      <!-- 搜索结果列表 -->
      <div v-if="locationResults.length > 0" class="location-results">
        <el-card
          v-for="result in locationResults"
          :key="result.id"
          class="location-card"
          shadow="hover"
          @click="selectLocation(result)"
        >
          <div class="location-info">
            <el-icon :size="16" class="location-icon"><Location /></el-icon>
            <div class="location-details">
              <p class="location-name">{{ result.name }}</p>
              <p class="location-address">{{ result.address }}</p>
              <p class="location-type">{{ result.type }}</p>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 可视区域发现 POI -->
    <el-divider />
    <div class="discovery-section">
      <div class="discovery-header">
        <h3>🌐 可视区域发现 ({{ filteredPois.length }})</h3>
        <div class="discovery-actions">
          <!-- 添加标记显示按钮 -->
          <el-tooltip content="显示地图标记">
            <el-button
              :type="showMarkers ? 'primary' : 'default'"
              :icon="Position"
              circle
              size="small"
              @click="toggleMarkers"
            />
          </el-tooltip>
          <el-button
            type="primary"
            link
            :icon="Refresh"
            @click="handleRefreshPois"
            title="刷新"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 类别选择 -->
      <div class="category-filter">
        <el-radio-group v-model="selectedCategory" @change="handleCategoryChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="scenic">景点</el-radio-button>
          <el-radio-button label="restaurant">餐饮</el-radio-button>
          <el-radio-button label="hotel">酒店</el-radio-button>
          <el-radio-button label="shopping">购物</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 调试信息 -->
      <div class="debug-info" v-if="false"> <!-- 设置为 true 可以显示调试信息 -->
        <p>总POI数: {{ props.discoveredPois.length }}</p>
        <p>过滤后: {{ filteredPois.length }}</p>
        <p>当前类别: {{ selectedCategory }}</p>
      </div>

      <!-- 地点面板 -->
      <div v-if="filteredPois.length > 0" class="poi-list">
        <el-card
          v-for="poi in displayedPois"
          :key="poi.id"
          class="poi-card"
          shadow="hover"
        >
          <div class="poi-header">
            <el-icon :size="16" class="poi-icon"><component :is="getIconByType(poi.typecode)" /></el-icon>
            <span class="poi-name">{{ poi.name }}</span>
            <el-tag :type="getCategoryTagType(getPoiCategory(poi.typecode))" size="small">
              {{ getCategoryName(getPoiCategory(poi.typecode)) }}
            </el-tag>
          </div>
          <p class="poi-address">{{ poi.address }}</p>
          <div class="poi-footer">
            <el-button
              type="success"
              size="small"
              link
              class="add-button"
              @click="handleAddToItinerary(poi)"
            >
              添加到行程
            </el-button>
          </div>
        </el-card>
      </div>
      <el-empty v-else :description="emptyDescription" :image-size="50" />
    </div>

    <!-- 在天气面板上面添加休假信息 -->
    <el-divider />
    <div class="holiday-section">
      <div class="holiday-header">
        <h3>📅 本月休假</h3>
        <el-button
          type="primary"
          link
          :icon="Refresh"
          @click="getHolidayInfo"
          :loading="isLoadingHoliday"
          size="small"
        >
          刷新
        </el-button>
      </div>

      <el-card v-if="holidayData.length > 0" class="holiday-card" @click="showHolidayDialog = true">
        <template #header>
          <div class="card-header">
            <span>本月有 {{ holidayData.length }} 天休假</span>
          </div>
        </template>
        <div class="holiday-preview">
          <p v-for="holiday in holidayData.slice(0, 3)" :key="holiday.name" class="holiday-item">
            📌 {{ holiday.name }} ({{ formatHolidayDate(holiday.date) }})
          </p>
        </div>
      </el-card>

      <el-card v-else class="holiday-card" @click="getHolidayInfo">
        <div class="no-holiday">
          <el-icon :size="20" class="holiday-icon"><Calendar /></el-icon>
          <span>点击获取本月休假信息</span>
        </div>
      </el-card>
    </div>

    <!-- 休假信息详情弹窗 -->
    <el-dialog
      v-model="showHolidayDialog"
      title="📅 本月休假安排"
      width="600px"
    >
      <div class="holiday-detail">
        <div v-if="holidayData.length > 0" class="holiday-list">
          <el-timeline>
            <el-timeline-item
              v-for="holiday in holidayData"
              :key="holiday.name"
              :timestamp="formatHolidayDate(holiday.date)"
              placement="top"
            >
              <el-card shadow="hover">
                <h4>{{ holiday.name }}</h4>
                <p class="holiday-info">
                  <span class="date">{{ holiday.date }}</span>
                  <el-tag type="success" size="small">休假</el-tag>
                </p>
                <p v-if="holiday.tip" class="holiday-tip">💡 {{ holiday.tip }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
        <div v-else class="no-holiday-data">
          <el-empty description="本月暂无休假安排" :image-size="100" />
        </div>
      </div>

      <template #footer>
        <el-button @click="showHolidayDialog = false">关闭</el-button>
        <el-button type="primary" @click="getHolidayInfo" :loading="isLoadingHoliday">
          重新获取
        </el-button>
      </template>
    </el-dialog>

    <!-- 天气显示 -->
    <el-divider />
    <div class="weather-section">
    <div class="weather-header">
    <h3>🌤️ 天气信息</h3>
    <div class="weather-actions">
      <el-button
        type="primary"
        link
        :icon="Calendar"
        @click="getWeekWeather"
        :loading="isLoadingWeekWeather"
        :disabled="!props.weatherData"
        size="small"
      >
        一周预报
      </el-button>
    </div>
  </div>

    <!-- 实时天气 -->
    <el-card v-if="props.weatherData" class="weather-card">
  <template #header>
    <div class="card-header">
      <span>📍 {{ props.weatherData.city }} - 实时天气</span>
      <el-tag v-if="props.weatherData.reportTime" type="info" size="small">
        {{ formatTime(props.weatherData.reportTime) }}
      </el-tag>
    </div>
  </template>
  <div class="weather-info">
    <div class="weather-main">
      <span class="weather-icon">☀️</span>
      <span class="weather-temp">{{ props.weatherData.temperature }}°C</span>
      <span class="weather-desc">{{ props.weatherData.weather }}</span>
    </div>
    <div class="weather-details">
      <p>💧 湿度: {{ props.weatherData.humidity }}%</p>
      <p>💨 风速: {{ props.weatherData.wind }}</p>
    </div>
  </div>
</el-card>

    <!-- 没有天气数据时的提示 -->
    <el-card v-else class="weather-card">
  <div class="weather-placeholder">
    <p>点击地图获取实时天气</p>
  </div>
</el-card>
</div>
    <!-- 一周天气弹窗 -->
    <el-dialog
  v-model="showWeekWeatherDialog"
  title="📅 一周天气预报"
  width="800px"
  :close-on-click-modal="true"
>
  <div class="week-weather-dialog">
    <!-- 天气图表 -->
    <div v-if="weatherWeek.length > 0" class="weather-chart-container">
      <div ref="weatherChart" class="weather-chart"></div>
    </div>

    <!-- 天气详情列表 -->
    <div v-if="weatherWeek.length > 0" class="weather-week-list">
      <el-card
        v-for="(day, index) in weatherWeek"
        :key="index"
        class="weather-day-card"
        shadow="hover"
      >
        <div class="weather-day-header">
          <span class="week-day">{{ day.week }}</span>
          <span class="date">{{ day.date }}</span>
        </div>
        <div class="weather-day-main">
          <span class="weather-icon">🌤️</span>
          <span class="weather-desc">{{ day.weather }}</span>
        </div>
        <div class="weather-temps">
          <span class="temp-high">{{ day.highest }}°C</span>
          <span class="temp-separator">/</span>
          <span class="temp-low">{{ day.lowest }}°C</span>
        </div>
        <div class="weather-sun">
          <span>🌅 {{ day.sunrise }}</span>
          <span>🌇 {{ day.sunset }}</span>
        </div>
      </el-card>
    </div>

    <!-- 穿衣建议 -->
    <div v-if="dressAdvice" class="dress-advice">
      <el-alert
        :title="dressAdvice"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <div v-if="isLoadingWeekWeather" class="loading-week-weather">
      <el-skeleton :rows="3" animated />
    </div>
  </div>

  <template #footer>
    <el-button @click="showWeekWeatherDialog = false">关闭</el-button>
    <el-button type="primary" @click="getWeekWeather" :loading="isLoadingWeekWeather">
      刷新预报
    </el-button>
  </template>
</el-dialog>


    <!-- 在适当位置添加AI分析按钮 -->
    <el-button
      class="ai-analysis-btn"
      type="primary"
      :icon="Magic"
      @click="showAIAnalysis"
      :loading="aiLoading"
    >
      AI行程综合分析
    </el-button>

    <el-dialog
      v-model="aiAnalysisVisible"
      title="🤖 AI行程综合分析"
      width="700px"
      :before-close="handleAIAnalysisClose"
    >
      <div class="ai-analysis-dialog">
        <div v-if="aiAnalysisResult" class="analysis-result">
          <div class="result-content">
            {{ aiAnalysisResult }}
          </div>
        </div>

        <div v-else-if="aiLoading" class="analysis-loading">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else class="analysis-prompt">
          <p>点击"开始分析"按钮获取基于以下信息的综合建议：</p>
          <ul class="analysis-sources">
            <li>📅 当月假期信息</li>
            <li>🌤️ 未来一周天气</li>
            <li>📋 当前行程计划</li>
          </ul>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleAIAnalysisClose">关闭</el-button>
        <el-button
          type="primary"
          :loading="aiLoading"
          @click="getAIAnalysis"
        >
          {{ aiLoading ? '分析中...' : '开始分析' }}
        </el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed, inject,watch } from 'vue'
import axios from 'axios'
import Qs from 'qs'
import { ElMessage } from 'element-plus'

// 导入图标
import {
  Search,
  Position,
  Location,
  Food,
  OfficeBuilding,
  ShoppingBag,
  Refresh,
  CopyDocument,
  View,
  Calendar  // 新增日历图标
} from '@element-plus/icons-vue'

// 实时天气数据（从外部传入）
const props = defineProps({
  weatherData: Object, // 实时天气数据
  discoveredPois: Array
})



// 监听 weatherData 的变化
watch(() => props.weatherData, (newVal, oldVal) => {
  console.log('🔄 ControlPanel weatherData 发生变化:')
  console.log('旧值:', oldVal)
  console.log('新值:', newVal)
  console.log('新值详情:', {
    city: newVal?.city,
    weather: newVal?.weather,
    temperature: newVal?.temperature,
    humidity: newVal?.humidity,
    wind: newVal?.wind,
    reportTime: newVal?.reportTime
  })
}, { deep: true, immediate: true })

const emit = defineEmits(['search-place', 'plan-route', 'add-to-itinerary', 'refresh-pois', 'category-change'])

// 在响应式数据中添加
const holidayData = ref([])
const showHolidayDialog = ref(false)
const isLoadingHoliday = ref(false)

// 替换原来的 getHolidayInfo 方法
const getHolidayInfo = async () => {
  isLoadingHoliday.value = true

  try {
    console.log('📅 通过后端获取休假信息')

    const response = await fetch('/api/holiday', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()

    if (data.success && data.data) {
      holidayData.value = data.data
      console.log('✅ 获取到休假信息:', holidayData.value)

      if (holidayData.value.length > 0) {
        showHolidayDialog.value = true
        ElMessage.success(`本月有 ${holidayData.value.length} 天休假`)
      } else {
        ElMessage.info('本月暂无休假安排')
      }
    } else {
      holidayData.value = []
      console.warn('❌ 未获取到有效节假日数据:', data)
      ElMessage.warning('未获取到休假信息')
    }
  } catch (error) {
    console.error('❌ 获取节假日失败:', error)
    holidayData.value = []
    ElMessage.error('获取休假信息失败')
  } finally {
    isLoadingHoliday.value = false
  }
}

// 格式化休假日期
const formatHolidayDate = (dateString) => {
  if (!dateString) return ''

  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    })
  } catch {
    return dateString
  }
}






import { Magic } from '@element-plus/icons-vue'

// 注入行程面板引用
const itineraryRef = inject('itineraryRef')

// 确保 weatherData 被正确定义（根据你原有的代码）
const weatherData = ref(null)

// AI 相关数据
const aiLoading = ref(false)
const aiAnalysisVisible = ref(false)
const aiAnalysisResult = ref('')

// 显示AI分析弹窗
const showAIAnalysis = () => {
  aiAnalysisVisible.value = true
}


const buildAnalysisPrompt = (itineraryData, daysCount, activitiesCount) => {
  // 使用组件中已经获取的数据
  const currentHolidays = holidayData.value || []
  const currentWeekWeather = weatherWeek.value || []
  const currentRealtimeWeather = props.weatherData || {}

  const prompt = `你是一个专业的旅行规划师。请基于以下信息提供全面的行程分析建议：

行程概览：
- 行程天数：${daysCount}天
- 活动数量：${activitiesCount}个

当月假期信息：
${currentHolidays.length > 0 ? currentHolidays.map(holiday =>
  `- ${holiday.name} (${holiday.date}): ${holiday.tip || '休假安排'}`
).join('\n') : '本月无假期安排'}

当前实时天气：
城市：${currentRealtimeWeather.city || '未知'}
天气：${currentRealtimeWeather.weather || '未知'}
温度：${currentRealtimeWeather.temperature || '未知'}°C
湿度：${currentRealtimeWeather.humidity || '未知'}%
风力：${currentRealtimeWeather.wind || '未知'}

未来一周天气预报：
${currentWeekWeather.length > 0 ? currentWeekWeather.map(day =>
  `- ${day.date} (${day.week}): ${day.weather}, ${day.lowest}°C~${day.highest}°C`
).join('\n') : '暂无一周天气数据'}

行程详细安排：
${JSON.stringify(itineraryData, null, 2)}

请从以下角度提供专业分析：
1. 时间安排合理性评估
2. 活动密度分析（是否过于紧凑或松散）
3. 考虑假期因素的出行建议
4. 天气适应性建议（结合实时天气和一周预报）
5. 行程优化建议
6. 潜在问题预警

请用中文回复，分析要具体、专业，并提供实用的改进建议。`

  // 打印完整的 prompt 到控制台
  console.log('🤖 AI分析完整提示词:')
  console.log('='.repeat(50))
  console.log(prompt)
  console.log('='.repeat(50))
  console.log('提示词长度:', prompt.length, '字符')
  console.log('使用的假期数据:', currentHolidays)
  console.log('使用的一周天气数据:', currentWeekWeather)
  console.log('使用的实时天气数据:', currentRealtimeWeather)

  return prompt
}

// 直接在前端调用 OpenAI API
const getAIAnalysis = async () => {
  aiLoading.value = true
  aiAnalysisResult.value = ''

  try {
    // 获取当前行程数据（原有逻辑不变）
    let itineraryData = []
    if (itineraryRef?.value) {
      if (typeof itineraryRef.value.getItineraryData === 'function') {
        itineraryData = itineraryRef.value.getItineraryData()
      } else {
        itineraryData = itineraryRef.value.itinerary || []
      }
    }

    // 检查必要数据
    if (!itineraryData.length) {
      ElMessage.warning('当前没有行程计划，请先添加行程')
      return
    }

    if (!props.weatherData) {
      ElMessage.warning('请先获取天气信息')
      return
    }

    console.log('🤖 发送AI分析请求...')

    // 改为调用自己的后端！
    const response = await fetch('/api/ai/analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        itineraryData: itineraryData,
        weatherData: props.weatherData
      })
    })

    const data = await response.json()

    if (data.success) {
      aiAnalysisResult.value = data.result
      ElMessage.success('AI分析完成')
    } else {
      throw new Error(data.error || '分析失败')
    }

  } catch (error) {
    console.error('AI分析失败:', error)
    ElMessage.error('AI分析失败: ' + error.message)
  } finally {
    aiLoading.value = false
  }
}

// 关闭弹窗
const handleAIAnalysisClose = () => {
  aiAnalysisVisible.value = false
  aiAnalysisResult.value = ''
}











// 导入 echarts
import * as echarts from 'echarts'

// 一周天气相关变量（使用原来的变量名）
const weatherWeek = ref([])
const dressAdvice = ref('')
const showWeekWeatherDialog = ref(false)
const isLoadingWeekWeather = ref(false)
const weatherChart = ref(null)

// 替换原来的 getWeekWeather 方法
const getWeekWeather = async () => {
  if (!props.weatherData) {
    ElMessage.warning('请先点击地图获取实时天气')
    return
  }

  isLoadingWeekWeather.value = true

  try {
    const response = await fetch('/api/weather/week', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        city: props.weatherData.city
      })
    })

    const data = await response.json()
    console.log('📅 一周天气API响应:', data)

    if (data.success && data.weatherWeek) {
      dressAdvice.value = data.dressAdvice || ''
      weatherWeek.value = data.weatherWeek

      console.log('✅ 获取到一周天气:', weatherWeek.value)
      showWeekWeatherDialog.value = true

      setTimeout(() => {
        drawChart()
      }, 100)

    } else {
      console.warn('❌ 未获取到一周天气数据:', data)
      ElMessage.warning('获取一周天气失败')
    }
  } catch (error) {
    console.error('❌ 获取一周天气失败:', error)
    ElMessage.error('获取一周天气失败')
  } finally {
    isLoadingWeekWeather.value = false
  }
}

// 绘制天气图表（保持原来的逻辑）
const drawChart = () => {
  if (!weatherWeek.value || weatherWeek.value.length === 0) return

  const highestArr = weatherWeek.value.map(item => item.highest)
  const lowestArr = weatherWeek.value.map(item => item.lowest)
  const sunriseArr = weatherWeek.value.map(item => item.sunrise)
  const sunsetArr = weatherWeek.value.map(item => item.sunset)
  const weatherArr = weatherWeek.value.map(item => item.weather)
  const weekArr = weatherWeek.value.map(item => item.week)

  const chartDom = weatherChart.value
  if (!chartDom) return

  const myChart = echarts.init(chartDom)

  const startDate = weatherWeek.value[0].date
  const endDate = weatherWeek.value[weatherWeek.value.length - 1].date
  const locationName = props.weatherData?.city || "未知地点"

  const option = {
    title: {
      text: `一周天气预报☁️ (${locationName} ${startDate} ~ ${endDate})`,
      textStyle: { color: '#303133', fontSize: 16 },
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        const dataIndex = params[0].dataIndex
        return (
          '日期：' + weekArr[dataIndex] + '<br>' +
          '最高气温：' + highestArr[dataIndex] + '℃<br>' +
          '最低气温：' + lowestArr[dataIndex] + '℃<br>' +
          '日出时间：' + sunriseArr[dataIndex] + '<br>' +
          '日落时间：' + sunsetArr[dataIndex] + '<br>' +
          '天气状况：' + weatherArr[dataIndex] + '<br>'
        )
      },
    },
    legend: {
      data: ['最高气温', '最低气温'],
      textStyle: { color: '#303133' },
      top: 40
    },
    grid: { top: 80, left: '3%', right: '4%', bottom: '3%', containLabel: true },
    toolbox: {
      feature: {
        saveAsImage: {
          title: '保存图片',
          pixelRatio: 2
        }
      },
      right: 10,
      top: 10
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: weekArr,
      axisLabel: { color: '#606266' },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#606266',
        formatter: '{value}°C'
      },
    },
    series: [
      {
        name: '最高气温',
        type: 'line',
        data: highestArr,
        lineStyle: { color: '#e6a23c', width: 3 },
        itemStyle: { color: '#e6a23c' },
        smooth: true
      },
      {
        name: '最低气温',
        type: 'line',
        data: lowestArr,
        lineStyle: { color: '#409eff', width: 3 },
        itemStyle: { color: '#409eff' },
        smooth: true
      },
    ],
  }

  myChart.setOption(option)

  window.addEventListener('resize', () => {
    myChart.resize()
  })
}


// 实时天气相关变量（新增）
const realtimeWeather = ref(null) // 使用 realtimeWeather 避免与一周天气冲突
const isLoadingRealtimeWeather = ref(false)


// 获取实时天气（使用高德API）
const getRealtimeWeather = async (cityName = '') => {
  isLoadingRealtimeWeather.value = true

  try {
    // 如果没有指定城市，使用默认城市编码（上海）
    const cityCode = cityName ? await getCityCode(cityName) : '310000' // 310000是上海市的编码

    const weatherKey = "3623efdd7327c543ffe6ccab8aded336"
    const weatherUrl = `https://restapi.amap.com/v3/weather/weatherInfo?key=${weatherKey}&city=${cityCode}&extensions=base`

    console.log("🌤️ ControlPanel 获取天气数据，城市编码:", cityCode)

    const response = await axios.get(weatherUrl)

    if (response.data.status === "1" && response.data.lives && response.data.lives.length > 0) {
      const weatherInfo = response.data.lives[0]
      console.log("✅ ControlPanel 天气数据获取成功:", weatherInfo)

      realtimeWeather.value = {
        city: weatherInfo.city,
        weather: weatherInfo.weather,
        temperature: weatherInfo.temperature,
        humidity: weatherInfo.humidity,
        wind: `${weatherInfo.winddirection}风 ${weatherInfo.windpower}级`,
        reportTime: weatherInfo.reporttime
      }

      ElMessage.success(`已获取${weatherInfo.city}的实时天气`)
    } else {
      console.error("❌ ControlPanel 天气数据获取失败:", response.data)
      ElMessage.warning('获取实时天气失败')
    }
  } catch (error) {
    console.error("❌ ControlPanel 天气API请求失败:", error)
    ElMessage.error('获取实时天气失败')
  } finally {
    isLoadingRealtimeWeather.value = false
  }
}

// 根据城市名获取城市编码（辅助函数）
const getCityCode = async (cityName) => {
  try {
    const geoKey = "3623efdd7327c543ffe6ccab8aded336"
    const geoUrl = `https://restapi.amap.com/v3/geocode/geo?key=${geoKey}&address=${encodeURIComponent(cityName)}`

    const response = await axios.get(geoUrl)
    if (response.data.status === "1" && response.data.geocodes && response.data.geocodes.length > 0) {
      return response.data.geocodes[0].adcode
    }
  } catch (error) {
    console.error('获取城市编码失败:', error)
  }
  return '310000' // 默认返回上海编码
}














// 组件卸载时清理 echarts 实例
import { onUnmounted } from 'vue'

onUnmounted(() => {
  if (weatherChart.value) {
    const chartInstance = echarts.getInstanceByDom(weatherChart.value)
    if (chartInstance) {
      chartInstance.dispose()
    }
  }
})




// 在响应式数据中添加
const locationKeyword = ref('')
const locationResults = ref([])
const isLoadingLocation = ref(false)

// 替换原来的 searchLocation 方法
const searchLocation = async () => {
  const keyword = locationKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索地点')
    return
  }

  isLoadingLocation.value = true
  locationResults.value = []

  try {
    const response = await fetch('/api/location/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        keyword: keyword
      })
    })

    const data = await response.json()
    console.log('🗺️ 地点搜索API响应:', data)

    if (data.success && data.data) {
      locationResults.value = data.data
      console.log('✅ 地点搜索结果:', locationResults.value)
      ElMessage.success(`找到 ${locationResults.value.length} 个相关地点`)
    } else {
      console.warn('❌ 未找到相关地点:', data)
      ElMessage.warning('未找到相关地点')
    }
  } catch (error) {
    console.error('❌ 地点搜索失败:', error)
    ElMessage.error('地点搜索失败')
  } finally {
    isLoadingLocation.value = false
  }
}

// 选择地点并在地图上显示
const selectLocation = (location) => {
  console.log('📍 选择地点:', location)

  // 通过地图引用跳转到该地点
  if (mapRef?.value) {
    // 调用地图组件的跳转方法
    mapRef.value.flyToLocation({
      lng: location.location.lng,
      lat: location.location.lat,
      name: location.name,
      address: location.address
    })

    ElMessage.success(`已跳转到 ${location.name}`)

    // 清空搜索结果
    locationResults.value = []
    locationKeyword.value = ''
  } else {
    ElMessage.error('地图组件未就绪')
  }
}













// 定义所有需要的响应式变量
const searchKeyword = ref('')
const startPoint = ref('')
const endPoint = ref('')
const selectedCategory = ref('all')
const briefIntro = ref('') // 景点简介内容
const isLoadingIntro = ref(false) // 加载状态
const showIntroDialog = ref(false) // 控制弹窗显示
const currentPlace = ref('') // 当前查询的景点名称

// 标记显示相关变量
const showMarkers = ref(false)
const mapRef = inject('mapRef')

// 标记控制方法
const toggleMarkers = () => {
  console.log('🗺️ 点击标记按钮，当前状态:', showMarkers.value)

  if (showMarkers.value) {
    // 如果当前显示标记，则清除
    clearMarkers()
    showMarkers.value = false
    ElMessage.info('已隐藏地图标记')
  } else {
    // 如果当前隐藏标记，则显示
    if (props.discoveredPois.length === 0) {
      ElMessage.warning('请先搜索周边获取POI数据')
      return
    }
    showCurrentMarkers()
    showMarkers.value = true
    ElMessage.success('已在地图显示标记')
  }
}

const showCurrentMarkers = () => {
  if (!mapRef?.value) {
    ElMessage.error('地图组件未就绪')
    return
  }

  if (!props.discoveredPois.length) {
    ElMessage.warning('没有可显示的POI数据，请先搜索周边')
    return
  }

  console.log('🗺️ 显示当前POI标记，数量:', props.discoveredPois.length)

  // 转换POI数据格式以匹配行程面板的格式
  const markersData = props.discoveredPois.map(poi => {
    let lng, lat

    // 检查不同的位置数据格式
    if (poi.lng && poi.lat) {
      // 格式1: 直接包含lng, lat
      lng = poi.lng
      lat = poi.lat
    } else if (poi.location && poi.location.lng && poi.location.lat) {
      // 格式2: 包含location对象
      lng = poi.location.lng
      lat = poi.location.lat
    } else if (poi.location && typeof poi.location === 'string') {
      // 格式3: location是字符串 "lng,lat"
      const [lngStr, latStr] = poi.location.split(',')
      lng = parseFloat(lngStr)
      lat = parseFloat(latStr)
    } else {
      console.warn('❌ POI缺少位置信息:', poi.name)
      return null
    }

    // 构建与行程面板相同的格式
        return {
      id: poi.id,
      name: poi.name,
      lng: lng,
      lat: lat,
      details: poi.address || poi.details || '',
      address: poi.address || '',
      type: poi.type || '', // 确保type有默认值
      typecode: poi.typecode || '', // 确保typecode有默认值
      // 确保包含行程面板需要的字段
      rawPoiData: poi
    }
  }).filter(poi => poi !== null) // 过滤掉无效的POI

  console.log('🗺️ 转换后的标记数据数量:', markersData.length)

  // 根据当前选择的类别过滤POI
  const filteredPois = filterPoisByCategory(markersData, selectedCategory.value)
  console.log('🗺️ 过滤后的POI数量:', filteredPois.length)

  // 在地图上显示标记
  if (filteredPois.length > 0) {
    mapRef.value.showMultipleActivities(filteredPois)
    console.log('✅ 成功调用地图标记方法')
  } else {
    ElMessage.warning('当前类别下没有可显示的POI')
  }
}

const filterPoisByCategory = (pois, category) => {
  if (category === 'all') return pois

  const categoryMap = {
    scenic: ['风景名胜', '景点', '110000'],
    restaurant: ['餐饮', '餐厅', '050000'],
    hotel: ['酒店', '住宿', '商务住宅', '100000'],
    shopping: ['购物', '商场', '060000']
  }

  const keywords = categoryMap[category] || []

  return pois.filter(poi => {
    // 安全地检查 poi 的 type 和 typecode 字段
    const poiType = poi.type || ''
    const poiTypecode = poi.typecode || ''

    return keywords.some(keyword =>
      poiType.includes(keyword) ||
      poiTypecode.includes(keyword)
    )
  })
}

const clearMarkers = () => {
  if (mapRef?.value) {
    mapRef.value.removeAllMarkers()
    console.log('🗺️ 已清除地图标记')
  }
}


// 替换原来的 getBriefIntro 方法
const getBriefIntro = async (place) => {
  if (!place.trim()) return

  currentPlace.value = place
  isLoadingIntro.value = true
  briefIntro.value = ''
  showIntroDialog.value = true

  try {
    const response = await fetch('/api/scenic/intro', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        place: place
      })
    })

    const data = await response.json()
    console.log('景点简介API响应:', data)

    if (data.success) {
      briefIntro.value = data.content
      if (data.content) {
        ElMessage.success('成功获取景点简介')
      } else {
        ElMessage.info('暂无该景点简介信息')
      }
    } else {
      briefIntro.value = ''
      ElMessage.error('获取景点简介失败')
    }
  } catch (error) {
    console.error('获取景点简介失败:', error)
    briefIntro.value = ''
    ElMessage.error('获取景点简介失败')
  } finally {
    isLoadingIntro.value = false
  }
}

// 事件处理
const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (keyword) {
    // 触发搜索事件（给地图组件）
    emit('search-place', keyword)
    // 同时获取景点简介（会打开弹窗）
    getBriefIntro(keyword)
    searchKeyword.value = ''

    // 搜索后自动清除标记（因为搜索结果会替换POI列表）
    if (showMarkers.value) {
      clearMarkers()
      showMarkers.value = false
      ElMessage.info('已清除旧标记，请重新点击显示标记')
    }
  }
}

// 复制简介功能
const copyBriefIntro = async () => {
  if (!briefIntro.value) return

  try {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = briefIntro.value
    const plainText = tempDiv.textContent || tempDiv.innerText || ''

    await navigator.clipboard.writeText(plainText)
    ElMessage.success('简介已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

const handlePlanRoute = () => {
  if (startPoint.value.trim() && endPoint.value.trim()) {
    emit('plan-route', {
      start: startPoint.value.trim(),
      end: endPoint.value.trim()
    })
    startPoint.value = ''
    endPoint.value = ''
  }
}

const handleCategoryChange = (category) => {
  console.log('🔍 ControlPanel 切换类别:', category)
  emit('category-change', category)

  // 如果标记显示开启，更新显示的标记
  if (showMarkers.value) {
    // 清除旧标记，显示新类别的标记
    clearMarkers()
    showCurrentMarkers()
  }
}

const handleRefreshPois = () => {
  console.log('🔄 手动刷新POI')
  emit('refresh-pois', selectedCategory.value) // 传递当前类别

  // 刷新后自动清除标记，让用户决定是否重新显示
  if (showMarkers.value) {
    clearMarkers()
    showMarkers.value = false
    ElMessage.info('已刷新POI数据，请重新点击显示标记')
  }
}

const handleAddToItinerary = (poi) => {
  console.log('➕ 添加到行程:', poi)
  emit('add-to-itinerary', poi)
}

// 辅助函数...
const getIconByType = (typecode) => {
  if (!typecode) return Location
  const typePrefix = typecode.toString().substring(0, 2)
  if (typePrefix === '10') return OfficeBuilding
  if (typePrefix === '05') return Food
  if (typePrefix === '06') return ShoppingBag
  if (typePrefix === '11') return Location
  return Location
}

const getPoiCategory = (typecode) => {
  if (!typecode) return 'other'
  const typePrefix = typecode.toString().substring(0, 2)
  if (typePrefix === '11') return 'scenic'
  if (typePrefix === '05') return 'restaurant'
  if (typePrefix === '10') return 'hotel'
  if (typePrefix === '06') return 'shopping'
  return 'other'
}

const getCategoryName = (category) => {
  const names = {
    scenic: '景点',
    restaurant: '餐饮',
    hotel: '酒店',
    shopping: '购物',
    other: '其他'
  }
  return names[category] || '其他'
}

const getCategoryTagType = (category) => {
  const colors = {
    scenic: 'primary',
    restaurant: 'warning',
    hotel: 'success',
    shopping: 'info',
    other: 'info'
  }
  return colors[category] || 'info'
}

const formatDistance = (distance) => {
  const dist = parseInt(distance)
  if (dist < 1000) {
    return `${dist}米`
  } else {
    return `${(dist / 1000).toFixed(1)}公里`
  }
}

const formatTime = (timeString) => {
  if (!timeString) return ''
  try {
    const date = new Date(timeString)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return timeString
  }
}

// 计算属性
const filteredPois = computed(() => {
  if (selectedCategory.value === 'all') {
    return props.discoveredPois
  }
  const categoryCodes = categoryTypeMap[selectedCategory.value]
  if (!categoryCodes) return props.discoveredPois
  return props.discoveredPois.filter(poi => {
    const poiTypePrefix = poi.typecode?.toString().substring(0, 2) || ''
    return categoryCodes.some(code => poiTypePrefix.startsWith(code))
  })
})

// 修改：只显示前10个POI
const displayedPois = computed(() => filteredPois.value.slice(0, 10))

const emptyDescription = computed(() => {
  if (selectedCategory.value === 'all') {
    return props.discoveredPois.length === 0 ? '点击"搜索周边"获取周边信息' : '暂无数据'
  }
  return `当前区域暂无${getCategoryName(selectedCategory.value) || '该类别'}信息`
})

const categoryTypeMap = {
  scenic: ['11'],
  restaurant: ['05'],
  hotel: ['10'],
  shopping: ['06']
}
</script>

<style scoped>
.ai-analysis-btn {
  width: 100%;
  margin-bottom: 16px;
}

.ai-analysis-dialog {
  min-height: 300px;
}

.analysis-result {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.result-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
}

.analysis-loading {
  padding: 20px;
}

.analysis-prompt {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.analysis-sources {
  list-style: none;
  padding: 0;
  margin: 20px 0 0 0;
}

.analysis-sources li {
  padding: 8px 0;
  font-size: 14px;
}

.weather-info {
  background: #f0f9ff;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  border-left: 4px solid #409eff;
}

.weather-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.weather-info p {
  margin: 0;
  font-size: 13px;
  color: #606266;
}

.suggestion-result {
  background: #f6ffed;
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid #52c41a;
}

.suggestion-result h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.suggestion-content {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
}
/* 休假信息样式 */
.holiday-section {
  margin-bottom: 20px;
}

.holiday-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.holiday-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.holiday-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.holiday-preview {
  padding: 5px 0;
}

.holiday-item {
  margin: 8px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.more-holidays {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.no-holiday {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.holiday-icon {
  margin-right: 8px;
}

/* 休假详情弹窗样式 */
.holiday-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.holiday-list {
  padding: 10px 0;
}

.holiday-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0;
}

.holiday-info .date {
  color: #909399;
  font-size: 13px;
}

.holiday-tip {
  margin: 8px 0 0 0;
  padding: 8px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
  font-size: 12px;
  color: #606266;
}

.no-holiday-data {
  padding: 40px 0;
}

/* 时间线样式调整 */
:deep(.el-timeline-item__timestamp) {
  color: #409eff;
  font-weight: 500;
}

:deep(.el-timeline-item__node) {
  background-color: #409eff;
}

.control-panel {
padding: 20px;
height: 100%;
/* 恢复滚动 */
overflow-y: auto;
}

/* 移除之前添加的flex布局相关样式，恢复原来的样式 */
.weather-section, .search-section, .route-section, .discovery-section {
margin-bottom: 25px;
}

/* 其他样式保持不变 */
.weather-card {
margin-top: 10px;
}

.weather-info p {
margin: 8px 0;
display: flex;
align-items: center;
gap: 8px;
}

.card-header {
display: flex;
justify-content: space-between;
align-items: center;
}

.discovery-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 15px;
}

.discovery-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-filter {
margin-bottom: 15px;
}

.debug-info {
background: #f5f5f5;
padding: 8px;
border-radius: 4px;
margin-bottom: 10px;
font-size: 12px;
color: #666;
}

:deep(.el-radio-group) {
width: 100%;
}

:deep(.el-radio-button) {
flex: 1;
}

:deep(.el-radio-button__inner) {
width: 100%;
padding: 8px 4px;
}

.poi-list {
max-height: 400px;
overflow-y: auto;
}

.poi-card {
margin-bottom: 10px;
}

.poi-header {
display: flex;
align-items: center;
font-weight: bold;
font-size: 14px;
margin-bottom: 5px;
}

.poi-icon {
color: #409eff;
margin-right: 8px;
flex-shrink: 0;
}

.poi-name {
flex-grow: 1;
overflow: hidden;
white-space: nowrap;
text-overflow: ellipsis;
margin-right: 8px;
}

.poi-address {
color: #909399;
font-size: 12px;
margin: 5px 0;
}

.poi-footer {
display: flex;
justify-content: space-between;
align-items: center;
margin-top: 8px;
}

.poi-distance {
font-size: 12px;
color: #67c23a;
font-weight: 500;
}

.add-button {
margin-top: 0;
}

/* 天气头部样式 */
.weather-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

/* 实时天气样式 */
.weather-main {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.weather-icon {
  font-size: 24px;
  margin-right: 10px;
}

.weather-temp {
  font-size: 24px;
  font-weight: bold;
  color: #e6a23c;
  margin-right: 10px;
}

.weather-desc {
  font-size: 16px;
  color: #606266;
}

.weather-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.weather-details p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

/* 一周天气弹窗样式 */
.week-weather-dialog {
  max-height: 70vh;
  overflow-y: auto;
}

.weather-chart-container {
  height: 300px;
  margin-bottom: 20px;
}

.weather-chart {
  width: 100%;
  height: 100%;
}

.weather-week-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.weather-day-card {
  text-align: center;
  padding: 12px;
}

.weather-day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.week-day {
  font-weight: bold;
  color: #303133;
}

.date {
  font-size: 12px;
  color: #909399;
}

.weather-day-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 10px 0;
}

.weather-temps {
  margin: 8px 0;
}

.temp-high {
  font-size: 18px;
  font-weight: bold;
  color: #e6a23c;
}

.temp-low {
  font-size: 14px;
  color: #409eff;
}

.temp-separator {
  margin: 0 4px;
  color: #909399;
}

.weather-sun {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.dress-advice {
  margin-top: 20px;
}

.loading-week-weather {
  padding: 20px;
}
</style>
