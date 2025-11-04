from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import get_user_by_username, create_user
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password:
        return jsonify({'error': '用户名和密码是必需的'}), 400

    if get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 400

    if create_user(username, password, email):
        return jsonify({'message': '注册成功'}), 201
    else:
        return jsonify({'error': '注册失败'}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '用户名和密码是必需的'}), 400

    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=str(user['id']))
        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    else:
        return jsonify({'error': '用户名或密码错误'}), 401


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    # 这里可以添加获取用户详细信息的逻辑
    return jsonify({'user_id': user_id}), 200