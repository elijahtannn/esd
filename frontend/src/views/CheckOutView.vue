<template>
    <NavBar/>

    <!-- Banner -->
    <div class="container-fluid carousel banner mx-0 p-5">
        <div class="row">
            <div class="col-10">
                <div>
                    <p class="bannerText p-5">{{ eventName }}</p>
                    <p class="ms-5" style="background-color: var(--main-blue); padding: 10px 20px; color:white; text-transform: uppercase; font-weight: 600; width: fit-content; margin-top: -30px;">
                        {{ startDate }} - {{ endDate }}, {{ startTime }} - {{ endTime }}
                    </p>
                    <p class="ms-5" style="color: white;">{{ venue }}</p>
                </div>
            </div>
            <div class="col-4"></div>
        </div>
    </div>

    <div class="container-fluid p-5">
        <div class="row px-5">
            <p @click="goBack" style="cursor: pointer;"><i class="bi bi-arrow-left-short"></i> Back to {{ previousStep }}</p>
        </div>
        <div class="row p-5">
            <div class="col">

            </div>
        </div>
    </div>

    
</template>

<script>

import NavBar from "../components/nav-bar.vue";

export default {
    name: 'checkout',
    components: {
        NavBar
    },
    data() {
        return {
            eventId: 0,
            eventName: "Lady Gaga in Singapore",
            startDate: "12 May 2025",
            endDate: "15 May 2025",
            startTime: "7pm",
            endTime: "9pm",
            venue: "National Stadium",
            eventImage: "../assets/carousel/eventiva_carousel1.png",

            previousStep: "browsing event",
        }
    },
    methods: {
        goBack(){
            this.$router.back() 
        }
    },
    mounted() {
        this.eventId = this.$route.query.eventId;
    }
}
</script>

<style scoped>
.carousel {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
        url("../assets/carousel/eventiva_carousel1.png");
    background-repeat: no-repeat;
    background-size: cover;
    height: 50vh;
    width: 100%;
}
</style>