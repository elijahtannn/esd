<template>
    <NavBar />

    <!-- Banner -->
    <div class="container-fluid bannerImg banner mx-0 p-5">
        <div class="row">
            <div class="col-12">
                <div>
                    <p class="bannerText p-5">{{ eventDetails.Name }}</p>
                    <p class="ms-5"
                        style="background-color: var(--main-blue); padding: 10px 20px; color:white; text-transform: uppercase; font-weight: 600; width: fit-content; margin-top: -30px;">
                        {{ formattedDate }}<br>{{ formatTimeRange(eventDetails.StartTime, eventDetails.EndTime) }}
                    </p>
                    <p class="ms-5" style="color: white;">{{ eventDetails.Venue }}</p>
                </div>
            </div>
        </div>
    </div>

    <div class="container-fluid p-5">

        <!-- Arrow to go back -->
        <div class="row px-5">
            <p style="cursor: pointer;" @click="prevStep" :disabled="currentStep === 0"
                v-if="currentStep == 1 || currentStep == 2">
                <i class="bi bi-arrow-left-short"></i> Back to {{ steps[currentStep - 1] }}
            </p>
            <p style="cursor: pointer;" @click="goBack" v-else>
                <i class="bi bi-arrow-left-short"></i> Back to browsing event
            </p>
        </div>


        <!-- Timeline info -->
        <div class="row p-5">
            <div>
                <!-- Timeline -->
                <div class="timeline">
                    <div v-for="(step, index) in steps" :key="index" class="timeline-step"
                        :class="{ active: currentStep === index, completed: currentStep > index }">
                        <div class="circle"></div>
                        <span class="step-label">{{ step }}</span>
                    </div>
                </div>

                <!-- Step Content -->
                <div class="step-content pt-5" style="margin-bottom: -70px;">
                    <div v-if="currentStep === 0">
                        <h2>Ticket Selection</h2>
                        <p>Select your tickets and quantities here.</p>
                        <!-- Add your ticket selection component here -->
                    </div>
                    <div v-if="currentStep === 1">
                        <h2>Confirmation</h2>
                        <p>Review your selected tickets and confirm.</p>
                    </div>
                    <div v-if="currentStep === 2">
                        <h2>Payment</h2>
                        <p>Enter your payment details to proceed.</p>
                    </div>
                    <div v-if="currentStep === 3">
                        <h2>Complete</h2>
                        <p>Your booking is complete. Thank you!</p>
                    </div>
                </div>

            </div>
        </div>

        <!-- Step 1: Ticket selection -->
        <div class="row p-5" v-if="currentStep == 0">

            <!-- selections -->
            <div class="col">



                <!-- date input -->
                <label for="date" class="input-label">Date</label>
                <div class="input-container">
                    <select v-model="selectedDateId" id="eventDate" class="input-field" style="width: fit-content;"
                        @change="showCategories()">
                        <option disabled value="">Select a date</option>
                        <option v-for="date in eventDates" :key="date.dateId" :value="date.dateId">
                            {{ date.date }}
                        </option>
                    </select>
                </div>

                <!-- Selecting ticket types and their quantity -->
                <div class="row" v-if="selectedDateId != ''">

                    <!-- Render all ticket types dynamically -->
                    <div>
                        <div v-for="(ticket, index) in selectedTickets" :key="index" class="row">
                            <div class="col-7">
                                <!-- Ticket type dropdown -->
                                <label for="ticketType" class="input-label">Ticket Type</label>
                                <select v-model="ticket.selectedType" class="input-field"
                                    @change="updateTicketPrice(index)">
                                    <option v-for="(category, idx) in filteredeventCategories(index)" :key="idx"
                                        :value="category.Cat">
                                        {{ category.Cat }} - ${{ category.Price }}
                                    </option>
                                </select>
                            </div>
                            <div class="col-3">
                                <!-- Quantity input -->
                                <label for="quantity" class="input-label">Quantity</label>
                                <input type="number" v-model.number="ticket.quantity" class="input-field" min="1" />
                            </div>
                            <div class="col-2" style="display: flex; align-items: center;">
                                <!-- Remove ticket type button -->
                                <div v-if="selectedTickets.length > 1" @click="removeTicketType(index)"
                                    style=" margin-top: 30px; color: var(--text-grey); cursor: pointer;">
                                    <i class="bi bi-dash-circle"></i>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Add more ticket type button -->
                    <div class="row" v-if="!isAddDisabled">
                        <p @click="addTicketType"
                            style="color: var(--text-grey); font-size: 14px; cursor: pointer; width: fit-content;">
                            <i class="bi bi-plus"></i> Add more ticket type
                        </p>
                    </div>

                </div>





            </div>
            <div class="col"></div>

            <div class="row ps-4 pt-5">
                <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px;" @click="nextStep">
                    Next Step
                </button>
            </div>
        </div>


        <!-- Step 2: Confirmation -->
        <div class="row p-5" v-if="currentStep == 1">
            <div class="col">
                <table class="table">
                    <thead>
                        <tr>
                            <th scope="col">Type</th>
                            <th scope="col">Quantity</th>
                            <th scope="col">Price</th>
                            <th scope="col">Sub-Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(ticket, index) in calculatedTickets" :key="index">
                            <td>{{ ticket.selectedType }}</td>
                            <td>{{ ticket.quantity }}</td>
                            <td>${{ ticket.price }}</td>
                            <td>${{ ticket.subtotal }}</td>
                        </tr>
                        <tr class="bold-line">
                            <th colspan="3" class="text-end">Grand Total</th>
                            <td>${{ grandTotal }}</td>
                        </tr>
                    </tbody>
                </table>

                <div class="row ps-4 pt-5">
                    <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px;" @click="nextStep">
                        Next Step
                    </button>
                </div>
            </div>

            <!-- Selected event details -->
            <div class="col">
                <div class="col d-flex justify-content-end">
                    <div class="selectedEventDetails">
                        <h5 style="color:var(--main-blue); text-transform: uppercase;">Selected event details</h5>
                        <p><i class="bi bi-calendar-week-fill"
                                style="padding-right: 10px; color:var(--main-blue);"></i>{{ selectedDate.date }}
                        </p>
                        <p><i class="bi bi-alarm-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                            formatTimeRange(eventDetails.StartTime, eventDetails.EndTime) }}</p>
                        <p><i class="bi bi-geo-alt-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                            eventDetails.Venue }}</p>
                    </div>
                </div>
            </div>

        </div>


        <!-- Step 3: Payment -->
        <div class="row p-5" v-if="currentStep == 2">

            <div class="col">

                <div>

                    <div v-if="isStripeLoaded">
                        <label>Name on Card</label>
                        <input type="text" id="cardName" class="input-field" />

                        <label>Card Number</label>
                        <div id="cardNumber" class="input-field"></div>

                        <label>Expiry Date</label>
                        <div id="cardExpiry" class="input-field"></div>

                        <label>CVC</label>
                        <div id="cardCvc" class="input-field"></div>
                    </div>

                    <p v-else>Loading payment form...</p>
                </div>

                <br>
                <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px; margin-top: 30px;"
                    @click="getToken">
                    Confirm Payment
                </button>
            </div>

            <div class="col d-flex justify-content-end">
                <div class="selectedEventDetails">
                    <!-- Selected event details -->
                    <h5 style="color:var(--main-blue); text-transform: uppercase;">Selected event details</h5>
                    <p><i class="bi bi-calendar-week-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        selectedDate.date }}</p>
                    <p><i class="bi bi-alarm-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        formatTimeRange(eventDetails.StartTime, eventDetails.EndTime) }}</p>
                    <p><i class="bi bi-geo-alt-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        eventDetails.Venue }}
                    </p>

                    <hr>

                    <!-- Ticket details -->
                    <h5 style="color:var(--main-blue); text-transform: uppercase;">Ticket details</h5>
                    <table class="table">
                        <tbody>
                            <tr v-for="(ticket, index) in calculatedTickets" :key="index">
                                <td>{{ ticket.quantity }}x {{ ticket.selectedType }}</td>
                                <td>${{ ticket.subtotal }}</td>
                            </tr>
                            <tr class="bold-line">
                                <th>Grand Total</th>
                                <td>${{ grandTotal }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>


        </div>


        <!-- Step 4: Complete -->
        <div class="row p-5" v-if="currentStep == 3">

            <div class="col text-center">
                <h3>We are happy that you chose</h3>
                <img src="../assets/EVENTIVA.png" width="30%">
                <br>
                <img src="../assets/confirm.png" width="20%" style="margin: 20px;">

                <p>Your tickets have been successfully <b>confirmed!</b></p>
                <p style="color:var(--text-grey); width: 60%; margin: auto; margin-bottom: 30px;">A confirmation email
                    has been sent to yadayada@gmail.com with your ticket details.</p>

                <router-link to="/"><button style="text-transform: uppercase;">Browse more events</button></router-link>
            </div>

            <div class="col d-flex justify-content-end">
                <div class="selectedEventDetails">
                    <!-- Selected event details -->
                    <h5 style="color:var(--main-blue); text-transform: uppercase;">Selected event details</h5>
                    <p><i class="bi bi-calendar-week-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        selectedDate.date }}</p>
                    <p><i class="bi bi-alarm-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        formatTimeRange(eventDetails.StartTime, eventDetails.EndTime) }}</p>
                    <p><i class="bi bi-geo-alt-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        eventDetails.Venue
                    }}
                    </p>

                    <hr>

                    <!-- Ticket details -->
                    <h5 style="color:var(--main-blue); text-transform: uppercase;">Ticket details</h5>
                    <table class="table">
                        <tbody>
                            <tr v-for="(ticket, index) in calculatedTickets" :key="index">
                                <td>{{ ticket.quantity }}x {{ ticket.selectedType }}</td>
                                <td>${{ ticket.subtotal }}</td>
                            </tr>
                            <tr class="bold-line">
                                <th>Grand Total</th>
                                <td>${{ grandTotal }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>



    </div>


</template>

<script>

import NavBar from "../components/nav-bar.vue";
import axios, { formToJSON } from 'axios';
import { auth } from '../stores/auth';

import { loadStripe } from '@stripe/stripe-js';

export default {
    name: 'checkout',
    components: {
        NavBar
    },
    data() {
        return {
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            stripePublishableKey: import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY,
            eventId: 0,
            eventImage: "../assets/carousel/eventiva_carousel1.png",

            previousStep: "browsing event",
            steps: ["Ticket selection", "Confirmation", "Payment", "Complete"],
            currentStep: 0,

            selectedTickets: [{ selectedType: "", quantity: 1, price: 0 }],
            selectedDate: '',
            selectedDateId: '',

            cardName: '',
            cardNumber: '',
            cardExpiry: '',
            cardCVV: '',
            paymentToken: '',
            stripe: null,
            elements: null,
            cardNumberElement: null,
            cardExpiryElement: null,
            cardCvcElement: null,
            isStripeLoaded: false,

            formattedDate: "",
            eventDetails: [],
            eventDates: [],
            eventCategories: [],

            user: null,


        }
    },
    computed: {
        selectedDate() {
            return this.eventDates.find(dateObj => dateObj.dateId === this.selectedDateId);
        },
        isAddDisabled() {
            return this.selectedTickets.length >= this.eventCategories.length;
        },
        calculatedTickets() {
            return this.selectedTickets.map(ticket => {
                const selectedTicket = this.eventCategories.find(
                    catDetails => catDetails.Cat === ticket.selectedType
                );

                const price = selectedTicket ? selectedTicket.Price : 0;

                const subtotal = price * ticket.quantity;

                return { ...ticket, price, subtotal };
            });
        },
        grandTotal() {
            return this.calculatedTickets.reduce((total, ticket) => total + ticket.subtotal, 0);
        },
        listDates() {
            return this.eventDetails.dates.map((dateString) => {
                const date = new Date(dateString);
                const formatted = new Intl.DateTimeFormat("en-GB", {
                    day: "2-digit",
                    month: "long",
                    year: "numeric",
                }).format(date);
                return { value: dateString, label: formatted };
            });
        },
    },
    methods: {
        goBack() {
            this.$router.back()
        },
        filteredeventCategories(index) {
            // Get all currently selected types except for the current row
            const selectedTypes = this.selectedTickets.map((ticket, idx) =>
                idx !== index ? ticket.selectedType : null
            );

            // Filter out already selected categories, but include the current row's selection
            return this.eventCategories.filter(
                (category) =>
                    !selectedTypes.includes(category.Cat) ||
                    category.Cat === this.selectedTickets[index].selectedType
            );
        },
        addTicketType() {
            // Add a new ticket row with default values
            if (this.selectedTickets.length < this.eventCategories.length) {
                this.selectedTickets.push({ selectedType: "", quantity: 1, price: 0 });
            } else {
                alert("All categories have been selected.");
            }
        },
        updateTicketPrice(index) {
            const selectedCategory = this.eventCategories.find(
                (category) => category.Cat === this.selectedTickets[index].selectedType
            );

            if (selectedCategory) {
                this.selectedTickets[index].price = selectedCategory.Price;
                this.selectedTickets[index].catId = selectedCategory.CatId;
            }
        },
        removeTicketType(index) {
            this.selectedTickets.splice(index, 1);
        },
        nextStep() {
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;

                if (this.currentStep == 2) {
                    this.elements = this.stripe.elements();
                    this.isStripeLoaded = true;

                    // Wait until the DOM updates
                    this.$nextTick(() => {
                        if (document.getElementById('cardNumber')) {
                            this.cardNumberElement = this.elements.create('cardNumber');
                            this.cardExpiryElement = this.elements.create('cardExpiry');
                            this.cardCvcElement = this.elements.create('cardCvc');

                            this.cardNumberElement.mount('#cardNumber');
                            this.cardExpiryElement.mount('#cardExpiry');
                            this.cardCvcElement.mount('#cardCvc');
                        } else {
                            console.error("Card input fields are not found in the DOM.");
                        }
                    });
                }else if(this.currentStep == 1){
                    // create ticket and change ticket status to reserved 
                    this.reserveTicket();
                }
            }
        },
        prevStep() {
            if (this.currentStep > 0) {
                this.currentStep--;
            }
        },
        formatDates(dates) {
            const sortedDates = dates.map(date => new Date(date)).sort((a, b) => a - b);

            let formattedDates = [];
            let currentRangeStart = sortedDates[0];
            let currentRangeEnd = sortedDates[0];

            for (let i = 1; i < sortedDates.length; i++) {
                const currentDate = sortedDates[i];
                const previousDate = sortedDates[i - 1];

                if ((currentDate - previousDate) / (1000 * 60 * 60 * 24) === 1) {
                    currentRangeEnd = currentDate;
                } else {
                    formattedDates.push(this.formatRange(currentRangeStart, currentRangeEnd));
                    currentRangeStart = currentDate;
                    currentRangeEnd = currentDate;
                }
            }

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
        formatDate(dateString) {
            const date = new Date(dateString);

            const formattedDate = new Intl.DateTimeFormat("en-GB", {
                day: "2-digit",
                month: "long",
                year: "numeric",
            }).format(date);

            return formattedDate;
        },
        async processPayment() {

            // console.log(this.selectedTickets);

            try {
                const paymentData = {
                    user_id: this.user.id,
                    EventId: this.eventId,
                    EventDateId: this.selectedDateId,
                    payment_token: this.paymentToken,
                    ticketArr: this.selectedTickets,
                };

                const response = await axios.post(`http://localhost:8080/process_ticket_order`, paymentData, {
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                console.log("Payment Response:", response.data);
                this.currentStep++;
            } catch (error) {
                console.error("Payment Error:", error.response?.data || error.message);
            }
        },
        async getToken() {
            if (!this.cardNumberElement) {
                console.error("Card element not initialized.");
                return;
            }

            const { token, error } = await this.stripe.createToken(this.cardNumberElement);

            if (error) {
                console.error(error.message);
            } else {
                console.log('Token:', token.id);
                this.paymentToken = token.id;
                this.processPayment();
            }
        },
        async getDates() {
            try {
                const response = await axios.get(`${this.apiGatewayUrl}/events/${this.eventId}`);
                console.log(response.data.Event);

                for (let info of response.data.Event) {
                    var formattedDate = this.formatDate(info.Date);
                    this.eventDates.push({ 'dateId': info.EventDateId, 'date': formattedDate })
                }

            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },
        async showCategories() {
            try {
                const response = await axios.get(`${this.apiGatewayUrl}/events/dates/${this.selectedDateId}/categories`);
                console.log(response.data.Cats);
                
                for (let info of response.data.Cats) {
                    this.eventCategories.push({ 'Cat': info.Cat, 'CatId': info.Id, 'Price': info.Price, 'AvailableTickets': info.AvailableTickets })
                }
                
            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },
        async reserveTicket() {

            // for (let i = 0; i < this.selectedTickets.length; i++) {
            //     const element = array[i];
                
            // }

            try {
                const ticketsData = {
                    selectedTickets: this.selectedTickets,
                    selectedDateId: this.selectedDateId,
                    selectedEventId: this.eventId,
                    userId: this.user.id,
                };
                const response = await axios.post(`http://localhost:8006/reserve_ticket`, ticketsData, {
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                console.log(response.data);

            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },

        
    },
    created() {
        this.eventId = Number(this.$route.query.eventId);
        this.eventDetails = JSON.parse(this.$route.query.eventDetails);

        this.getDates();
        this.formatDates(this.eventDetails.dates);
    },
    async mounted() {

        const userData = auth.getUser();
        if (userData) {
            this.user = userData;
        }

        this.stripe = await loadStripe(this.stripePublishableKey);
        if (!this.stripe) {
            console.error("Stripe failed to load.");
            return;
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
    height: 50vh;
    width: 100%;
}


/* inputs */
.input-label {
    display: block;
    font-size: 12px;
    margin-bottom: 5px;
    text-align: left;
}

.input-container {
    margin-bottom: 15px;
}

.input-field {
    width: 100%;
    padding: 8px;
    margin-top: 5px;
    border: 1px solid #ccc;
    font-size: 14px;
}

.input-field:focus {
    outline: none;
    border-color: #2A68E1;
}



/* Timeline */
.timeline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    margin-bottom: 30px;
}

.timeline::before {
    content: "";
    position: absolute;
    top: 12%;
    left: 0;
    right: 0;
    height: 2px;
    background-color: #e0e0e0;
    /* Default grey line */
    z-index: -1;
    /* Send the line behind the circles */
}

.timeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.circle {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #e0e0e0;
    /* Default grey */
}

.timeline-step.active .circle,
.timeline-step.completed .circle {
    background-color: #007bff;
    /* Blue for active/completed steps */
}

.step-label {
    margin-top: 8px;
    font-size: 14px;
}

.timeline-step.active .step-label,
.timeline-step.completed .step-label {
    color: #007bff;
    /* Blue for active/completed text */
}

.timeline-step .step-label {
    color: #a0a0a0;
    /* Grey for inactive text */
}

/* Navigation Buttons */
.navigation-buttons button {
    margin-right: 10px;
}


.bold-line {
    border-top: 2px solid #b3b3b3;
    /* Makes the line bold and black */
}


.selectedEventDetails {
    border: 1px solid rgb(202, 202, 202);
    border-radius: 5px;
    padding: 30px;
    width: fit-content;
    top: 0;
}


.paymentInputs {
    width: 100%;
    padding: 8px;
    margin-top: 5px;
    border: 1px solid #ccc;
    /* font-size: 14px; */
}
</style>