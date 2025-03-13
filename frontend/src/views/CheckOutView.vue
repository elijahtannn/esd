<template>
    <NavBar />

    <!-- Banner -->
    <div class="container-fluid carousel banner mx-0 p-5">
        <div class="row">
            <div class="col-10">
                <div>
                    <p class="bannerText p-5">{{ eventName }}</p>
                    <p class="ms-5"
                        style="background-color: var(--main-blue); padding: 10px 20px; color:white; text-transform: uppercase; font-weight: 600; width: fit-content; margin-top: -30px;">
                        {{ startDate }} - {{ endDate }}, {{ startTime }} - {{ endTime }}
                    </p>
                    <p class="ms-5" style="color: white;">{{ venue }}</p>
                </div>
            </div>
            <div class="col-4"></div>
        </div>
    </div>

    <div class="container-fluid p-5">

        <!-- Arrow to go back -->
        <div class="row px-5">
            <p style="cursor: pointer;" @click="prevStep" :disabled="currentStep === 0" v-if="currentStep != 0">
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
                <label for="email" class="input-label">
                    Date
                </label>
                <div class="input-container">
                    <input type="date" id="date" class="input-field" required placeholder="Enter your email"
                        style="width: fit-content;" />
                </div>

                <!-- Selecting ticket types and their quantity -->
                <div class="row">

                    <!-- Render all ticket types dynamically -->
                    <div v-for="(ticket, index) in tickets" :key="index" class="row">
                        <div class="col-7">
                            <!-- Ticket type dropdown -->
                            <label for="ticketType" class="input-label">Ticket Type</label>
                            <select v-model="ticket.selectedType" class="input-field">
                                <option v-for="(option, idx) in filteredTicketTypes(index)" :key="idx"
                                    :value="option.name">
                                    {{ option.name }} - ${{ option.price }}
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
                            <div v-if="tickets.length > 1" @click="removeTicketType(index)"
                                style="margin-top: 30px; color: var(--text-grey); cursor: pointer;">
                                <i class="bi bi-dash-circle"></i>
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
        </div>


        <!-- Step 1: Confirmation -->
        <div class="row p-5" v-if="currentStep == 1">

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
                    <tr v-for="(ticket, index) in tickets">
                        <th scope="row">{{ ticket.selectedType }}</th>
                        <td>Mark</td>
                        <td>Otto</td>
                        <td>@mdo</td>
                    </tr>
                    <tr>
                        <th scope="row">2</th>
                        <td>Jacob</td>
                        <td>Thornton</td>
                        <td>@fat</td>
                    </tr>
                    <tr>
                        <th colspan="3" class="text-end">Grand Total</th>
                        <td>@twitter</td>
                    </tr>
                </tbody>
            </table>
        </div>


        <!-- Step 3: Payment -->
        <div class="row p-5" v-if="currentStep == 2">


        </div>


        <!-- Step 4: Complete -->
        <div class="row p-5" v-if="currentStep == 3">


        </div>


        <div class="row ps-5 ms-1">
            <button style="text-transform: uppercase; width: fit-content; padding: 5px 30px;" @click="nextStep"
                :disabled="currentStep === steps.length - 1">Next Step</button>
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
            steps: ["Ticket selection", "Confirmation", "Payment", "Complete"], // Timeline steps
            currentStep: 0, // Tracks the current step


            ticketTypes: [{ name: 'Cat 1', price: 190 }, { name: 'Cat 2', price: 209 }, { name: 'Cat 3', price: 400 }],
            tickets: [
                { selectedType: '', quantity: 1 }, // Default ticket type
            ],



        }
    },
    computed: {
        isAddDisabled() {
            const selectedTypes = this.tickets.map(ticket => ticket.selectedType);
            return selectedTypes.length >= this.ticketTypes.length;
        },
    },
    methods: {
        goBack() {
            this.$router.back()
        },
        addTicketType() {
            if (!this.isAddDisabled) {
                this.tickets.push({ selectedType: '', quantity: 1 });
            }
        },
        // Method to filter available ticket types for each dropdown
        filteredTicketTypes(index) {
            const selectedTypes = this.tickets.map(ticket => ticket.selectedType);
            return this.ticketTypes.filter(option => !selectedTypes.includes(option.name) || option.name === this.tickets[index].selectedType);
        },
        // Method to remove a ticket type input
        removeTicketType(index) {
            if (this.tickets.length > 1) {
                this.tickets.splice(index, 1);
            }
        },
        nextStep() {
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
            }
        },
        prevStep() {
            if (this.currentStep > 0) {
                this.currentStep--;
            }
        },
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
</style>