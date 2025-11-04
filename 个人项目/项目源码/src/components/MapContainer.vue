<template>
  <div id="map" class="map-container">
    <div v-if="!isMapLoaded" class="map-loading">
      地图加载中...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineEmits, defineExpose } from 'vue'
import axios from 'axios'

const emit = defineEmits([
  'location-click',
  'weather-data',
  'location-details',
  'pois-found',
  'poi-marker-click'
])

// 响应式数据
const isMapLoaded = ref(false)
const map = ref(null)
const currentPois = ref([])
const currentCategory = ref('all')
const markers = ref([]) // 存储所有标记
let searchTimeout = null

// 类别映射
const categoryTypeMap = {
  all: ['050000', '070000', '120000', '110000', '060000'], // 全部类别
  scenic: ['110000'], // 风景名胜
  restaurant: ['050000'], // 餐饮服务
  hotel: ['100000'], // 商务住宅
  shopping: ['060000'] // 购物服务
}

// 获取安全的 AMap 引用
const getAMap = () => {
  return window.AMap
}

// 检查 AMap 是否可用
const isAMapReady = () => {
  const amap = getAMap()
  return amap &&
    typeof amap.Map !== 'undefined'
}

// 初始化地图
const initMap = () => {
  try {
    const amap = getAMap()

    if (!amap) {
      console.error('❌ AMap 未定义')
      return
    }

    if (!isAMapReady()) {
      console.error('❌ AMap 核心类未完全加载')
      setTimeout(initMap, 500)
      return
    }

    console.log('✅ AMap 核心类已就绪，开始创建地图')

    // 创建地图实例
    map.value = new amap.Map("map", {
      center: [121.5063, 31.2814],
      zoom: 15,
      viewMode: '2D'
    })

    console.log('🗺️ 地图实例创建成功')

    isMapLoaded.value = true
    console.log('🗺️ 地图完全初始化成功')

    map.value.on('click', handleMapClick)

    // 初始搜索
    setTimeout(searchVisiblePois, 1000)

  } catch (error) {
    console.error('❌ 地图初始化失败:', error)
  }
}


// 使用 REST API 搜索可视区域 POI
const searchVisiblePois = async (category = null) => {
  if (!map.value) return

  // 如果传入了新的类别，更新当前类别
  if (category !== null) {
    currentCategory.value = category
  }

  try {
    // 获取地图可视区域边界
    const bounds = map.value.getBounds()
    if (!bounds) {
      console.error('❌ 无法获取地图边界')
      return
    }

    // 获取边界坐标
    const southwest = bounds.getSouthWest()
    const northeast = bounds.getNorthEast()

    // 计算可视区域的宽度和高度
    const width = northeast.lng - southwest.lng
    const height = northeast.lat - southwest.lat

    console.log('🗺️ ========== 可视区域搜索 ==========')
    console.log('📏 可视区域边界:')
    console.log('  左下:', `${southwest.lng.toFixed(6)},${southwest.lat.toFixed(6)}`)
    console.log('  右上:', `${northeast.lng.toFixed(6)},${northeast.lat.toFixed(6)}`)
    console.log('📏 可视区域尺寸:', {
      经度跨度: width.toFixed(6),
      纬度跨度: height.toFixed(6),
      大致宽度: (width * 111).toFixed(2) + 'km',
      大致高度: (height * 111).toFixed(2) + 'km'
    })
    console.log('🎯 搜索策略: 单次API请求，返回最重要POI')
    console.log('🎯 当前搜索类别:', currentCategory.value)

    // 使用单次矩形搜索
    const pois = await searchByBounds(southwest, northeast, currentCategory.value)
    console.log(`✅ 搜索成功! 找到 ${pois.length} 个POI`)

    // 显示POI分布信息
    if (pois.length > 0) {
      console.log('📊 POI分布信息:')
      pois.forEach((poi, index) => {
        console.log(`  ${index + 1}. ${poi.name}`)
        console.log(`     位置: 经度${poi.location.lng.toFixed(6)}, 纬度${poi.location.lat.toFixed(6)}`)
        console.log(`     地址: ${poi.address}`)
        console.log(`     类型: ${poi.type}`)
      })
    }

    // 更新当前POI列表
    currentPois.value = pois

    // 发射POI数据
    if (pois.length > 0) {
      emit('pois-found', pois)
    } else {
      emit('pois-found', [])
    }
  } catch (error) {
    console.error('❌ POI搜索失败:', error)
    emit('pois-found', [])
  }
}

