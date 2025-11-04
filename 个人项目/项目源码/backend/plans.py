from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import sqlite3
import os
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

plans_bp = Blueprint('plans', __name__)

# 数据库文件路径
DB_PATH = 'users.db'


def init_plans_db():
    """初始化行程计划数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创建行程计划表
    c.execute('''CREATE TABLE IF NOT EXISTS travel_plans
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        user_id
        INTEGER
        NOT
        NULL,
        title
        TEXT
        NOT
        NULL,
        description
        TEXT,
        itinerary
        TEXT
        NOT
        NULL,
        days_count
        INTEGER
        NOT
        NULL,
        activities_count
        INTEGER
        NOT
        NULL,
        created_at
        TIMESTAMP
        DEFAULT
        CURRENT_TIMESTAMP,
        updated_at
        TIMESTAMP
        DEFAULT
        CURRENT_TIMESTAMP,
        FOREIGN
        KEY
                 (
        user_id
                 ) REFERENCES users
                 (
                     id
                 ))''')

    conn.commit()
    conn.close()


# 初始化数据库
init_plans_db()


@plans_bp.route('/plans', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_plans():
    """获取用户的所有行程计划"""
    print(f"🎯 ========== 进入 get_plans 函数 ==========")
    print(f"📧 请求方法: {request.method}")
    print(f"📋 完整请求头: {dict(request.headers)}")

    if request.method == 'OPTIONS':
        print("🔄 处理 OPTIONS 预检请求")
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()
        print(f"🔍 JWT 解析出的用户ID: {user_id} (类型: {type(user_id)})")

        # 详细检查用户是否存在
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        print(f"🔧 使用的数据库路径: {DB_PATH}")
        print(f"✅ 数据库文件存在: {os.path.exists(DB_PATH)}")

        # 检查用户表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table_exists = c.fetchone()
        print(f"📊 users 表存在: {bool(users_table_exists)}")

        # 检查 travel_plans 表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='travel_plans'")
        plans_table_exists = c.fetchone()
        print(f"📊 travel_plans 表存在: {bool(plans_table_exists)}")

        # 详细检查用户
        c.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        print(f"👤 数据库查询的用户: {user}")

        if not user:
            print("❌ 用户不存在于数据库中")
            conn.close()
            return jsonify({'error': '用户不存在'}), 404

        print(f"✅ 用户验证通过: {user[1]} (ID: {user[0]})")

        # 检查行程数据
        c.execute('''
                  SELECT id, title, description, itinerary, days_count, activities_count, created_at
                  FROM travel_plans
                  WHERE user_id = ?
                  ORDER BY created_at DESC
                  ''', (user_id,))

        plans_data = c.fetchall()
        print(f"📋 数据库查询结果: {len(plans_data)} 条记录")
        for i, plan in enumerate(plans_data):
            print(f"  行程{i + 1}: ID={plan[0]}, 标题='{plan[1]}'")

        # 原来的处理逻辑继续...
        plans = []
        for row in plans_data:
            # 安全地解析 itinerary
            itinerary_data = []
            if row[3]:
                try:
                    import json
                    itinerary_data = json.loads(row[3])
                    print(f"✅ 行程 {row[0]} JSON 解析成功")
                except json.JSONDecodeError as e:
                    print(f"⚠️ 行程 {row[0]} JSON 解析失败: {e}")
                    try:
                        itinerary_data = eval(row[3])
                        print(f"✅ 行程 {row[0]} eval 解析成功")
                    except Exception as e2:
                        print(f"❌ 行程 {row[0]} 所有解析方法都失败: {e2}")
                        itinerary_data = []

            plan = {
                'id': row[0],
                'title': row[1],
                'description': row[2] or '',
                'itinerary': itinerary_data,
                'days_count': row[4],
                'activities_count': row[5],
                'created_at': row[6],
                'is_current': False
            }
            plans.append(plan)

        conn.close()

        print(f"✅ 成功返回 {len(plans)} 个行程计划")
        return jsonify({'plans': plans}), 200

    except Exception as e:
        print(f"❌ 获取行程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@plans_bp.route('/plans/save', methods=['POST', 'OPTIONS'])
@jwt_required()
def save_plan():
    """保存行程计划"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        print(f"💾 用户 {user_id} 保存行程")
        print(f"📝 接收到的数据: {data}")

        # 检查必要字段
        required_fields = ['title', 'itinerary', 'days_count', 'activities_count']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            print(f"❌ 缺少必要字段: {missing_fields}")
            return jsonify({'error': f'缺少必要字段: {", ".join(missing_fields)}'}), 400

        # 验证数据类型
        if not isinstance(data['itinerary'], list):
            return jsonify({'error': 'itinerary 必须是数组'}), 400

        if not isinstance(data['days_count'], int) or data['days_count'] < 0:
            return jsonify({'error': 'days_count 必须是正整数'}), 400

        if not isinstance(data['activities_count'], int) or data['activities_count'] < 0:
            return jsonify({'error': 'activities_count 必须是正整数'}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 使用 json.dumps 安全地序列化 itinerary
        import json
        itinerary_json = json.dumps(data['itinerary'], ensure_ascii=False)

        c.execute('''
                  INSERT INTO travel_plans
                      (user_id, title, description, itinerary, days_count, activities_count)
                  VALUES (?, ?, ?, ?, ?, ?)
                  ''', (
                      user_id,
                      data['title'].strip(),
                      data.get('description', '').strip(),
                      itinerary_json,  # 使用 JSON 序列化
                      data['days_count'],
                      data['activities_count']
                  ))

        plan_id = c.lastrowid
        conn.commit()
        conn.close()

        print(f"✅ 行程保存成功，ID: {plan_id}")
        return jsonify({
            'message': '行程保存成功',
            'plan_id': plan_id
        }), 201

    except Exception as e:
        print(f"❌ 保存行程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '保存行程失败: ' + str(e)}), 500


@plans_bp.route('/plans/<int:plan_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_plan(plan_id):
    """删除行程计划"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 检查行程是否存在且属于当前用户
        c.execute('SELECT id FROM travel_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': '行程不存在或无权访问'}), 404

        c.execute('DELETE FROM travel_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))

        conn.commit()
        conn.close()

        return jsonify({'message': '删除成功'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@plans_bp.route('/plans/<int:plan_id>/download', methods=['GET', 'OPTIONS'])
@jwt_required()
def download_plan(plan_id):
    """下载行程计划为Word文档"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 获取行程数据
        c.execute('''
                  SELECT title, description, itinerary, days_count, activities_count, created_at
                  FROM travel_plans
                  WHERE id = ?
                    AND user_id = ?
                  ''', (plan_id, user_id))

        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': '行程不存在或无权访问'}), 404

        title, description, itinerary_str, days_count, activities_count, created_at = row


        # 修复：使用安全的 JSON 解析替代 eval
        itinerary = []
        if itinerary_str:
            try:
                import json
                # 方法1：直接使用 json.loads
                itinerary = json.loads(itinerary_str)
            except json.JSONDecodeError:
                try:
                    # 方法2：如果 JSON 解析失败，尝试替换布尔值
                    fixed_str = itinerary_str.replace(': false', ': false').replace(': true', ': true')
                    itinerary = json.loads(fixed_str)
                except:
                    # 方法3：如果还是失败，使用安全的 literal_eval
                    import ast
                    try:
                        itinerary = ast.literal_eval(itinerary_str)
                    except:
                        itinerary = []


        conn.close()

        # 创建Word文档
        doc = Document()

        # 标题
        title_para = doc.add_heading(title, 0)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 基本信息
        doc.add_paragraph(f'创建时间: {created_at}')
        doc.add_paragraph(f'行程天数: {days_count}天')
        doc.add_paragraph(f'活动数量: {activities_count}个')

        if description:
            doc.add_paragraph(f'行程描述: {description}')

        doc.add_paragraph()  # 空行

        # 添加每一天的行程
        for day in itinerary:
            # 天标题
            day_title = f"第{day['day']}天"
            if day.get('date'):
                try:
                    day_date = datetime.strptime(day['date'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y年%m月%d日')
                    day_title += f" - {day_date}"
                except:
                    day_title += f" - {day['date']}"

            doc.add_heading(day_title, level=1)

            # 添加活动
            if day.get('items'):
                for item in day['items']:
                    # 活动时间
                    time_text = ''
                    if item.get('startTime') and item.get('endTime'):
                        time_text = f"{item['startTime']}-{item['endTime']}"
                    elif item.get('time'):
                        time_text = item['time']

                    if time_text:
                        time_para = doc.add_paragraph()
                        time_para.add_run('🕒 ' + time_text).bold = True

                    # 活动名称和类型
                    activity_para = doc.add_paragraph()

                    # 添加图标
                    icons = {
                        'attraction': '🗺️',
                        'restaurant': '🍽️',
                        'hotel': '🏨',
                        'route': '🛣️',
                        'route-planning': '🚗'
                    }
                    icon = icons.get(item.get('type', ''), '📍')

                    activity_para.add_run(f"{icon} {item['name']}").bold = True

                    # 添加类型标签
                    type_map = {
                        'attraction': '景点',
                        'restaurant': '餐厅',
                        'hotel': '酒店',
                        'route': '路程',
                        'route-planning': '行程规划'
                    }
                    type_text = type_map.get(item.get('type', ''), '活动')
                    activity_para.add_run(f" ({type_text})")

                    # 地址信息
                    if item.get('details') or item.get('address'):
                        address = item.get('details') or item.get('address', '')
                        doc.add_paragraph(f"📍 地址: {address}")

                    # 路径规划信息
                    if item.get('type') == 'route-planning':
                        route_para = doc.add_paragraph()
                        route_para.add_run(
                            f"🚗 从 {item.get('startPoint', '')} 到 {item.get('endPoint', '')}").bold = True

                        route_info = []
                        if item.get('duration'):
                            route_info.append(f"⏱️ {item['duration']}")
                        if item.get('distance'):
                            route_info.append(f"📏 {item['distance']}")
                        if item.get('cost') and item.get('cost') != '0':
                            route_info.append(f"💰 ¥{item['cost']}")

                        if route_info:
                            doc.add_paragraph(' | '.join(route_info))

                        # 路线步骤
                        if item.get('steps'):
                            doc.add_paragraph('详细路线:')
                            for step in item['steps']:
                                step_icons = {
                                    'walking': '🚶',
                                    'bus': '🚌',
                                    'driving': '🚗',
                                    'subway': '🚇'
                                }
                                step_icon = step_icons.get(step.get('type', ''), '📍')
                                doc.add_paragraph(f"  {step_icon} {step.get('instruction', '')}")

                    # 备注信息
                    if item.get('note'):
                        note_para = doc.add_paragraph()
                        note_para.add_run('📝 备注: ').bold = True
                        note_para.add_run(item['note'])

                    doc.add_paragraph()  # 空行

            doc.add_paragraph()  # 天之间的空行

        # 保存到内存
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=f"{title}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        print(f"下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@plans_bp.route('/plans/<int:plan_id>/load', methods=['GET', 'OPTIONS'])
@jwt_required()
def load_plan(plan_id):
    """加载行程详情用于继续编辑"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()
        print(f"🔍 用户 {user_id} 请求加载行程 {plan_id}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 获取行程数据
        c.execute('''
                  SELECT id,
                         title,
                         description,
                         itinerary,
                         days_count,
                         activities_count,
                         created_at,
                         updated_at
                  FROM travel_plans
                  WHERE id = ?
                    AND user_id = ?
                  ''', (plan_id, user_id))

        row = c.fetchone()
        if not row:
            conn.close()
            print(f"❌ 行程 {plan_id} 不存在或无权访问")
            return jsonify({'error': '行程不存在或无权访问'}), 404

        # 解析行程数据
        plan_id, title, description, itinerary_str, days_count, activities_count, created_at, updated_at = row

        # 安全地解析 itinerary
        itinerary_data = []
        if itinerary_str:
            try:
                import json
                itinerary_data = json.loads(itinerary_str)
            except json.JSONDecodeError:
                try:
                    # 尝试修复常见的 JSON 格式问题
                    fixed_str = itinerary_str.replace("'", '"').replace(': False', ': false').replace(': True',
                                                                                                      ': true')
                    itinerary_data = json.loads(fixed_str)
                except:
                    try:
                        # 最后尝试使用 ast.literal_eval
                        import ast
                        itinerary_data = ast.literal_eval(itinerary_str)
                    except:
                        itinerary_data = []
                        print(f"⚠️ 行程 {plan_id} 的 itinerary 数据解析失败")

        conn.close()

        # 构建完整的行程数据响应
        plan_data = {
            'id': plan_id,
            'title': title,
            'description': description or '',
            'itinerary': itinerary_data,
            'days_count': days_count,
            'activities_count': activities_count,
            'created_at': created_at,
            'updated_at': updated_at
        }

        print(f"✅ 成功加载行程 {plan_id}: {title}")
        print(f"📊 行程包含 {days_count} 天, {activities_count} 个活动")

        return jsonify({
            'message': '行程加载成功',
            'plan': plan_data
        }), 200

    except Exception as e:
        print(f"❌ 加载行程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '加载行程失败: ' + str(e)}), 500


@plans_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_plan(plan_id):
    """更新行程计划"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        print(f"🔄 用户 {user_id} 更新计划 {plan_id}")
        print(f"📝 更新数据: {data}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 检查计划是否存在且属于当前用户
        c.execute('SELECT id FROM travel_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': '行程不存在或无权访问'}), 404

        # 更新计划
        import json
        itinerary_json = json.dumps(data['itinerary'], ensure_ascii=False)

        c.execute('''
                  UPDATE travel_plans
                  SET title            = ?,
                      description      = ?,
                      itinerary        = ?,
                      days_count       = ?,
                      activities_count = ?,
                      updated_at       = CURRENT_TIMESTAMP
                  WHERE id = ?
                    AND user_id = ?
                  ''', (
                      data['title'].strip(),
                      data.get('description', '').strip(),
                      itinerary_json,
                      data['days_count'],
                      data['activities_count'],
                      plan_id,
                      user_id
                  ))

        conn.commit()
        conn.close()

        return jsonify({'message': '更新成功'}), 200

    except Exception as e:
        print(f"❌ 更新计划失败: {str(e)}")
        return jsonify({'error': '更新失败: ' + str(e)}), 500