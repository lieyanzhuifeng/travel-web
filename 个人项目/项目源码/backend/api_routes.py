from flask import Blueprint, request, jsonify
import os
import requests
import json
from openai import OpenAI

api_bp = Blueprint('api', __name__)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', 'sk-RrolPLWPWB0yemF95aF9De5663C14b0cA26d9a5c4dF08e48'),
    base_url=os.getenv('OPENAI_BASE_URL', 'https://api.v3.cm/v1')
)

# 高德地图API密钥
AMAP_API_KEY = "3623efdd7327c543ffe6ccab8aded336"
TIANAPI_KEY = "1e12d5d1fb06599d02ef546b73e2c360"


@api_bp.route('/ai/analysis', methods=['POST'])
def ai_analysis():
    """AI行程分析"""
    try:
        data = request.get_json()
        itinerary_data = data.get('itineraryData', [])
        weather_data = data.get('weatherData', {})

        # 构建提示词
        days_count = len(itinerary_data)
        activities_count = sum(len(day.get('items', [])) for day in itinerary_data)

        prompt = f"""
        请分析这个{days_count}天旅行行程（共{activities_count}个活动）：
        {itinerary_data}

        天气情况：{weather_data}

        请给出行程优化建议和天气适应性分析。
        """

        # 调用AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )

        result = response.choices[0].message.content
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        print(f"AI分析错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/holiday', methods=['GET'])
def get_holiday():
    """获取休假信息"""
    try:
        import datetime
        current_month = datetime.datetime.now().month
        formatted_month = str(current_month).zfill(2)
        date = f"{datetime.datetime.now().year}-{formatted_month}"

        response = requests.post(
            'https://apis.tianapi.com/jiejiari/index',
            data={
                'key': TIANAPI_KEY,
                'date': date,
                'type': 2
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        data = response.json()

        if data.get('code') == 200 and data.get('result', {}).get('list'):
            # 过滤出休假日期
            holiday_data = [item for item in data['result']['list'] if item.get('isnotwork') == 1]
            return jsonify({'success': True, 'data': holiday_data})
        else:
            return jsonify({'success': False, 'error': '未获取到休假信息'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/scenic/intro', methods=['POST'])
def get_scenic_intro():
    """获取景点简介"""
    try:
        data = request.get_json()
        place = data.get('place', '')

        response = requests.post(
            'https://apis.tianapi.com/scenic/index',
            data={
                'key': TIANAPI_KEY,
                'word': place
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        data = response.json()

        if data.get('code') == 200 and data.get('result', {}).get('list'):
            intro_content = data['result']['list'][0].get('content', '')
            return jsonify({'success': True, 'content': intro_content})
        else:
            return jsonify({'success': True, 'content': ''})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/weather/week', methods=['POST'])
def get_week_weather():
    """获取一周天气"""
    try:
        data = request.get_json()
        city = data.get('city', '')

        response = requests.post(
            'https://apis.tianapi.com/tianqi/index',
            data={
                'key': TIANAPI_KEY,
                'city': city,
                'type': '7'
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        data = response.json()

        if data.get('code') == 200 and data.get('result', {}).get('list'):
            weather_list = data['result']['list']
            formatted_weather = []
            for item in weather_list:
                formatted_weather.append({
                    'week': item.get('week', ''),
                    'date': item.get('date', ''),
                    'lowest': float(item.get('lowest', 0)),
                    'highest': float(item.get('highest', 0)),
                    'weather': item.get('weather', ''),
                    'sunrise': item.get('sunrise', ''),
                    'sunset': item.get('sunset', '')
                })
            dress_advice = weather_list[0].get('tips', '') if weather_list else ''

            return jsonify({
                'success': True,
                'weatherWeek': formatted_weather,
                'dressAdvice': dress_advice
            })
        else:
            return jsonify({'success': False, 'error': '获取天气失败'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/location/search', methods=['POST'])
def search_location():
    """地点搜索"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')

        url = f"https://restapi.amap.com/v3/place/text?key={AMAP_API_KEY}&keywords={keyword}&offset=10&page=1&extensions=base"

        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('status') == '1' and data.get('pois'):
            pois = []
            for poi in data['pois']:
                location_parts = poi.get('location', '').split(',')
                lng = float(location_parts[0]) if location_parts else 0
                lat = float(location_parts[1]) if len(location_parts) > 1 else 0

                pois.append({
                    'id': poi.get('id'),
                    'name': poi.get('name'),
                    'address': poi.get('address'),
                    'type': poi.get('type'),
                    'location': {'lng': lng, 'lat': lat},
                    'cityname': poi.get('cityname'),
                    'adname': poi.get('adname')
                })

            return jsonify({'success': True, 'data': pois})
        else:
            return jsonify({'success': False, 'error': '未找到相关地点'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/weather/realtime', methods=['POST'])
def get_realtime_weather():
    """获取实时天气"""
    try:
        data = request.get_json()
        city_name = data.get('city', '')

        # 先获取城市编码
        geo_url = f"https://restapi.amap.com/v3/geocode/geo?key={AMAP_API_KEY}&address={city_name}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()

        city_code = '310000'  # 默认上海
        if geo_data.get('status') == '1' and geo_data.get('geocodes'):
            city_code = geo_data['geocodes'][0].get('adcode', '310000')

        # 获取天气
        weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={AMAP_API_KEY}&city={city_code}&extensions=base"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if weather_data.get('status') == '1' and weather_data.get('lives'):
            weather_info = weather_data['lives'][0]
            result = {
                'city': weather_info.get('city'),
                'weather': weather_info.get('weather'),
                'temperature': weather_info.get('temperature'),
                'humidity': weather_info.get('humidity'),
                'wind': f"{weather_info.get('winddirection')}风 {weather_info.get('windpower')}级",
                'reportTime': weather_info.get('reporttime')
            }
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'error': '获取天气失败'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500