// 矩形边界搜索 REST API - 单次请求
const searchByBounds = async (southwest, northeast, category = 'all') => {
  const apiKey = "3623efdd7327c543ffe6ccab8aded336"
  const types = categoryTypeMap[category]?.join('|') || categoryTypeMap.all.join('|')

  // 构建矩形边界参数
  const polygon = `${southwest.lng},${southwest.lat}|${northeast.lng},${northeast.lat}`

  // 搜索整个可视区域，返回10个最重要的POI
  const url = `https://restapi.amap.com/v3/place/polygon?key=${apiKey}&polygon=${polygon}&types=${types}&offset=10&page=1&extensions=base`

  console.log('🌐 API请求信息:')
  console.log('  边界参数:', polygon)
  console.log('  类别代码:', types)

  try {
    const response = await axios.get(url, {
      timeout: 5000
    })

    console.log('📊 API响应状态:', response.data.status)
    console.log('📊 API返回POI数量:', response.data.pois ? response.data.pois.length : 0)

    if (response.data.status === '1' && response.data.pois) {
      // 直接返回高德地图智能选择的最重要POI
      return response.data.pois.slice(0, 10).map(poi => ({
        id: poi.id,
        name: poi.name,
        type: poi.type,
        typecode: poi.typecode,
        address: poi.address,
        location: {
          lng: parseFloat(poi.location.split(',')[0]),
          lat: parseFloat(poi.location.split(',')[1])
        },
        distance: poi.distance || 0,
        tel: poi.tel || '',
        website: poi.website || ''
      }))
    } else {
      console.warn('❌ API返回错误:', response.data)
      return []
    }
  } catch (error) {
    console.error('❌ API请求失败:', error)
    return []
  }
}




// 可以删除这个函数，因为现在使用矩形边界搜索
const calculateRadius = (zoom) => {
   const radiusMap = {
    10: 5000, // 缩放级别10 -> 5km
     11: 3000, // 11 -> 3km
     12: 2000, // 12 -> 2km
     13: 1000, // 13 -> 1km
     14: 500, // 14 -> 500m
     15: 300, // 15 -> 300m
     16: 200, // 16 -> 200m
     17: 100, // 17 -> 100m
     18: 50 // 18 -> 50m
   }
   return radiusMap[zoom] || 1000
}


// 处理地图点击
const handleMapClick = (event) => {
  const lng = event.lnglat.lng
  const lat = event.lnglat.lat

  console.log('🗺️ 地图点击坐标:', lng, lat)
  emit('location-click', { lnglat: [lng, lat], lng, lat })
  getLocationDetails(lng, lat)
}

// 逆地理编码
const getLocationDetails = (lng, lat) => {
  const geoKey = "3623efdd7327c543ffe6ccab8aded336"
  const geoUrl = `https://restapi.amap.com/v3/geocode/regeo?key=${geoKey}&location=${lng},${lat}`

  axios.get(geoUrl)
    .then((res) => {
      if (res.data.status === "1") {
        const addressInfo = res.data.regeocode.addressComponent
        const locationDetails = res.data.regeocode

        console.log("📍 位置详情:", locationDetails.formatted_address)

        emit('location-details', {
          city: addressInfo.adcode,
          locationDetails: locationDetails,
          formattedAddress: locationDetails.formatted_address
        })

        // 调用真实天气API
        getWeatherData(addressInfo.adcode)
      }
    })
    .catch((err) => console.log("逆地理编码:", err.message))
}

