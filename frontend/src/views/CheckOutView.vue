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
                    <select v-model="selectedDate" id="eventDate" class="input-field" style="width: fit-content;">
                        <option disabled value="">Select a date</option>
                        <option v-for="date in listDates" :key="date.value" :value="date.value">
                            {{ date.label }}
                        </option>
                    </select>
                </div>

                <!-- Selecting ticket types and their quantity -->
                <div class="row">

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
                    :disabled="!isStep1Valid || currentStep === steps.length - 1"
                    :class="{ disabledButton: !isStep1Valid }">
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
                                style="padding-right: 10px; color:var(--main-blue);"></i>{{ formatDate(selectedDate) }}
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
                <!-- Name input -->
                <label for="cardName" class="input-label">Name on Card</label>
                <input type="text" id="cardName" class="input-field" required v-model="cardName"
                    style="width: fit-content;" placeholder="Enter your name" />

                <!-- Card Number input -->
                <label for="cardNumber" class="input-label mt-3">Card Number</label>
                <input type="text" id="cardNumber" class="input-field" required v-model="cardNumber"
                    style="width: fit-content;" placeholder="XXXX XXXX XXXX XXXX" />

                <!-- Card Expiry input -->
                <label for="cardExpiry" class="input-label mt-3">Expiry Date (MM/YY)</label>
                <input type="text" id="cardExpiry" class="input-field" required maxlength="5" v-model="cardExpiry"
                    style="width: fit-content;" placeholder="MM/YY" pattern="(0[1-9]|1[0-2])\/[0-9]{2}" />

                <!-- Card CVV input -->
                <label for="cardCVV" class="input-label mt-3">CVV</label>
                <input type="text" id="cardCVV" class="input-field" required maxlength="3" v-model="cardCVV"
                    style="width: fit-content;" placeholder="XXX" />


                <br>
                <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px; margin-top: 30px;"
                    @click="nextStep" :disabled="!isPaymentValid" :class="{ disabledButton: !isPaymentValid }">
                    Confirm Payment
                </button>
                <!-- <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px; margin-top: 30px;"
                    @click="nextStep" :disabled="!isPaymentValid" :class="{ disabledButton: !isPaymentValid }">
                    Confirm Payment
                </button> -->
            </div>

            <div class="col d-flex justify-content-end">
                <div class="selectedEventDetails">
                    <!-- Selected event details -->
                    <h5 style="color:var(--main-blue); text-transform: uppercase;">Selected event details</h5>
                    <p><i class="bi bi-calendar-week-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                        formatDate(selectedDate) }}</p>
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
                        formatDate(selectedDate) }}</p>
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

export default {
    name: 'checkout',
    components: {
        NavBar
    },
    data() {
        return {
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            eventId: 0,

            eventImage: "../assets/carousel/eventiva_carousel1.png",

            previousStep: "browsing event",
            steps: ["Ticket selection", "Confirmation", "Payment", "Complete"], // Timeline steps
            currentStep: 0, // Tracks the current step

            selectedTickets: [{ selectedType: "", quantity: 1, price: 0 }], // Default ticket structure
            selectedDate: '', // Store the selected date

            cardName: '',
            cardNumber: '',
            cardExpiry: '',
            cardCVV: '',
            paymentToken: 'tok_visa',

            formattedDate: "",
            eventDetails: [],
            eventCategories: [],


            user:null,

        }
    },
    computed: {
        isStep1Valid() {
            const hasValidDate =
                this.selectedDate
            const hasValidTickets = this.selectedTickets.every(
                ticket => ticket.selectedType && ticket.quantity > 0
            ); // Ensure each ticket has a type and quantity > 0
            return hasValidDate && hasValidTickets;
        },
        isAddDisabled() {
            return this.selectedTickets.length >= this.eventCategories.length;
        },
        calculatedTickets() {
            return this.selectedTickets.map(ticket => {
                // Find the selected ticket type in eventCategories
                const selectedTicket = this.eventCategories.find(
                    catDetails => catDetails.Cat === ticket.selectedType
                );

                // Use the correct property name 'Price' instead of 'price'
                const price = selectedTicket ? selectedTicket.Price : 0;

                // Calculate subtotal based on quantity and price
                const subtotal = price * ticket.quantity;

                // Return a new object with updated price and subtotal
                return { ...ticket, price, subtotal };
            });
        },
        // Calculate grand total
        grandTotal() {
            return this.calculatedTickets.reduce((total, ticket) => total + ticket.subtotal, 0);
        },
        isPaymentValid() {
            return this.cardName.trim() !== '' &&
                this.cardNumber.replace(/\s/g, '').length === 16 &&
                /^(0[1-9]|1[0-2])\/[0-9]{2}$/.test(this.cardExpiry) &&
                this.cardCVV.length === 3;
        },
        listDates() {
            // Format each date into "13 May 2024" format
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
            // Find the selected category and update its price
            const selectedCategory = this.eventCategories.find(
                (category) => category.Cat === this.selectedTickets[index].selectedType
            );

            if (selectedCategory) {
                // Update the price based on the selected type and quantity
                this.selectedTickets[index].price = selectedCategory.Price;
            }
        },
        removeTicketType(index) {
            // Remove the selected ticket row at the given index
            this.selectedTickets.splice(index, 1);
        },
        nextStep() {
            if (this.currentStep == this.steps.length - 1) {
                this.processPayment();
            }else if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
            }
        },
        prevStep() {
            if (this.currentStep > 0) {
                this.currentStep--;
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

            // Convert the time strings into Date objects
            const start = new Date(`1970-01-01T${startTime}Z`).toLocaleTimeString(
                "en-US",
                options
            );
            const end = new Date(`1970-01-01T${endTime}Z`).toLocaleTimeString(
                "en-US",
                options
            );

            return `${start} - ${end}`;
        },
        formatDate(dateString) {
            // Convert the ISO date string to a Date object
            const date = new Date(dateString);

            // Use Intl.DateTimeFormat to format the date
            const formattedDate = new Intl.DateTimeFormat("en-GB", {
                day: "2-digit",
                month: "long",
                year: "numeric",
            }).format(date);

            return formattedDate;
        },
        async processPayment() {
            console.log(this.user.id);
            try {
                // Prepare the data payload
                const paymentData = {
                    user_id: this.user.id, // Replace with the actual user ID
                    amount: this.grandTotal, // Use grand total as the payment amount
                    payment_token: this.paymentToken, // Replace with your payment token
                };

                // Send POST request to the Flask API
                const response = await axios.post(`${this.apiGatewayUrl}/payments/process`, paymentData, {
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                // Handle successful response
                console.log("Payment Response:", response.data);
                alert("Payment successful! Transaction ID: " + response.data.transaction_id);
                this.currentStep++;
                // cue trigger to process new order composite
            } catch (error) {
                // Handle error response
                console.error("Payment Error:", error.response?.data || error.message);
                alert("Payment failed! " + (error.response?.data.error || error.message));
            }
        },

    },
    created() {
        this.eventId = this.$route.query.eventId;
        this.eventDetails = JSON.parse(this.$route.query.eventDetails);
        this.eventCategories = JSON.parse(this.$route.query.eventCategories);

        this.formatDates(this.eventDetails.dates);
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
</style>