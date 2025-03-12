<template>
    <NavBar />

    <!-- Banner -->
    <div class="container-fluid carousel banner mx-0 p-5">
        <div class="row">
            <div class="col-10">
                <div>
                    <p class="bannerText p-5">{{ eventName }}</p>
                </div>
            </div>
            <div class="col-4"></div>
        </div>
    </div>


    <!-- Event details -->
    <div class="container-fluid p-5">
        <div class="row px-5">
            <div class="col">
                <p><i class="bi bi-calendar-week-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{
                    startDate }} - {{ endDate }}</p>
                <p><i class="bi bi-alarm-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{ startTime }}
                    - {{ endTime }}</p>
                <p><i class="bi bi-geo-alt-fill" style="padding-right: 10px; color:var(--main-blue);"></i>{{ venue }}
                </p>
            </div>
            <div class="col">
                <p>Price</p>
                <h2 style="color:var(--main-blue); margin-top: -10px;">${{ minPrice }} - ${{ maxPrice }}</h2>
            </div>
            <div class="col text-center">
                <button style="text-transform: uppercase;" @click="toCheckout">Buy tickets</button>
                <p style="color:var(--text-grey)">max capacity: {{ capacity }}</p>
            </div>
        </div>
    </div>

    <!-- Event description -->
    <div class="container-fluid p-5" style="background-color: var(--light-blue);">
        <div class="row p-5">
            <div class="col-6">
                <h3 style="text-transform: uppercase; color:var(--main-blue)">Event details</h3>
                <p style="line-height: 30px; margin-right: 100px;">{{ description }}</p>
            </div>
            <div class="col-6">
                <img src="../assets/carousel/eventiva_carousel1.png" style="width: 100%; object-fit: cover;">
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
                    <li><b>CAT 1:</b> $80</li>
                    <li><b>CAT 2:</b> $70</li>
                    <li><b>CAT 3:</b> $58</li>
                    <li><b>CAT 4:</b> $48</li>
                    <li><b>CAT 5:</b> $38</li>
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
                    <button style="text-transform: uppercase;" @click="toCheckout">Buy your ticket now!</button>
                </div>
            </div>
        </div>
    </div>

</template>

<script>

import NavBar from "../components/nav-bar.vue";

export default {
    name: 'event',
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
            description: "Lady Gaga announced her highly anticipated return to Singapore with four massive stadium shows this spring. Performing in the country for the first time in 13 years since her 2012 Born This Way Ball Tour, the four-show run at National Stadium kicks off on Sunday, May 18, 2025, with additional performances on May 19, 21, and 24. Today's announcement comes just days after the release of Gaga's seventh studio album, MAYHEM, out now via Interscope Records. Marking a return to her pop roots, MAYHEM reaffirms that Gaga is a master of reinvention, crafting an album that is as bold and eclectic as it is deeply personal. It is a declaration of artistic freedom, a celebration of life's contradictions, and a testament to music's power to bring people together in the face of chaos.",
            capacity: 899,
            eventType: "Concert",
            availableTickets: 200,
            eventImage: "../assets/carousel/eventiva_carousel1.png",
            minPrice: 38,
            maxPrice: 80,
        }
    },
    methods: {
        toCheckout(){
            this.$router.push({ path: '/checkout', query: { eventId: [this.eventId] } });
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