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
            <p style="cursor: pointer; width: fit-content;" @click="goBack" v-else>
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

                <!-- Timer -->
                <div class="timer-container" v-if="isTimerActive">
                    <div class="timer" :class="{ 'timer-warning': remainingSeconds <= 10 }">
                        <span class="timer-text">Time remaining:</span>
                        <span class="timer-count">{{ minutes }}:{{ seconds.toString().padStart(2, '0') }}</span>
                        <p style="font-size: 12px; color:var(--text-grey)">Your tickets are being reserved. Please
                            complete the transaction within the time limit or you will be routed back to the events
                            page.</p>
                    </div>
                </div>

                <!-- Step Content -->
                <div class="step-content pt-5" style="margin-bottom: -70px;">
                    <div v-if="currentStep === 0">
                        <h2>Ticket Selection</h2>
                        <p>Select your tickets and quantities here.</p>
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
                        @change="handleDateChange">
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
                <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px;" @click="nextStep"
                    :disabled="!isFormValid || eventCategories.length === 0"
                    :class="{ 'disabled-button': !isFormValid || eventCategories.length === 0 }">
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

            <div class="col" v-if="loadingPayment">
                <p>Your payment is loading... Please give us a moment.</p>
            </div>
            <div class="col" v-else>

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
                    has been sent to {{ user.email }} with your ticket details.</p>

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

    <!-- Toasts -->
    <Toasts/>

</template>

<script>

import NavBar from "../components/nav-bar.vue";
import Toasts from "../components/toasts.vue";

import axios, { formToJSON } from 'axios';
import { auth } from '../stores/auth';
import { Toast } from 'bootstrap';
import { loadStripe } from '@stripe/stripe-js';

