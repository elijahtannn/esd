<template>
    <div>
        <NavBar/>
        <div class="container mt-4" v-if="user">
            <h2>Profile</h2>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{{ user.name }}</h5>
                    <p class="card-text">Email: {{ user.email }}</p>
                    <!-- Add more user details as needed -->
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import NavBar from "../components/nav-bar.vue";
import { auth } from '../stores/auth';

export default {
    name: 'profile',
    components: {
        NavBar
    },
    data() {
        return {
            user: null
        }
    },
    mounted() {
        const userData = auth.getUser();
        if (userData) {
            this.user = userData;
        }
    }
}
</script>

<style scoped>
.container {
    padding: 20px;
}

.card {
    max-width: 600px;
    margin: 0 auto;
}
</style>