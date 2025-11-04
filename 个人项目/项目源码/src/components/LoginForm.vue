<template>
  <div class="login-form">
    <div class="form-container">
      <!-- 关闭按钮 -->
      <button class="close-btn" @click="handleClose">×</button>

      <h2>{{ isLogin ? '登录' : '注册' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名:</label>
          <input v-model="form.username" type="text" required>
        </div>
        <div class="form-group">
          <label>密码:</label>
          <input v-model="form.password" type="password" required>
        </div>
        <div v-if="!isLogin" class="form-group">
          <label>邮箱:</label>
          <input v-model="form.email" type="email">
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>
      <p @click="toggleMode" class="toggle-mode">
        {{ isLogin ? '没有账号？点击注册' : '已有账号？点击登录' }}
      </p>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="message" class="success">{{ message }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginForm',
  emits: ['login-success', 'close'],
  data() {
    return {
      isLogin: true,
      loading: false,
      error: '',
      message: '',
      form: {
        username: '',
        password: '',
        email: ''
      }
    }
  },
  methods: {
    handleClose() {
      this.$emit('close')
    },
    toggleMode() {
      this.isLogin = !this.isLogin
      this.error = ''
      this.message = ''
    },
    async handleSubmit() {
      this.loading = true
      this.error = ''
      this.message = ''

      try {
        const url = this.isLogin ? '/api/auth/login' : '/api/auth/register'
        const response = await fetch(`http://localhost:5000${url}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.form)
        })

        const data = await response.json()

        if (response.ok) {
          if (this.isLogin) {
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('user', JSON.stringify(data.user))
            this.message = '登录成功！'
            this.$emit('login-success', data.user)
          } else {
            this.message = '注册成功！请登录'
            this.isLogin = true
            this.form.password = ''
          }
        } else {
          this.error = data.error || '操作失败'
        }
      } catch (err) {
        this.error = '网络错误，请检查后端服务是否启动'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-form {
  position: relative;
}

.form-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  min-width: 350px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f5f5f5;
}

/* 其余样式保持不变 */
.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

button[type="submit"] {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
}

button[type="submit"]:hover:not(:disabled) {
  background: #5a6fd8;
}

button[type="submit"]:disabled {
  background: #a0a0a0;
  cursor: not-allowed;
}

.toggle-mode {
  margin-top: 1rem;
  text-align: center;
  color: #667eea;
  cursor: pointer;
  font-weight: 500;
}

.error {
  color: #e74c3c;
  margin-top: 1rem;
  text-align: center;
  padding: 0.5rem;
  background: #ffeaea;
  border-radius: 4px;
}

.success {
  color: #27ae60;
  margin-top: 1rem;
  text-align: center;
  padding: 0.5rem;
  background: #eaffea;
  border-radius: 4px;
}
</style>