// 获取实时天气信息
const getWeatherData = (cityCode) => {
  const weatherKey = "3623efdd7327c543ffe6ccab8aded336" // 使用同一个key
  const weatherUrl = `https://restapi.amap.com/v3/weather/weatherInfo?key=${weatherKey}&city=${cityCode}&extensions=base`

  console.log("🌤️ 获取天气数据，城市编码:", cityCode)

  axios.get(weatherUrl)
    .then((response) => {
      if (response.data.status === "1" && response.data.lives && response.data.lives.length > 0) {
        const weatherInfo = response.data.lives[0]
        console.log("✅ 天气数据获取成功:", weatherInfo)

        const weatherData = {
          city: weatherInfo.city,
          weather: weatherInfo.weather,
          temperature: weatherInfo.temperature,
          humidity: weatherInfo.humidity,
          wind: `${weatherInfo.winddirection}风 ${weatherInfo.windpower}级`,
          reportTime: weatherInfo.reporttime
        }

        emit('weather-data', weatherData)
      } else {
        console.error("❌ 天气数据获取失败:", response.data)
        // 如果失败，发送默认数据
        emit('weather-data', {
          city: '未知',
          weather: '未知',
          temperature: '--',
          humidity: '--',
          wind: '--',
          reportTime: '--'
        })
      }
    })
    .catch((error) => {
      console.error("❌ 天气API请求失败:", error)
      // 如果请求失败，发送默认数据
      emit('weather-data', {
        city: '未知',
        weather: '未知',
        temperature: '--',
        humidity: '--',
        wind: '--',
        reportTime: '--'
      })
    })
}

// 清除所有标记
const clearAllMarkers = () => {
  if (map.value && markers.value.length > 0) {
    markers.value.forEach(marker => {
      map.value.remove(marker)
    })
    markers.value = []
  }
}





// 添加标记到地图 - 使用官方推荐的方法
const addMarker = (lng, lat, title, content) => {
  if (!map.value) return

  const amap = getAMap()

  // 创建标记 - 使用官方推荐的偏移量
  const marker = new amap.Marker({
    position: [lng, lat],
    offset: new amap.Pixel(0, -0) // 官方推荐的偏移量
  })

  // 添加到地图
  marker.setMap(map.value)
  markers.value.push(marker)

  // 添加点击事件
  marker.on('click', () => {
    const infoWindow = new amap.InfoWindow({
      content: `<div class="marker-info">
        <h3>${title}</h3>
        <p>${content || '暂无详细信息'}</p>
      </div>`,
      offset: new amap.Pixel(0, 0)
    })
    infoWindow.open(map.value, marker.getPosition())
  })

  return marker
}



// 显示活动位置
const showActivityOnMap = (activity) => {
  if (!activity.lng || !activity.lat) {
    console.warn('活动缺少经纬度信息:', activity)
    return
  }

  clearAllMarkers()

  const marker = addMarker(
    activity.lng,
    activity.lat,
    activity.name,
    activity.details || activity.address
  )

  // 移动到标记位置
  if (map.value) {
    map.value.setCenter([activity.lng, activity.lat])
    map.value.setZoom(16)
  }

  console.log('📍 在地图上显示活动:', activity.name)
}

// 暴露的方法
const searchPlace = (keyword) => {
  if (!map.value) return
  console.log('搜索地点:', keyword)

  // 使用 REST API 进行关键字搜索
  const center = map.value.getCenter()
  searchByKeyword(keyword, center.lng, center.lat)
}

