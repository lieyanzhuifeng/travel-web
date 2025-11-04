import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     username
                     TEXT
                     UNIQUE
                     NOT
                     NULL,
                     password
                     TEXT
                     NOT
                     NULL,
                     email
                     TEXT
                 )''')

    # 插入测试用户
    try:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  ('test', generate_password_hash('test123'), 'test@example.com'))
    except sqlite3.IntegrityError:
        pass  # 用户已存在

    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2],
            'email': user[3]
        }
    return None


def create_user(username, password, email=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  (username, generate_password_hash(password), email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False