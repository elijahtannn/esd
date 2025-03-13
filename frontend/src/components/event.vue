<template>

    <div class="col">
        <div class="card rounded-0 border-0 addShadow">
            <img src="../assets/carousel/eventiva_carousel1.png" class="card-img-top rounded-0" style="object-fit: cover; height: 35vh;">
            <div class="card-body p-4">
                <div class="text-start">
                    <p style="color:var(--main-blue)">{{ eventType }}</p>
                    <h4 class="card-title">{{ name }}</h4>
                    <p style="text-transform: uppercase; font-size: 14px;">{{ dateRange }}, {{ startTime }} - {{ endTime }}</p>
                    <p style="font-size: 14px; color:var(--text-grey);">{{ venue }} (capacity: {{ capacity }})</p>
                </div>
    
                <button style="padding: 5px 20px; text-transform: uppercase;" class="text-center" @click="toEvent">
                    Buy Now
                </button>
    
                <p style="color:red; font-size: 14px;" v-if="availableTickets < ticketThreshold">Tickets running low!</p>
            </div>
        </div>

    </div>

</template>

<script>


export default {
    name: 'event',
    data() {
        return {
            dateRange: "",
            ticketThreshold: 30,
        }
    },
    props: {
        id: Number,
        name: String,
        startDate: String,
        endDate: String,
        startTime: String,
        endTime: String,
        venue: String,
        capacity: Number,
        eventType: String,
        availableTickets: Number,
        image: String,
        description: String,
    },
    methods: {
        toEvent(){
            this.$router.push({ path: '/event', query: { eventId: [this.id] } });
        }
    },
    mounted() {
        if (this.startDate == this.endDate){
            this.dateRange = this.startDate;
        }else{
            this.dateRange = this.startDate + " - " + this.endDate;
        }
    },
    
}


</script>