export default {
    name: 'checkout',
    components: {
        NavBar, Toasts
    },
    data() {
        return {
            // Misc
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            stripePublishableKey: import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY,
            
            // Event Info
            eventId: 0,
            eventImage: "../assets/carousel/eventiva_carousel1.png",
            formattedDate: "",
            eventDetails: [],
            eventDates: [],
            eventCategories: [],
            
            // Steps related
            previousStep: "browsing event",
            steps: ["Ticket selection", "Confirmation", "Payment", "Complete"],
            currentStep: 0,

            // Selection
            selectedTickets: [{ selectedType: "", quantity: 1, price: 0 }],
            selectedDate: '',
            selectedDateId: '',

            // Payment
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
            loadingPayment: false,
            paymentStatus: false,

            // User
            user: null,

            // Timer
            paymentTimer: null,
            abortController: null,
            secondsThreshold: 20,
            remainingSeconds: 20,
            isTimerActive: false,
        }
    },
    computed: {
        minutes() {
            return Math.floor(this.remainingSeconds / 60);
        },
        seconds() {
            return this.remainingSeconds % 60;
        },
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
        isFormValid() {
            // Ensure a date is selected and all ticket types are filled with valid quantities
            return this.selectedDateId !== '' && this.selectedTickets.every(ticket => ticket.selectedType !== '' && ticket.quantity > 0);
        }
    },
    methods: {
        goBack() {
            this.cancelReservation();
            if (this.currentStep == 0 || this.currentStep == 3) {
                this.$router.push({ path: '/event', query: { eventId: [this.eventId] } });
            } else {
                this.prevStep();
            }
        },
        handleDateChange() {
            // Reset ticket selections to a single default entry
            this.selectedTickets = [{ selectedType: "", quantity: 1, price: 0 }];

            // Clear existing categories and fetch new ones for the selected date
            this.eventCategories = [];
            this.showCategories();
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

                if (this.currentStep == 1) {
                    this.reserveTicket();
                } else {
                    this.currentStep++;
                }
            }
        },
        prevStep() {
            if (this.currentStep == 2) {
                this.cancelReservation(true);
                this.remainingSeconds = this.secondsThreshold;
                this.currentStep--;
            } else if (this.currentStep > 0) {
                this.currentStep--;
            }
        },
        displayPayment() {
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
            this.cancelReservation(false);
            this.loadingPayment = true;
            try {
                const paymentData = {
                    user_id: this.user._id ?? this.user.id,
                    user_email: this.user.email,
                    event_id: this.eventId,
                    event_date_id: this.selectedDateId,
                    eventName: this.eventDetails.Name,
                    eventDate: this.selectedDate.date,
                    venue: this.eventDetails.Venue,
                    payment_token: this.paymentToken,
                    ticket_arr: this.selectedTickets.map(ticket => ({
                        catId: ticket.catId,
                        quantity: ticket.quantity,
                        price: ticket.price
                    }))
                };

                const response = await axios.post(`${this.apiGatewayUrl}/process_ticket_order`, paymentData, {
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                this.currentStep = 3;
                this.paymentStatus = true;
            } catch (error) {
                this.currentStep = 0;
                this.remainingSeconds = this.secondsThreshold;
                this.cancelReservation(true);

                // show toast
                const toastElement = document.getElementById('paymentDecline');
                const toastInstance = Toast.getOrCreateInstance(toastElement);
                toastInstance.show();
            }
            this.loadingPayment = false;
        },
        async getToken() {
            if (!this.cardNumberElement) {
                console.error("Card element not initialized.");
                return;
            }

            const { token, error } = await this.stripe.createToken(this.cardNumberElement);

            if (error) {
                // show toast
                const toastElement = document.getElementById('incompleteFields');
                const toastInstance = Toast.getOrCreateInstance(toastElement);
                toastInstance.show();
            } else {
                this.paymentToken = token.id;
                this.processPayment();
            }
        },
        async getDates() {
            try {
                const response = await axios.get(`${this.apiGatewayUrl}/events/${this.eventId}`);

                for (let info of response.data.Event) {
                    var formattedDate = this.formatDate(info.Date);
                    this.eventDates.push({ 'dateId': info.EventDateId, 'date': formattedDate })
                }

            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },
        async showCategories() {
            this.eventCategories = []
            try {
                const response = await axios.get(`${this.apiGatewayUrl}/events/dates/${this.selectedDateId}/categories`);

                for (let info of response.data.Cats) {
                    this.eventCategories.push({ 'Cat': info.Cat, 'CatId': info.Id, 'Price': info.Price, 'AvailableTickets': info.AvailableTickets })
                }

            } catch (error) {
                console.error('Error fetching events:', error);
            }
        },
        async reserveTicket() {

            // Create abort controller for the request
            this.reservationController = new AbortController();

            var checkTicketsAvail = true;

            for (var ticket of this.selectedTickets) {
                const response = await axios.get(`${this.apiGatewayUrl}/events/dates/${this.selectedDateId}/categories`);

                // loop through and find category 
                for (var cat of response.data.Cats) {
                    // found category info
                    if (cat.Id == ticket.catId) {
                        // check if there is insufficent tickets then return and inform user
                        if (cat.AvailableTickets < ticket.quantity) {
                            checkTicketsAvail = false;
                            break;
                        }
                    }
                }
            }

            if (checkTicketsAvail == true) {
                this.currentStep++;
                this.displayPayment()

                try {
                    const ticketsData = {
                        selected_tickets: this.selectedTickets,
                        event_date_id: this.selectedDateId,
                        event_id: this.eventId,
                        user_id: this.user._id ?? this.user.id,
                        event_category: this.eventDetails.Category,
                    };

                    // Create new AbortController for this request
                    this.abortController = new AbortController();
                    this.startPaymentTimer();

                    const response = await axios.post(`${this.apiGatewayUrl}/reserve_ticket`, ticketsData,
                        {
                            signal: this.abortController.signal,
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );

                    if (this.paymentTimer) clearTimeout(this.paymentTimer);

                    if (response.data.status === false) {
                        if (this.currentStep != 3) {
                            this.goBack();
                        }
                    }
                } catch (error) {
                    if (!axios.isCancel(error)) {
                        if (this.currentStep != 3) {
                            this.goBack();
                        }
                    }
                }



            } else {
                // show toast
                const toastElement = document.getElementById('insufficientTickets');
                const toastInstance = Toast.getOrCreateInstance(toastElement);
                toastInstance.show();
            }

        },
        startPaymentTimer() {
            if (this.paymentTimer) clearTimeout(this.paymentTimer);

            this.isTimerActive = true;
            this.paymentTimer = setInterval(() => {
                if (this.remainingSeconds > 0) {
                    this.remainingSeconds--;
                    if (this.remainingSeconds == 0 && this.paymentStatus == false) {
                        
                        // show toast
                        const toastElement = document.getElementById('timeOut');
                        const toastInstance = Toast.getOrCreateInstance(toastElement);
                        toastInstance.show();
                    }
                } else {
                    this.cancelReservation(true);
                    this.goBack();
                }
            }, 1000);
        },
        cancelReservation(goback) {
            this.isTimerActive = false;
            if (this.abortController) {
                this.abortController.abort(); // Proper cancellation method
                this.abortController = null;
            }
            if (this.paymentTimer) {
                clearTimeout(this.paymentTimer);
                this.paymentTimer = null;
                this.loadingPayment = false;
                if(goback){this.goBack();}
            }
        },
        updateBannerImage(newUrl) {
            const bannerElement = document.querySelector('.bannerImg');
            bannerElement.style.backgroundImage = `linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)), url('${newUrl}')`;
        }

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

        this.updateBannerImage(this.eventDetails.Image);

    },
    beforeDestroy() {
        this.cancelReservation(true);
    }
}
</script>

<style scoped>
.disabled-button {
    background-color: #cccccc;
    color: #666666;
    cursor: not-allowed;
}

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
    z-index: -1;
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
}

.timeline-step.active .circle,
.timeline-step.completed .circle {
    background-color: #007bff;
}

.step-label {
    margin-top: 8px;
    font-size: 14px;
}

.timeline-step.active .step-label,
.timeline-step.completed .step-label {
    color: #007bff;
}

.timeline-step .step-label {
    color: #a0a0a0;
}

/* Navigation Buttons */
.navigation-buttons button {
    margin-right: 10px;
}


.bold-line {
    border-top: 2px solid #b3b3b3;
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
}

.timer-count {
    font-size: 24px;
    font-weight: bold;
    color: #e74c3c;
    margin: 0 5px;
}
</style>