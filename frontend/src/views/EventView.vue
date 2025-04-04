<template>
    <NavBar />

    <!-- Banner -->
    <div class="container-fluid bannerImg banner mx-0 p-5">
        <div class="row">
            <div class="col-12">
                <div>
                    <p class="bannerText p-5">{{ eventDetails.Name }}</p>
                </div>
            </div>
        </div>
    </div>


    <!-- Event details -->
    <div class="container-fluid p-5">
        <div class="row px-5">
            <div class="col">
                <p><i class="bi bi-calendar-week-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                    formattedDate }}</p>
                <p><i class="bi bi-alarm-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{ formattedTime
                    }}</p>
                <p><i class="bi bi-geo-alt-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                    eventDetails.Venue }}
                </p>
            </div>
            <div class="col">
                <p>Price</p>
                <h2 style="color:var(--main-blue); margin-top: -10px;">${{ minPrice }} - ${{ maxPrice }}</h2>
            </div>
            <div class="col text-center">
                <div v-if="doneLoading">
                    <button style="text-transform: uppercase;" @click="toCheckout">Buy tickets</button>
                    <p style="color:var(--text-grey)">max capacity: {{ eventDetails.Capacity }}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Event description -->
    <div class="container-fluid p-5" style="background-color: var(--light-blue);">
        <div class="row p-5">
            <div class="col-6">
                <h3 style="text-transform: uppercase; color:var(--main-blue)">Event details</h3>
                <p style="line-height: 30px; margin-right: 100px;">{{ eventDetails.Description }}</p>
            </div>
            <div class="col-6">
                <img :src="eventDetails.Image || '../assets/carousel/eventiva_carousel1.png'" style="width: 100%; object-fit: cover;">
            </div>
        </div>
    </div>


    <!-- Ticket pricing -->
    <div class="container-fluid p-5">
        <div class="row px-5">
            <div class="col">
                <h3 style="text-transform: uppercase; color:var(--main-blue)">Ticket Pricing</h3>
                <p style="color:var(--text-grey)">Browse available tickets</p>
            </div>
            <div class="col">
                <ul style="list-style: none;">
                    <li v-for="cat in eventCategories">
                        <b>{{ cat.Cat }}:</b>
                        ${{ cat.Price }}
                    </li>
                </ul>
            </div>
        </div>
    </div>


    <!-- Policies -->
    <div class="container-fluid p-5" style="background-color: var(--light-blue);">
        <div class="row p-5">
            <div class="col">
                <h3 style="text-transform: uppercase; color:var(--main-blue)">Policies</h3>

                <div class="accordion" id="accordionExample">
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button" type="button" data-bs-toggle="collapse"
                                data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                                EXCHANGE & REFUND POLICY
                            </button>
                        </h2>
                        <div id="collapseOne" class="accordion-collapse collapse show"
                            data-bs-parent="#accordionExample">
                            <div class="accordion-body">
                                <ul>
                                    <li>The Organiser/Venue Owner reserves the right, without refund or compensation, to
                                        refuse admission or evict any person(s) whose conduct is disorderly,
                                        inappropriate, or poses a threat to security or the enjoyment of the Event by
                                        others.</li>
                                    <li>Ticket holders assume all risk of injury and responsibility for property loss,
                                        destruction, or theft and release the promoters, performers, sponsors, ticket
                                        outlets, venues, and their employees from any liability thereafter.</li>
                                    <li>The resale of ticket(s) is allowed through the Eventiva website, and a refund
                                        will be issued only if the resale is successfully completed.</li>
                                    <li>There is no refund, exchange, or cancellation once ticket(s) are sold. Upgrade
                                        of ticket(s) is subject to terms & conditions.</li>
                                    <li>We caution members of the public against purchasing tickets from unauthorized
                                        sellers or third-party websites. Tickets purchased through these non-authorized
                                        points of sale may be invalid, with no refunds possible.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                                data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                                ADMISSION POLICY
                            </button>
                        </h2>
                        <div id="collapseTwo" class="accordion-collapse collapse" data-bs-parent="#accordionExample">
                            <div class="accordion-body">
                                <ul>
                                    <li>E-tickets will be issued at the point of sale.</li>
                                    <li>Admission to show/venue by full ticket only. Printed/electronic tickets must be
                                        produced for admission.</li>
                                    <li>There will be no admission for infants in arms and children below 6 years old.
                                    </li>
                                    <li>Individuals aged 6 years old and above will be required to purchase a ticket for
                                        admission.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <!-- Call to action banner -->
    <div class="container p-5">
        <div class="row px-5">
            <div class="col">
                <img src="../assets/cta_icon.png">
            </div>
            <div class="col" style="display: flex; align-items: center;">
                <div>
                    <h1 style="color:var(--main-blue)">Are you ready?</h1>
                    <p>Secure your spot at the most unforgettable events and create lifelong memories by purchasing your
                        tickets now!</p>
                    <br>
                    <button style="text-transform: uppercase;" @click="toCheckout" v-if="doneLoading">Buy your ticket now!</button>
                </div>
            </div>
        </div>
    </div>


    <!-- Toasts -->
    <Toasts/>

</template>

<script>

import NavBar from "../components/nav-bar.vue";
import Toasts from "../components/toasts.vue";
import axios from 'axios';
import { auth } from '../stores/auth';
import { Toast } from 'bootstrap';

