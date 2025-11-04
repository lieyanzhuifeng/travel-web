from flask import Blueprint, request, jsonify
import os
from openai import OpenAI

ai_bp = Blueprint('ai', __name__
')

# 初始化OpenAI客户端 - 密钥在后端
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', 'sk-RrolPLWPWB0yemF95aF9De5663C14b0cA26d9a5c4dF08e48'),
    base_url=os.getenv('OPENAI_BASE_URL', 'https://api.v3.cm/v1')
) \
 \
         @ ai_bp.route('/analysis', methods=['POST'])


def ai_analysis():
    """AI行程分析 - 后端代理"""
    try:
        data = request.get_json()
        itinerary_data = data.get('itineraryData', [])
        weather_data = data.get('weatherData', {})

        # 构建提示词（简化版）
        days_count = len(itinerary_data)
        activities_count = sum(len(day.get('items', [])) for day in itinerary_data)

        prompt = f"""
        请分析这个{days_count}天旅行行程（共{activities_count}个活动）：
        {itinerary_data}

        天气情况：{weather_data}

        请给出行程优化建议和天气适应性分析。
        """

        # 在后端安全地调用OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )

        result = response.choices[0].message.content
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        print(f"AI分析错误: {e}")
        return jsonify({'success': False, 'error': '分析服务暂时不可用'}), 500