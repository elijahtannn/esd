<template>
    <div class="col">
        <div 
            class="card rounded-0 border-0 addShadow" 
            @click="handleCardClick" 
            style="cursor: pointer;"
        >
            <div class="position-relative">
                <img :src="image || '../assets/carousel/eventiva_carousel1.png'" 
                    class="card-img-top rounded-0"
                    style="object-fit: cover; height: 35vh;">
                <!-- Sold Out Overlay -->
                <div v-if="isSoldOut" class="sold-out-overlay">
                    <span class="sold-out-badge">SOLD OUT</span>
                </div>
            </div>
            <div class="card-body p-4">
                <div class="text-start">
                    <p style="color:var(--main-blue)">{{ category }}</p>
                    <h4 class="card-title">{{ name }}</h4>
                    <p style="text-transform: uppercase; font-size: 14px;">{{ formattedDate }}
                        <br>{{ formatTimeRange(startTime, endTime) }}
                    </p>
                    <p style="font-size: 14px; color:var(--text-grey);">{{ venue }} (capacity: {{ capacity }})</p>
                </div>

                <!-- Conditional buttons for sold out events -->
                <div v-if="isSoldOut" class="d-flex justify-content-between align-items-center">
                    <button 
                        v-if="!isInterestedInResale"
                        @click.stop="openResaleNotificationModal" 
                        class="btn btn-outline-primary w-100"
                        style="text-transform: uppercase;"
                    >
                        Notify When Resale Available
                    </button>
                    <button 
                        v-else
                        class="btn btn-outline-success w-100"
                        style="text-transform: uppercase;"
                        disabled
                    >
                        <i class="bi bi-bell-fill me-2"></i>Notification Set
                    </button>
                </div>

                <div v-else>
                    <button 
                        @click.stop="toEvent" 
                        class="btn btn-primary w-100"
                        style="text-transform: uppercase;"
                    >
                        Learn More
                    </button>

                    <p 
                        v-if="availableTickets < ticketThreshold" 
                        class="text-danger mt-2 mb-0"
                        style="font-size: 14px;"
                    >
                        Tickets Running Low!
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

import axios from 'axios';
import { auth } from '../stores/auth.js';

export default {
    name: 'event',
    data() {
        return {
            ticketThreshold: 30,
            finalDateRange: "",
            formattedDate: "",
            isSoldOut: false,
            isInterestedInResale: false
        }
    },
    props: {
        id: Number,
        name: String,
        dates: Array,
        startTime: String,
        endTime: String,
        venue: String,
        capacity: Number,
        category: String,
        image: String,
        description: String,
    },
    methods: {
        handleCardClick() {
            if (!this.isSoldOut) {
                this.toEvent();
            }
        },
        toEvent() {
            this.$router.push({ path: '/event', query: { eventId: [this.id] } });
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

            return `${start} - ${end}`;
        },

        async checkSoldOutStatus() {
            try {
                const response = await axios.get(`https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI/events/${this.id}/is-sold-out`);
                
                console.log(`Sold out status for event ${this.id}:`, response.data);
                
                if (response.data && response.data.Result) {
                this.isSoldOut = response.data.isSoldOut || false;
                } else {
                this.isSoldOut = false;
                }
                
                console.log(`Event ${this.id} sold out status:`, this.isSoldOut);
            } catch (error) {
                console.error(`Failed to check sold-out status for event ${this.id}`, error);
                this.isSoldOut = false;
            }
        },
        async checkUserInterestStatus() {
            // Get user data from auth store
            const userData = auth.getUser();
            
            if (!userData) {
                // User not logged in, can't check interest status
                this.isInterestedInResale = false;
                return;
            }
            
            const userId = userData.id || userData._id; // Handle both formats
            console.log('Checking interest status for user:', userId); // Debug log
            
            try {
                // Use the correct endpoint to check if user is interested in this event
                const response = await axios.get(
                    `${this.apiGatewayUrl || 'http://localhost:5003'}/user/${userId}/interested-events/${this.id}`
                );
                
                console.log('User interest check response:', response.data);
                
                // Update status based on API response
                this.isInterestedInResale = response.data.is_interested;
            } catch (error) {
                console.error('Failed to check user interest status:', error);
                this.isInterestedInResale = false;
            }
        },
        async openResaleNotificationModal() {
            try {
                // Get user data from auth store
                const userData = auth.getUser();
                
                if (!userData) {
                    // User is not logged in, redirect to login
                    this.$router.push('/login');
                    return;
                }
                const userId = userData.id || userData._id;
                console.log('User ID from auth store:', userId); // Debug log
                
                const response = await axios.post(
                    `${this.apiGatewayUrl || 'http://localhost:5003'}/user/${userId}/interested-events`, 
                    {
                        event_id: this.id
                    }
                );

                // Update UI to show user is now interested
                this.isInterestedInResale = true;
                
                // Simple success message
                alert("We'll notify you when resale tickets become available!");
            } catch (error) {
                console.error('Failed to add event interest', error);
                alert('Failed to register for resale notification. Please try again.');
            }
        }
    },
    mounted() {

        this.formatDates(this.dates);
        this.checkSoldOutStatus();
        this.checkUserInterestStatus(); 
    },

}


</script>


<style scoped>
.sold-out-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
}

.sold-out-badge {
    color: white;
    padding: 10px 20px;
    font-weight: bold;
    text-transform: uppercase;
    border-radius: 5px;
}
</style>