export default {
    name: 'event',
    components: {
        NavBar, Toasts
    },
    data() {
        return {
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            eventImage: "../assets/carousel/eventiva_carousel1.png",
            minPrice: 38,
            maxPrice: 80,

            eventDetails: [],
            eventCategories: [],
            formattedDate: "",
            formattedTime: "",

            doneLoading: false,
        }
    },
    methods: {
        toCheckout() {

            if (auth.getUser()) {
                this.$router.push({ path: '/checkout', query: { eventId: [this.eventId], eventDetails: JSON.stringify(this.eventDetails), eventCategories: JSON.stringify(this.eventCategories) } });
            } else {
                const toastElement = document.getElementById('loginFirst');
                const toastInstance = Toast.getOrCreateInstance(toastElement);
                toastInstance.show();
            }
        },
        async fetchEventDetail() {
            try {
                const response = await axios.get(`${this.apiGatewayUrl}/events/${this.eventId}`);
                var rawData = response.data.Event
                this.processDetails(rawData);

                this.updateBannerImage(this.eventDetails.Image);

            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },
        processDetails(rawData) {
            const eventMap = new Map();

            rawData.forEach(event => {
                const key = event.Id; 

                if (!eventMap.has(key)) {

                    eventMap.set(key, {
                        Id: event.Id,
                        Name: event.Name,
                        Venue: event.Venue,
                        Category: event.Category,
                        Capacity: event.Capacity,
                        AvailableTickets: event.AvailableTickets,
                        StartTime: event.StartTime,
                        EndTime: event.EndTime,
                        Description: event.Description,
                        Image: event.Img,
                        dates: [], 
                        eventDateIds: [] 
                    });
                }

                // Push the date and EventDateId into the corresponding arrays
                const existingEvent = eventMap.get(key);
                existingEvent.dates.push(event.Date);
                existingEvent.eventDateIds.push(event.EventDateId);

            });


            // If there's only one event, store it directly instead of as an array
            this.eventDetails = Array.from(eventMap.values())[0]; 
            this.formatDates(this.eventDetails.dates)
            this.formatTimeRange(this.eventDetails.StartTime, this.eventDetails.EndTime)

            this.fetchEventCats(this.eventDetails.eventDateIds);
        },
        async fetchEventCats(eventDateIds) {

            try {
                // Initialize an empty array to store unique categories with details
                this.eventCategories = [];

                // Loop through each eventDateId
                for (const eventDateId of eventDateIds) {
                    // Fetch categories for the current eventDateId
                    const response = await axios.get(`${this.apiGatewayUrl}/events/dates/${eventDateId}/categories`);

                    const categories = response.data.Cats;

                    categories.forEach(category => {

                        const exists = this.eventCategories.some(
                            existingCategory => existingCategory.Cat === category.Cat
                        );

                        if (!exists) {
                            this.eventCategories.push({
                                Cat: category.Cat,
                                Price: category.Price,
                            });
                            if (category.Price < this.minPrice) {
                                this.minPrice = category.Price;
                            }
                            if (category.Price > this.maxPrice) {
                                this.maxPrice = category.Price;
                            }

                        }
                    });
                }
                this.doneLoading = true;

            } catch (error) {
                console.error("Error fetching event categories:", error);
            }
        },
        formatDates(dates) {
            // Convert ISO strings to Date objects and sort them
            const sortedDates = dates.map(date => new Date(date)).sort((a, b) => a - b);

            let formattedDates = [];
            let currentRangeStart = sortedDates[0];
            let currentRangeEnd = sortedDates[0];

            for (let i = 1; i < sortedDates.length; i++) {
                const currentDate = sortedDates[i];
                const previousDate = sortedDates[i - 1];

                // Check if currentDate is consecutive to previousDate
                if ((currentDate - previousDate) / (1000 * 60 * 60 * 24) === 1) {
                    currentRangeEnd = currentDate;
                } else {
                    // Push the formatted range or single date to formattedDates
                    formattedDates.push(this.formatRange(currentRangeStart, currentRangeEnd));
                    currentRangeStart = currentDate;
                    currentRangeEnd = currentDate;
                }
            }

            // Push the last range or single date
            formattedDates.push(this.formatRange(currentRangeStart, currentRangeEnd));

            this.formattedDate = formattedDates.join(", ");
        },
        formatRange(startDate, endDate) {
            const options = { day: "numeric", month: "short" };

            // Check if startDate and endDate are the same
            if (startDate.getTime() === endDate.getTime()) {
                return `${startDate.getDate()} ${startDate.toLocaleString("en-US", { month: "short" })}`; // Single date in "11 May" format
            }

            // If they are in the same month, display as a range within the same month
            if (startDate.getMonth() === endDate.getMonth()) {
                return `${startDate.getDate()}-${endDate.getDate()} ${startDate.toLocaleString("en-US", { month: "short" })}`;
            }

            // If they span different months, display full range
            return `${startDate.getDate()} ${startDate.toLocaleString("en-US", { month: "short" })} - ${endDate.getDate()} ${endDate.toLocaleString("en-US", { month: "short" })}`;
        },
        formatTimeRange(startTime, endTime) {

            const options = { hour: "numeric", minute: "numeric", hour12: true };

            // Parse and format start time
            const start = new Intl.DateTimeFormat("en-US", options).format(
                new Date(`1970-01-01T${startTime}`)
            );

            // Parse and format end time
            const end = new Intl.DateTimeFormat("en-US", options).format(
                new Date(`1970-01-01T${endTime}`)
            );

            this.formattedTime = `${start} - ${end}`;
        },
        updateBannerImage(newUrl) {
            const bannerElement = document.querySelector('.bannerImg');
            bannerElement.style.backgroundImage = `linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)), url('${newUrl}')`;
        }

    },
    mounted() {

        this.eventId = this.$route.query.eventId;
        this.fetchEventDetail();

    },
}
</script>

<style scoped>
.bannerImg {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
        url("../assets/carousel/eventiva_carousel1.png");
    background-repeat: no-repeat;
    background-size: cover;
    height: 50vh;
    width: 100%;
}
</style>