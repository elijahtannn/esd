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

        <!-- White boxes for profile and orders -->
        <div class="content-wrapper">
            <!-- profile box -->
            <div class="profile-box">
                <h3 class="profile-heading">PROFILE</h3>
                <p><span class="label">Id:</span> <br> #{{ user.id }}</p>
                <p><span class="label">Name:</span> <br> {{ user.name }}</p>
                <p><span class="label">Email:</span> <br> {{ user.email }}</p>
                <p><span class="label">Mobile Number:</span> <br> {{ user.mobile }}</p>
            </div>
            <!-- order box -->
            <div class="orders-box">
                <h3>Event Orders</h3>
                <p>Lady Gaga in Singapore</p>
                <p>Date: 18 May 2025, National Stadium</p>
                <p>Ticket Quantity: 4</p>
                <p>Total Cost: $300</p>
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

.content-wrapper {
    display: flex; /* Use Flexbox for alignment */
    justify-content: center; /* Centers the boxes horizontally */
    gap: 20px; /* Space between the boxes */
    position: relative; /* For overlapping */
    margin-top: -50px; /* Adjust to overlap with the banner */
}

.profile-box {
    flex: 0 0 auto; /* Prevents shrinking or growing */
    width: 20%; /* Set a fixed width for the profile box */
    background-color: white;
    padding: 20px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 2; /* Ensures it overlaps correctly */
}

.orders-box {
    flex: 0 0 auto; /* Prevents shrinking or growing */
    width: 70%; /* Set a fixed width for the orders box */
    background-color: white;
    padding: 20px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 2; /* Ensures it overlaps correctly */
}
.label {
    color: #808080; /* Grey color */
}
.profile-heading {
    color: #2A68E1; /* Blue color */
    text-align: center;
    font-size: 24px;
}
</style>