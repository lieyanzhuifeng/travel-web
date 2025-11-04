from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from auth import auth_bp
from plans import plans_bp
from database import init_db
from flask import jsonify
from ai_service import ai_bp
from api_routes import api_bp
from route_planning import route_bp

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600

CORS(app,
     resources={
         r"/api/*": {
             "origins": ["http://localhost:*", "http://127.0.0.1:*"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }
     },
     supports_credentials=True)

# 初始化扩展
jwt = JWTManager(app)

# 🔧 添加 JWT 错误处理（在这里添加）
@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ JWT Token 无效: {error}")
    return jsonify({'error': 'Token 无效'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"❌ 缺少 JWT Token: {error}")
    return jsonify({'error': '缺少 Token'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"❌ JWT Token 已过期: {jwt_payload}")
    return jsonify({'error': 'Token 已过期'}), 401

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(plans_bp, url_prefix='/api')
# 在创建app后注册蓝图
app.register_blueprint(ai_bp, url_prefix='/api/ai')  # 添加这行
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(route_bp, url_prefix='/api/route')

# 初始化数据库
init_db()

@app.route('/')
def hello():
    return 'Travel App Backend is running!'

if __name__ == '__main__':
    app.run(debug=True, port=5000)