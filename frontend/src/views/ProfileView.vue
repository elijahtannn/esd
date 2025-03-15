<template>
    <div>
        <NavBar/>
        <div v-if="user">
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
                    <h3 class="event-heading">EVENT ORDERS</h3>
                    <!-- Tab Links -->
                    <div class="tabs">
                        <button class="tablinks active" @click="openTab($event, 'Upcoming')">Upcoming</button>
                        <button class="tablinks" @click="openTab($event, 'History')">History</button>
                    </div>

                    <!-- Tab Content -->
                    <div id="Upcoming" class="tabcontent active">
                        <hr>
                        <p><strong>Lady Gaga in Singapore</strong></p>
                        <p>18 May 2025, National Stadium</p>
                        <p>Order Information: #4452</p>
                        <p>Ticket Quantity: 4</p>
                        <p>Total Cost: $300</p>
                    </div>

                    <div id="History" class="tabcontent">
                        <hr>
                        <h3>Event History</h3>
                        <p>No past events available.</p>
                    </div>
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
    },
    methods: {
        openTab(event, tabName) {
            // Remove active class from all tabs and content
            document.querySelectorAll('.tablinks, .tabcontent').forEach(element => {
                element.classList.remove('active');
            });

            // Add active class to clicked tab and corresponding content
            event.currentTarget.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        },
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
.event-heading {
    color: #2A68E1; /* Blue color */
    text-align: center;
    font-size: 24px;
    margin-bottom:20px ;
}
/* Tabs container */
.tabs {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
    position: relative;
}

/* Tab buttons */
.tablinks {
    background-color: #f1f1f1; /* Light grey for inactive tabs */
    border: none;
    outline: none;
    padding: 15px 100px;
    cursor: pointer;
    font-size: 16px;
    border-radius: 10px; /* Rounded corners */
    margin: 0 10px; /* Space between tabs */
    transition: background-color 0.3s ease, color 0.3s ease;
}

.tablinks.active {
    background-color: #2A68E1; /* Blue color for active tab */
    color: white; /* White text for active tab */
}

.tablinks:hover {
    background-color: #d9d9d9; /* Slight hover effect for inactive tabs */
}

/* Tab content */
.tabcontent {
    display: none; /* Hidden by default */
}

.tabcontent.active {
    display: block; /* Show active tab content */
}
</style>