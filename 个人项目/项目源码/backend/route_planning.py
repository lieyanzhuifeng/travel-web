from flask import Blueprint, request, jsonify
import requests
import os

route_bp = Blueprint('route', __name__)

# 高德地图API密钥 - 现在安全地放在后端
AMAP_API_KEY = "766b9fb43d163e907f36f41ac6e7c20a"


@route_bp.route('/transit', methods=['POST'])
def transit_route():
    """公交路径规划"""
    return handle_route_planning('transit')


@route_bp.route('/driving', methods=['POST'])
def driving_route():
    """驾车路径规划"""
    return handle_route_planning('driving')


@route_bp.route('/walking', methods=['POST'])
def walking_route():
    """步行路径规划"""
    return handle_route_planning('walking')


def handle_route_planning(transport_mode):
    """处理路径规划请求的通用函数"""
    try:
        data = request.get_json()
        origin = data.get('origin', '')
        destination = data.get('destination', '')

        if not origin or not destination:
            return jsonify({'success': False, 'error': '起点和终点不能为空'})

        # 构建高德地图API URL
        if transport_mode == 'transit':
            url = f"https://restapi.amap.com/v3/direction/transit/integrated?origin={origin}&destination={destination}&city=北京&key={AMAP_API_KEY}"
        elif transport_mode == 'driving':
            url = f"https://restapi.amap.com/v3/direction/driving?origin={origin}&destination={destination}&key={AMAP_API_KEY}"
        elif transport_mode == 'walking':
            url = f"https://restapi.amap.com/v3/direction/walking?origin={origin}&destination={destination}&key={AMAP_API_KEY}"
        else:
            return jsonify({'success': False, 'error': '不支持的交通方式'})

        # 调用高德地图API
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('status') == '1':
            formatted_result = format_route_result(data, transport_mode)
            return jsonify({'success': True, 'data': formatted_result})
        else:
            return jsonify({'success': False, 'error': data.get('info', '路径规划失败')})

    except Exception as e:
        print(f"路径规划错误 ({transport_mode}): {e}")
        return jsonify({'success': False, 'error': str(e)})


def format_route_result(data, transport_mode):
    """格式化路线结果"""
    if transport_mode == 'transit':
        transits = data.get('route', {}).get('transits', [])
        return {
            'plans': [
                {
                    'id': index,
                    'cost': plan.get('cost', '0'),
                    'duration': Math.floor((plan.get('duration', 0) / 60)),
                    'walkingDistance': plan.get('walking_distance', 0),
                    'distance': plan.get('distance', 0),
                    'steps': format_transit_steps(plan.get('segments', []))
                }
                for index, plan in enumerate(transits)
            ]
        }
    elif transport_mode in ['driving', 'walking']:
        paths = data.get('route', {}).get('paths', [])
        return {
            'plans': [
                {
                    'id': index,
                    'cost': '0',
                    'duration': Math.floor((path.get('duration', 0) / 60)),
                    'walkingDistance': 0,
                    'distance': path.get('distance', 0),
                    'steps': format_driving_walking_steps(path.get('steps', []), transport_mode)
                }
                for index, path in enumerate(paths)
            ]
        }
    return {'plans': []}


def format_transit_steps(segments):
    """格式化公交步骤"""
    steps = []
    for segment in segments:
        walking = segment.get('walking', {})
        if walking and walking.get('distance'):
            steps.append({
                'type': 'walking',
                'instruction': f"🚶 步行 {walking.get('distance')} 米"
            })

        bus = segment.get('bus', {})
        if bus and bus.get('buslines'):
            for line in bus['buslines']:
                name = line.get('name', '')
                dep = line.get('departure_stop', {}).get('name', '')
                arr = line.get('arrival_stop', {}).get('name', '')
                steps.append({
                    'type': 'bus',
                    'instruction': f"🚌 乘坐 {name}：{dep} → {arr}"
                })
    return steps


def format_driving_walking_steps(steps, transport_mode):
    """格式化驾车/步行步骤"""
    icon = '🚗' if transport_mode == 'driving' else '🚶'
    return [
        {
            'type': transport_mode,
            'instruction': f"{icon} {step.get('instruction', '')} ({step.get('distance', 0)}米)"
        }
        for step in steps
    ]