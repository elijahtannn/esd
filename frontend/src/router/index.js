import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/ProfileView.vue'
import EventView from '../views/EventView.vue'
import CheckOutView from '../views/CheckOutView.vue'
import AboutView from '../views/AboutView.vue'
import ContactView from '../views/ContactView.vue'
import { auth } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    },
    {
      path: '/event',
      name: 'event',
      component: EventView,
    },
    {
      path: '/checkout',
      name: 'checkout',
      component: CheckOutView,
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
    },
    {
      path: '/contact',
      name: 'contact',
      component: ContactView,
    },
  ],
})

// Add navigation guard
router.beforeEach((to, from, next) => {
  // Routes that require authentication
  const authenticatedRoutes = ['profile']
  
  if (authenticatedRoutes.includes(to.name)) {
    console.log('Accessing protected route:', to.name)
    const isAuth = auth.isAuthenticated()
    console.log('Is authenticated:', isAuth)
    
    if (!isAuth) {
      console.log('Not authenticated, redirecting to login')
      next({ name: 'login' })
    } else {
      console.log('Authenticated, proceeding to route')
      next()
    }
  } else {
    next()
  }
})

export default router
