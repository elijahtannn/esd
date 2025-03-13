// Create auth store to manage authentication state
const AUTH_KEY = 'auth_user'

export const auth = {
    getUser() {
        const userStr = localStorage.getItem(AUTH_KEY)
        console.log('Current user data:', userStr) // Debug log
        return userStr ? JSON.parse(userStr) : null
    },

    setUser(user) {
        console.log('Setting user:', user) // Debug log
        localStorage.setItem(AUTH_KEY, JSON.stringify(user))
    },

    clearUser() {
        console.log('Clearing user') // Debug log
        localStorage.removeItem(AUTH_KEY)
    },

    isAuthenticated() {
        const isAuth = this.getUser() !== null
        console.log('Authentication check:', isAuth) // Debug log
        return isAuth
    }
} 