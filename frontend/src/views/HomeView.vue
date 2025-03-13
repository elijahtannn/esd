<template>
  <NavBar />


  <!-- Banner -->
  <div class="container-fluid carousel banner mx-0 p-5">
    <div class="row">
      <div class="col-8">
        <div>
          <p class="bannerText">Your Gateway to Unforgettable Events!</p>
          <button><a href="#browseEvents" style="color:white; text-decoration: none; text-transform: uppercase;">Start browsing</a></button>
        </div>
      </div>
      <div class="col-4"></div>
    </div>
  </div>


  <!-- Stats to showcase -->
  <div class="container text-center p-5">
    <div class="row">
      <div class="col">
        <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">82</h1>
        <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Events Completed</p>
      </div>
      <div class="col">
        <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">5,898</h1>
        <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Tickets Sold</p>
      </div>
      <div class="col">
        <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">209</h1>
        <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Artists Involved</p>
      </div>
    </div>
  </div>


  <!-- List of upcoming events -->
  <div class="container" id="browseEvents">
    <h2 style="text-transform: uppercase;" class="text-center">upcoming Events</h2>
    <p class="text-center px-5">Our upcoming events include conferences, workshops, and networking sessions designed to bring you closer to industry leaders and innovators. From insightful talks to hands-on training, we have something for everyone. </p>
    
    <div class="container text-center py-5">
      <div class="row g-5 justify-content-center row-cols-1 row-cols-lg-3 row-cols-sm-2">
        <eventCard v-for="event in eventList" 
          :id="event.id" 
          :name="event.name"
          :startDate="event.startDate"
          :endDate="event.endDate"
          :startTime="event.startTime"
          :endTime="event.endTime"
          :venue="event.venue"
          :capacity="event.capacity"
          :eventType="event.eventType"
          :availableTickets="event.availableTickets"
          :image="event.image"
          :description="event.description"/>
      </div>
    </div>

  </div>


</template>

<script>

import NavBar from "../components/nav-bar.vue";
import eventCard from "../components/event.vue";

export default {
  name: 'home',
  components: {
    NavBar, eventCard
  },
  data() {
    return {
      eventList: [
        {
          id: 1,
          name: "Tech Conference 2025",
          startDate: "12 May 2025",
          endDate: "15 May 2025",
          startTime: "7pm",
          endTime: "9pm",
          venue: "National Stadium",
          description: "A conference showcasing the latest in technology and innovation.",
          capacity: 899,
          eventType: "Concert",
          availableTickets: 200,
          image: "../assets/carousel/eventiva_carousel1.png",
        },
        {
          id: 2,
          name: "Art Expo",
          startDate: "15 Apr 2025",
          endDate: "15 Apr 2025",
          startTime: "7pm",
          endTime: "9pm",
          venue: "National Stadium",
          description: "An exhibition of modern and contemporary art from around the world.",
          capacity: 899,
          eventType: "Expo",
          availableTickets: 754,
          image: "../assets/carousel/eventiva_carousel1.png",
        },
        {
          id: 3,
          name: "Music Festival",
          startDate: "17 Jun 2025",
          endDate: "17 Jun 2025",
          startTime: "7pm",
          endTime: "9pm",
          venue: "National Stadium",
          description: "A weekend of live music performances from top artists.",
          capacity: 899,
          eventType: "Festival",
          availableTickets: 294,
          image: "../assets/carousel/eventiva_carousel1.png",
        },
        {
          id: 4,
          name: "Startup Pitch Night",
          startDate: "8 Aug 2025",
          endDate: "10 Aug 2025",
          startTime: "7pm",
          endTime: "9pm",
          venue: "National Stadium",
          description: "An evening where startups pitch their ideas to investors.",
          capacity: 899,
          eventType: "Formal",
          availableTickets: 27,
          image: "../assets/carousel/eventiva_carousel1.png",
        },
        {
          id: 5,
          name: "Health and Wellness Fair",
          startDate: "12 Dec 2025",
          endDate: "12 Dec 2025",
          startTime: "7pm",
          endTime: "9pm",
          venue: "National Stadium",
          description: "A fair promoting health and wellness with workshops and activities.",
          capacity: 899,
          eventType: "Expo",
          availableTickets: 11,
          image: "../assets/carousel/eventiva_carousel1.png",
        }
      ],
    }
  },
  methods: {

  },
  mounted() {

  }
}
</script>

<style scoped>
.carousel {
  background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
    url("../assets/carousel/eventiva_carousel1.png");
  background-repeat: no-repeat;
  background-size: cover;
  height: 60vh;
  width: 100%;
}

</style>