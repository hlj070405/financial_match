import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/')
      return
    }
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        next('/')
        return
      }
    } catch (error) {
      console.error('Token验证失败:', error)
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      next('/')
      return
    }
  }
  
  if (to.path === '/' && token) {
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        next('/dashboard')
        return
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
      }
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  }
  
  next()
})

export default router
