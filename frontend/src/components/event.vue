<template>

    <div class="col">
        <div class="card rounded-0 border-0 addShadow" @click="toEvent" style="cursor: pointer;">
            <img src="../assets/carousel/eventiva_carousel1.png" class="card-img-top rounded-0"
                style="object-fit: cover; height: 35vh;">
            <div class="card-body p-4">
                <div class="text-start">
                    <p style="color:var(--main-blue)">{{ category }}</p>
                    <h4 class="card-title">{{ name }}</h4>
                    <p style="text-transform: uppercase; font-size: 14px;">{{ formattedDate }}
                    <br>{{ formatTimeRange(startTime, endTime) }}</p>
                    <p style="font-size: 14px; color:var(--text-grey);">{{ venue }} (capacity: {{ capacity }})</p>
                </div>

                <button style="padding: 5px 20px; text-transform: uppercase;" class="text-center" @click="toEvent">
                    Learn more
                </button>

                <p style="color:red; font-size: 14px;" v-if="availableTickets < ticketThreshold">Tickets running low!
                </p>
            </div>
        </div>

    </div>

</template>

<script>


export default {
    name: 'event',
    data() {
        return {
            ticketThreshold: 30,
            finalDateRange: "",
            formattedDate: "",
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
    },
    mounted() {

        this.formatDates(this.dates);
    },

}


</script>