// 关键字搜索
const searchByKeyword = async (keyword, lng, lat) => {
  const apiKey = "3623efdd7327c543ffe6ccab8aded336"
  const radius = calculateRadius(map.value.getZoom())

  const url = `https://restapi.amap.com/v3/place/around?key=${apiKey}&location=${lng},${lat}&radius=${radius}&keywords=${encodeURIComponent(keyword)}&offset=10&page=1&extensions=base`

  try {
    const response = await axios.get(url)

    if (response.data.status === '1' && response.data.pois) {
      const pois = response.data.pois.map(poi => ({
        id: poi.id,
        name: poi.name,
        type: poi.type,
        typecode: poi.typecode,
        address: poi.address,
        location: {
          lng: parseFloat(poi.location.split(',')[0]),
          lat: parseFloat(poi.location.split(',')[1])
        },
        distance: poi.distance,
        tel: poi.tel || '',
        website: poi.website || ''
      }))

      // 直接发射搜索结果的POI数据
      emit('pois-found', pois)
    } else {
      emit('pois-found', [])
    }
  } catch (error) {
    console.error('❌ 关键字搜索失败:', error)
    emit('pois-found', [])
  }
}

// 清除POI显示
const clearPois = () => {
  emit('pois-found', [])
}

const planRoute = (start, end) => {
  if (!map.value) return
  console.log('路径规划:', start, '->', end)
}

// 刷新POI - 修改为使用矩形边界搜索
const refreshPois = (category = 'all') => {
  console.log('🔄 手动刷新POI，使用矩形边界搜索')
  searchVisiblePois(category)
}

// 切换搜索类别
const changeSearchCategory = (category) => {
  console.log('切换搜索类别:', category)
  currentCategory.value = category
  // 切换类别时也使用矩形边界搜索当前可视区域
  searchVisiblePois(category)
}

onMounted(() => {
  console.log('🚀 MapContainer 挂载')

  if (typeof window.AMap !== 'undefined') {
    console.log('📜 AMap 已加载，直接初始化')
    initMap()
  } else {
    const script = document.createElement("script")
    // 升级到 2.0 版本
    script.src = "https://webapi.amap.com/maps?v=2.0&key=d114d311745c4a00a306b678630835ba"
    script.onload = () => {
      console.log('✅ 地图脚本加载完成')
      setTimeout(initMap, 100)
    }
    script.onerror = () => console.error('❌ 脚本加载失败')
    document.head.appendChild(script)
  }
})

// 绘制行政区域边界（可选功能）
const drawAdministrativeBoundary = async (areaName, lng, lat) => {
  try {
    const apiKey = "3623efdd7327c543ffe6ccab8aded336"

    // 首先获取区域的adcode
    const districtUrl = `https://restapi.amap.com/v3/config/district?key=${apiKey}&keywords=${encodeURIComponent(areaName)}&subdistrict=0`
    const districtResponse = await axios.get(districtUrl)

    if (districtResponse.data.status === '1' && districtResponse.data.districts.length > 0) {
      const adcode = districtResponse.data.districts[0].adcode

      // 获取边界数据
      const boundaryUrl = `https://restapi.amap.com/v3/config/district?key=${apiKey}&keywords=${adcode}&subdistrict=0&extensions=all`
      const boundaryResponse = await axios.get(boundaryUrl)

      if (boundaryResponse.data.status === '1' && boundaryResponse.data.districts[0].polyline) {
        const polyline = boundaryResponse.data.districts[0].polyline
        drawBoundaryOnMap(polyline, areaName)
      }
    }
  } catch (error) {
    console.warn('❌ 获取区域边界失败:', error)
    // 即使没有边界数据，也已经完成了跳转
  }
}

