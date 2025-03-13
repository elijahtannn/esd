<template>
    <nav class="navbar navbar-expand-lg bg-body-white py-2 px-3">
        <div class="container-fluid">
            <router-link class="navbar-brand" to="/"><img src="../assets/EVENTIVA.png"></router-link>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item px-2">
                        <router-link class="nav-link" :class="{ active: $route.path === '/' }" to="/">Home</router-link>
                    </li>
                    <li class="nav-item px-2">
                        <router-link class="nav-link" :class="{ active: $route.path === '/contact' }" to="/contact">Contact Us</router-link>
                    </li>
                    <li class="nav-item px-2">
                        <router-link class="nav-link" :class="{ active: $route.path === '/about' }" to="/about">About Us</router-link>
                    </li>
                    <li class="nav-item px-2" v-if="isAuthenticated">
                        <router-link class="nav-link" :class="{ active: $route.path === '/profile' }" to="/profile">Profile</router-link>
                    </li>
                    <li class="nav-item px-2" v-if="!isAuthenticated">
                        <router-link class="nav-link" :class="{ active: $route.path === '/login' }" to="/login">Login</router-link>
                    </li>
                    <li class="nav-item px-2" v-if="isAuthenticated">
                        <a class="nav-link" href="#" @click.prevent="logout">Logout</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
</template>

<script>
import { auth } from '../stores/auth'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
    setup() {
        const router = useRouter()
        const isAuthenticated = ref(auth.isAuthenticated())
        
        onMounted(() => {
            // Initialize authentication state
            isAuthenticated.value = auth.isAuthenticated()
        })

        const logout = () => {
            auth.clearUser()
            isAuthenticated.value = false
            router.push('/')
        }

        return {
            isAuthenticated,
            logout
        }
    }
}
</script>