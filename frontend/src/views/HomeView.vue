<template>
  <div>
    <NavBar :key="authUpdateKey" />


    <!-- Banner -->
    <div class="container-fluid bannerImg banner mx-0 p-5">
      <div class="row">
        <div class="col-8">
          <div>
            <p class="bannerText">Your Gateway to Unforgettable Events!</p>
            <button><a href="#browseEvents" style="color:white; text-decoration: none; text-transform: uppercase;">Start
                browsing</a></button>
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
      <p class="text-center px-5">Our upcoming events include conferences, workshops, and networking sessions designed
        to bring you closer to industry leaders and innovators. From insightful talks to hands-on training, we have
        something for everyone. </p>

      <div class="container text-center py-5">
        <div class="row g-5 justify-content-center row-cols-1 row-cols-lg-3 row-cols-sm-2">
          <eventCard v-for="event in eventList"
            :key="event.Id" 
            :id="event.Id" 
            :name="event.Name" 
            :dates="event.Dates"
            :startTime="event.StartTime" 
            :endTime="event.EndTime" 
            :venue="event.Venue"
            :capacity="event.Capacity" 
            :category="event.Category" 
            :image="event.Img" 
            :description="event.Description"
            @notify-resale="handleResaleNotification" />
        </div>
      </div>

    </div>


  </div>
</template>

<script>
import { auth } from '../stores/auth'
import NavBar from "../components/nav-bar.vue";
import eventCard from "../components/event.vue";
import { ref, onMounted } from 'vue'
import axios from 'axios';

export default {
  name: 'HomeView',
  components: {
    NavBar, eventCard
  },
  data() {
    return {
      eventList: [],
      apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL
    }
  },
  methods: {
    async fetchEvents() {
      try {
        const response = await axios.get(`${this.apiGatewayUrl}/events`);
        
        var rawData = response.data.Events;
        console.log("Raw API data received:", rawData);
        
        this.processEvents(rawData);
        
      } catch (error) {
        console.error('Error fetching events:', error);
      }
    },
    processEvents(rawData) {
      const processedEvents = [];

      rawData.forEach((event) => {
        // Log the original image URL from API
        console.log(`Original event ${event.Id} image URL:`, event.Img);
        
        const existingEvent = processedEvents.find((e) => e.Id === event.Id);

        if (existingEvent) {
          if (!existingEvent.Dates.includes(event.Date)) {
            existingEvent.Dates.push(event.Date);
          }
        } else {
          processedEvents.push({
            Id: event.Id,
            Name: event.Name,
            Description: event.Description,
            Venue: event.Venue,
            Category: event.Category,
            Capacity: event.Capacity,
            CreatedAt: event.CreatedAt,
            Img: event.Img,  // Keep the original field name as it comes from API
            StartTime: event.StartTime,
            EndTime: event.EndTime,
            Dates: [event.Date],
            AvailableTickets: event.AvailableTickets || 0
          });
        }
      });

      this.eventList = processedEvents;
      
      // Log the processed events with their image URLs
      console.log("Processed events with image URLs:");
      this.eventList.forEach(event => {
        console.log(`Event ${event.Id} - ${event.Name}: Image URL = ${event.Img}`);
      });
    },
    handleResaleNotification(eventDetails) {
      // Open a modal or trigger notification signup process
      // For example:
      if (this.$refs.resaleNotificationModal) {
        this.$refs.resaleNotificationModal.open(eventDetails);
      } else {
        console.log("Received resale notification for event:", eventDetails);
      }
    }
  },
  mounted() {
    console.log("HomeView component mounted");
    this.fetchEvents();
  },
  setup() {
    const authUpdateKey = ref(0)

    onMounted(() => {
      const urlParams = new URLSearchParams(window.location.search)
      const authData = urlParams.get('auth')

      if (authData) {
        try {
          const userData = JSON.parse(atob(authData))
          auth.setUser(userData)
          window.history.replaceState({}, document.title, '/')
          authUpdateKey.value++
        } catch (error) {
          console.error('Failed to process authentication data:', error)
        }
      }
    })

    return {
      authUpdateKey
    }
  }
}
</script>

<style scoped>
.bannerImg {
  background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
    url("../assets/carousel/eventiva_carousel1.png");
  background-repeat: no-repeat;
  background-size: cover;
  height: 60vh;
  width: 100%;
}
</style>