// 在地图上绘制边界
const drawBoundaryOnMap = (polyline, areaName) => {
  const amap = getAMap()

  // 解析边界坐标
  const boundaries = polyline.split('|').map(boundary => {
    return boundary.split(';').map(point => {
      const [lng, lat] = point.split(',')
      return [parseFloat(lng), parseFloat(lat)]
    })
  })

  // 绘制每个边界
  boundaries.forEach((boundary, index) => {
    const polygon = new amap.Polygon({
      path: boundary,
      strokeColor: '#409EFF',
      strokeWeight: 3,
      strokeOpacity: 0.8,
      fillColor: '#409EFF',
      fillOpacity: 0.2
    })

    polygon.setMap(map.value)
    markers.value.push(polygon) // 将多边形也加入标记管理

    // 添加信息窗口
    const infoWindow = new amap.InfoWindow({
      content: `<div class="area-info">
        <h3>${areaName}</h3>
        <p>行政区域边界</p>
      </div>`,
      offset: new amap.Pixel(0, -10)
    })

    // 计算中心点
    const center = calculatePolygonCenter(boundary)
    infoWindow.open(map.value, center)
  })
}

// 计算多边形中心点
const calculatePolygonCenter = (points) => {
  let totalLng = 0
  let totalLat = 0
  points.forEach(point => {
    totalLng += point[0]
    totalLat += point[1]
  })
  return [totalLng / points.length, totalLat / points.length]
}

// 在 MapContainer 的 defineExpose 中添加
defineExpose({
  searchPlace,
  planRoute,
  clearPois,
  refreshPois,
  changeSearchCategory,
  showActivityOnMap,
  clearAllMarkers,
  // 新增标记相关方法
  addMarkerToMap: addMarker,
  removeAllMarkers: clearAllMarkers,
  // 确保有这个方法
  showMultipleActivities: (activities) => {
    clearAllMarkers()
    console.log('🗺️ 在地图上显示活动:', activities.length)
    activities.forEach(activity => {
      if (activity.lng && activity.lat) {
        addMarker(
          activity.lng,
          activity.lat,
          activity.name,
          activity.details || activity.address
        )
      }
    })
  },

  flyToLocation: (location) => {
    if (!map.value) return

    const { lng, lat, name, address } = location

    // 清除现有标记
    clearAllMarkers()

    // 跳转到目标位置
    map.value.setCenter([lng, lat])
    map.value.setZoom(12) // 调整到合适的缩放级别

    // 添加标记
    addMarker(lng, lat, name, address)

    // 如果是行政区域，尝试绘制边界（需要额外的边界数据）
    if (name.includes('省') || name.includes('市') || name.includes('区') || name.includes('县')) {
      // 这里可以调用行政区域边界API来绘制区域
      drawAdministrativeBoundary(name, lng, lat)
    }

    console.log(`🗺️ 已跳转到: ${name}`)
  }


})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 20px;
  border-radius: 8px;
}

/* 自定义标记样式 */
.custom-marker {
  background: white;
  border: 2px solid #409eff;
  border-radius: 20px;
  padding: 5px 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  white-space: nowrap;
}

.marker-icon {
  font-size: 16px;
}

.marker-title {
  font-weight: bold;
  color: #409eff;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 信息窗口样式 */
.marker-info {
  padding: 10px;
  max-width: 200px;
}

.marker-info h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 14px;
}

.marker-info p {
  margin: 0;
  color: #606266;
  font-size: 12px;
}

/* 地点搜索样式 */
.location-search-section {
  margin-bottom: 20px;
}

.location-results {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.location-card {
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.location-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.location-info {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.location-icon {
  color: #409eff;
  margin-top: 2px;
  flex-shrink: 0;
}

.location-details {
  flex: 1;
  min-width: 0;
}

.location-name {
  margin: 0 0 4px 0;
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

.location-address {
  margin: 0 0 2px 0;
  font-size: 12px;
  color: #606266;
}

.location-type {
  margin: 0;
  font-size: 11px;
  color: #909399;
  font-style: italic;
}

/* 区域信息窗口样式 */
.area-info {
  padding: 8px;
  min-width: 120px;
}

.area-info h3 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
}

.area-info p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}
</style>
