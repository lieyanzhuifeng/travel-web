#!/usr/bin/env python3
"""
后端调试脚本 - 全面诊断 422 错误问题
"""

import sqlite3
import sys
import os
from datetime import datetime


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"🔍 {title}")
    print(f"{'=' * 60}")


def check_database():
    """检查数据库状态"""
    print_header("数据库检查")

    # 检查数据库文件
    if not os.path.exists('users.db'):
        print("❌ users.db 文件不存在")
        return False

    file_size = os.path.getsize('users.db')
    print(f"✅ users.db 存在，大小: {file_size} 字节")

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        # 检查所有表
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"📊 数据库中的表: {[table[0] for table in tables]}")

        # 检查用户表
        if 'users' in [table[0] for table in tables]:
            c.execute("SELECT * FROM users")
            users = c.fetchall()
            print(f"👤 用户数据 ({len(users)} 个用户):")
            for user in users:
                print(f"   ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[3]}")
        else:
            print("❌ users 表不存在")

        # 检查行程表
        if 'travel_plans' in [table[0] for table in tables]:
            c.execute("SELECT * FROM travel_plans")
            plans = c.fetchall()
            print(f"🗺️ 行程数据 ({len(plans)} 个行程):")
            for plan in plans:
                print(f"   ID: {plan[0]}, 用户ID: {plan[1]}, 标题: {plan[2]}")
        else:
            print("❌ travel_plans 表不存在")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return False


def check_imports():
    """检查所有必要的导入"""
    print_header("模块导入检查")

    requirements = {
        'flask': 'Flask',
        'flask_cors': 'CORS',
        'flask_jwt_extended': 'JWTManager',
        'werkzeug.security': ['generate_password_hash', 'check_password_hash'],
        'docx': 'Document'
    }

    all_ok = True
    for package, imports in requirements.items():
        try:
            if package == 'flask':
                from flask import Flask
            elif package == 'flask_cors':
                from flask_cors import CORS
            elif package == 'flask_jwt_extended':
                from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
            elif package == 'werkzeug.security':
                from werkzeug.security import generate_password_hash, check_password_hash
            elif package == 'docx':
                from docx import Document

            print(f"✅ {package} 导入成功")
        except ImportError as e:
            print(f"❌ {package} 导入失败: {e}")
            all_ok = False

    return all_ok


def test_jwt_token():
    """测试 JWT token 解析"""
    print_header("JWT Token 测试")

    # 这是一个示例 token，你需要替换成前端实际的 token
    sample_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MTM2NDY0NSwianRpIjoiNDg2MmNlNzQtMzk3MS00MmRhLWFjYjEtNzQ1ODY4YTc0NjEzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MiwibmJmIjoxNzYxMzY0NjQ1LCJleHAiOjE3NjEzNjgyNDV9.oxV_zBAoJhFJPbZ9yjYvOGx4dBVWgqHk1YLRqeAHXrk"
    try:
        import jwt
        secret_key = 'your-secret-key-change-this'

        # 解码 token（不验证，只是查看内容）
        decoded = jwt.decode(sample_token, options={"verify_signature": False})
        print("✅ Token 解码成功:")
        print(f"   用户ID (sub): {decoded.get('sub')}")
        print(f"   签发时间 (iat): {datetime.fromtimestamp(decoded.get('iat'))}")
        print(f"   过期时间 (exp): {datetime.fromtimestamp(decoded.get('exp'))}")
        print(f"   是否过期: {'是' if decoded.get('exp') < datetime.now().timestamp() else '否'}")

    except Exception as e:
        print(f"❌ Token 解析失败: {e}")


def check_flask_app():
    """测试 Flask 应用启动"""
    print_header("Flask 应用测试")

    try:
        from flask import Flask
        from flask_cors import CORS
        from flask_jwt_extended import JWTManager

        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600

        CORS(app)
        JWTManager(app)

        print("✅ Flask 应用配置成功")
        print("✅ CORS 配置成功")
        print("✅ JWT 配置成功")

        return True

    except Exception as e:
        print(f"❌ Flask 应用配置失败: {e}")
        return False


def simulate_api_request():
    """模拟 API 请求测试"""
    print_header("模拟 API 请求")

    try:
        import requests

        # 测试基础连接
        response = requests.get('http://localhost:5000/', timeout=5)
        print(f"✅ 基础连接测试: 状态码 {response.status_code}")
        print(f"   响应: {response.text}")

        # 测试登录
        login_data = {
            'username': 'test',
            'password': 'test123'
        }
        response = requests.post('http://localhost:5000/api/auth/login',
                                 json=login_data, timeout=5)
        print(f"✅ 登录测试: 状态码 {response.status_code}")
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"   获取到 Token: {token[:50]}...")

            # 测试获取行程
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get('http://localhost:5000/api/plans',
                                    headers=headers, timeout=5)
            print(f"✅ 获取行程测试: 状态码 {response.status_code}")
            if response.status_code != 200:
                print(f"   错误响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端正在运行")
    except Exception as e:
        print(f"❌ API 请求测试失败: {e}")


def main():
    print("🚀 开始后端调试诊断...")
    print(f"📁 当前目录: {os.getcwd()}")
    print(f"🐍 Python 版本: {sys.version}")

    # 执行各项检查
    db_ok = check_database()
    imports_ok = check_imports()
    flask_ok = check_flask_app()

    # 只有数据库正常才检查 token
    if db_ok:
        test_jwt_token()

    # 只有导入正常才测试 API
    if imports_ok:
        simulate_api_request()

    print_header("诊断总结")
    if all([db_ok, imports_ok, flask_ok]):
        print("🎉 所有基础检查通过！问题可能在于：")
        print("   1. Token 过期或无效")
        print("   2. 数据库中的用户数据问题")
        print("   3. 行程数据格式问题")
        print("\n💡 建议：查看后端启动时的详细日志")
    else:
        print("❌ 发现基础配置问题，请先修复上述错误")

    print("\n🔧 下一步：请运行 'python app.py' 并查看完整输出")


if __name__ == '__main__':
    main()