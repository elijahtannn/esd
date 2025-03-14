<template>
    <div>
        <NavBar/>

        <!-- Banner -->
        <div class="container-fluid bannerImg banner mx-0 p-5">
            <div class="row">
                <div class="col-8">
                <div>
                    <p class="bannerText">Hello,<br> {{ user.name }}</p>
                </div>
                </div>
                <div class="col-4"></div>
            </div>
        </div>
        
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

.bannerImg {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
        url("../assets/images/background_profile.png");
    background-repeat: no-repeat;
    background-size: cover;
    height: 60vh;
    width: 100%;
}
</style>