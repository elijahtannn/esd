<template>
    <div>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <div>
            <NavBar />
            <div v-if="user">
                <!-- Banner -->
                <div class="container-fluid bannerImg banner mx-0 p-5">
                    <div class="row">
                        <div class="col-8">
                            <div>
                                <p class="bannerText">Hello,<br> {{ user.name }}</p>
                            </div>
                        </div>
                        <div class="col-4"></div>
                    </div>
                </div>

                <!-- White boxes for profile and orders -->
                <div class="content-wrapper">
                    <!-- profile box -->
                    <div class="profile-box">
                        <h3 class="profile-heading">PROFILE</h3>
                        <p><span class="label">Id:</span> <br> {{ user._id || user.id}}</p>
                        <p><span class="label">Name:</span> <br> {{ user.name }}</p>
                        <p><span class="label">Email:</span> <br> {{ user.email }}</p>
                        <!-- EDITABLE MOBILE NUMBER -->
                        <p>
                            <span class="label">Mobile Number:</span> <br>
                            <span v-if="!isEditing">{{ user.mobile }}</span>
                            <input v-else type="text" v-model="user.mobile" class="mobile-input" />

                            <!-- Font Awesome Pencil Icon -->
                            <button @click="toggleEdit" class="icon-button">
                                <i :class="isEditing ? 'fas fa-check' : 'fas fa-pencil-alt'"></i>
                            </button>
                        </p>

                        <!-- Divider Line Between Notifications and Phone -->
                        <hr class="divider" />

                        <div class="notifications-section">
                            <!-- Notifications Label -->
                            <span class="notifications-label">Notifications:</span>

                            <!-- Notifications List -->
                            <div class="notifications-list">
                                <div
                                    v-for="(notification, index) in notifications"
                                    :key="index"
                                    class="notification-item"
                                    @click="showExpandedNotification(notification)">
                                    {{ notification.message.substring(0, 30) }}
                                </div>
                            </div>
                        </div>

                        <!-- Expanded Notification Modal -->
                        <div v-if="isModalOpen" class="notification-modal" @click.self="closeModal">
                            <div class="modal-content">
                                <span class="close-button" @click="closeModal">&times;</span>
                                <h3>Pending Transfer</h3>
                                <br>
                                <p>{{ selectedNotification.message }}</p> <!-- Display full message -->
                            </div>
                        </div>

                    </div>
                    <!-- order box -->
                    <div class="orders-box">
                        <h3 class="event-heading">EVENT ORDERS</h3>
                        <!-- Tab Links -->
                        <div class="tabs">
                            <button class="tablinks active" @click="openTab($event, 'Upcoming')">Upcoming</button>
                            <button class="tablinks" @click="openTab($event, 'History')">History</button>
                        </div>

                        <!-- Tab Content -->
                        <!-- UPCOMING TAB -->
                        <div id="Upcoming" class="tabcontent active order-card">
                            <hr>
                            <div v-if="upcomingOrders.length === 0">No orders available</div>
                            <div v-else>
                                <div v-for="order in upcomingOrders" :key="order.OrderId" class="order-item">
                                    <div class="order-header" @click="toggleExpand(order)">
                                        <div>
                                            <!-- Event Information -->
                                            <div class="order-summary">
                                                <span><strong>{{ order.EventName }}</strong></span><br>
                                                <span>{{ formatDates(order.EventDate) }}, {{ order.Venue }}</span>
                                            </div> <br>
                                            <!-- Order Information -->
                                            <div>
                                                <span style="font-size: 15px; color: grey;">Order Information: #{{
                                                    order.OrderId }}</span><br>
                                                <span style="font-size: 15px; color: grey;">Ticket Quantity: {{
                                                    order.TicketQuantity }}</span><br>
                                                <span style="font-size: 15px; color: grey;">Total Cost: ${{
                                                    order.TotalCost.toFixed(2) }}</span>
                                            </div>
                                        </div>
                                        <button class="toggle-button">
                                            <i
                                                :class="['fa-solid', order.isExpanded ? 'fa-chevron-up' : 'fa-chevron-down', 'icon']"></i>
                                        </button>

                                    </div>
                                    <div v-if="order.isExpanded" class="order-details">
                                        <!-- HERE -->
                                        <div class="order-details">
                                            <!-- QR cards -->
                                            <br>
                                            <div class="qr-cards">
                                                <!-- DEBUGGING -->
                                                <div class="qr-card" v-for="ticket in order.tickets" :key="ticket.ticketId">
                                                    <!-- Three-dot menu -->
                                                    <div class="menu-container">
                                                        <span class="menu-icon" @click="toggleMenu(ticket)">
                                                            &#x22EE; <!-- Vertical three dots -->
                                                        </span>
                                                        <div v-if="openMenus.includes(ticket) && !disabledMenus[ticket.ticketId]" class="menu-dropdown">
                                                            <p @click="handleOption('resale', ticket)">Resell Ticket</p>
                                                            <p @click="handleOption('transfer', ticket)">Transfer Ticket</p>
                                                        </div>
                                                    </div>
                                                    <!--QR code image -->
                                                    <div>
                                                        <img src="../assets/images/dummy QR code.png" class="qr-image">
                                                    </div>
                                                    <!-- TICKET ON HOLD TEXT -->
                                                    <div v-if="ticketStatuses[ticket.ticketId] && !ticketStatuses[ticket.ticketId].isQrVisible" class="ticket-status">
                                                        <p
                                                            style="background-color:#2A68E1; color: white; margin-top:30px; padding: 5px; text-align: center;">
                                                            <strong>ON HOLD:</strong> {{ ticketStatuses[ticket.ticketId].status }}
                                                        </p>
                                                    </div>
                                                    <p>#{{ ticket.ticketId }}</p>
                                                    <p>Type: {{ ticket.categoryName }}</p>
                                                    <p>Seat: {{ ticket.seatInfo }}</p>
                                                    <p v-if="ticket.price !== undefined">Price: ${{ ticket.price }}</p>

                                                    <!-- Resale Confirmation Modal -->
                                                    <div v-if="showResalePopup" class="modal-overlay">
                                                        <div class="modal-content">
                                                            <!-- Close (X) Button -->
                                                            <span class="close-button" @click="closePopup">&times;</span>

                                                            <h3>Are you sure you want to resell your ticket?</h3>
                                                            <p><strong>Ticket ID:</strong> #{{ selectedTicket.ticketId }}</p>
                                                            <p><strong>Type:</strong>{{ selectedTicket.categoryName }}</p>
                                                            <p><strong>Price:</strong> ${{ selectedTicket.price }}</p>
                                                            <p><strong>Seat:</strong> #{{ selectedTicket.seatInfo }}</p>
                                                            <hr>
                                                            <!-- Mandatory Checkbox for Agreement -->
                                                            <div class="checkbox-container">
                                                                <input type="checkbox" id="agreeCheckbox" v-model="isAgreed" />
                                                                <label for="agreeCheckbox">
                                                                    I agree that a refund will only be issued once the resale process is
                                                                    complete and the transaction is finalized.
                                                                </label>
                                                            </div>

                                                            <button @click="confirmResale" class="confirm-button">CONFIRM</button>
                                                        </div>
                                                    </div>
                                                    <!-- Transfer Ticket Modal -->
                                                    <div v-if="showTransferPopup" class="modal-overlay">
                                                        <div class="modal-content">
                                                            <!-- Close (X) Button -->
                                                            <span class="close-button" @click="closePopup">&times;</span>

                                                            <h3>Transfer your ticket</h3>
                                                            <p><strong>Ticket ID:</strong> #{{ selectedTicket.ticketId }}</p>
                                                            <p><strong>Type:</strong> {{ selectedTicket.categoryName }}</p>
                                                            <p><strong>Price:</strong> ${{ selectedTicket.price }}</p>
                                                            <p><strong>Seat:</strong> #{{ selectedTicket.seatInfo }}</p>
                                                            <hr>

                                                            <!-- Input Form for Recipient's Information -->
                                                            <div class="form-group">
                                                                <label for="email">Recipient's Email:</label>
                                                                <input type="text" id="email" v-model="email"
                                                                    placeholder="Enter email" />
                                                            </div>

                                                            <!-- Mandatory Checkbox for Agreement -->
                                                            <div class="checkbox-container">
                                                                <input type="checkbox" id="agreeCheckbox" v-model="isAgreed" />
                                                                <label for="agreeCheckbox" style="font-size: 14px;">
                                                                    I agree that transfer will only be completed once both parties has
                                                                    accepted the transfer. Once the transfer is complete, it cannot be
                                                                    undone or transferred back to me. </label>
                                                            </div>
                                                            <button @click="confirmTransfer" class="confirm-button">CONFIRM</button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <hr>
                                </div>
                            </div>
                        </div>

                        <!-- History Tab -->
                        <div id="History" class="tabcontent">
                            <hr>
                            <div v-if="pastOrders.length === 0">No past events available.</div>
                            <div v-else>
                                <div class="order-header" v-for="order in pastOrders" :key="order.OrderId">
                                    <template v-if="order.EventDetails">
                                        <div class="order-summary">
                                            <span><strong>{{ order.EventName }}</strong></span><br>
                                            <span>{{ formatDates(order.EventDate) }}, {{ order.Venue }}</span>
                                        </div> <br>
                                            <!-- Order Information -->
                                        <div>
                                            <span style="font-size: 15px; color: grey;">Order Information: #{{order.OrderId }}</span><br>
                                            <span style="font-size: 15px; color: grey;">Ticket Quantity: {{order.TicketQuantity }}</span><br>
                                            <span style="font-size: 15px; color: grey;">Total Cost: ${{order.TotalCost.toFixed(2) }}</span>
                                        </div>
                                    </template>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import NavBar from "../components/nav-bar.vue";
import { auth } from '../stores/auth';
import axios from 'axios';

export default {
    name: 'profile',
    components: {
        NavBar
    },
    data() {
        return {
            isModalOpen: false,
            selectedNotification: null,
            unreadCount: 1,
            notifications: [{ id: 1, message: "You have a new message!jgahgjhjrhtuihbersuibyuithythyivuhtrbytruibghygyg" },
            { id: 2, message: "Your order has been shippedlkrjybijtryimjbinjhyifjhoijbtyuoguihugmofb!" }],
            //test notif
            disabledMenus: {},
            selectedTicket: null,
            ticketStatuses: {},
            user: null,
            isExpanded: false,
            isMenuOpen: false,
            showResalePopup: false,
            isAgreed: false,
            showTransferPopup: false,
            eventivaAccount: '',
            email: '',
            isEditing: false,
            isQrVisible: true,
            ticketStatus: "",
            orderList: [],
            eventList: [],
            ticketList: [],
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            openMenus: [],
            
        }
    },
    mounted() {
    const userData = auth.getUser();

    if (!userData || (!userData._id && !userData.id)) { // Check for both _id and id
        console.error("User ID is missing from auth.getUser()!", userData);
        return;
    }

    // Normalize the user object: map id to _id if _id is missing
    this.user = { ...userData, _id: userData._id || userData.id };

    console.log("Fetched User from auth:", this.user);

    // Fetch the latest user data
    this.fetchUserData()
        .then(() => this.fetchOrders())
        .catch(error => console.error("Error in fetching process:", error));
},

    methods: {
        toggleExpand(order) {
            order.isExpanded = !order.isExpanded;
        },
        // BACKEND METHODS
        async fetchOrders() {
            try {
                if (!this.user || (!this.user._id && !this.user.id)) {
                console.error('No user ID available');
                return;
                }

                const userId = this.user._id || this.user.id;
                console.log("Fetching orders for user:", userId);
                
                const response = await axios.get(`${this.apiGatewayUrl}/orders/user/${userId}`);
                const rawOrders = response.data;
                console.log("Raw Order response:", rawOrders);
                
                this.processOrders(rawOrders);
                
                // After processing orders, fetch additional details
                await this.fetchOrderDetails();
            } catch (error) {
                console.error('Error fetching orders:', error);
            }
        },

        processOrders(rawOrders) {
            console.log("Processing Order", rawOrders);
            this.orderList = rawOrders.map(order => {
                // Extract all ticket IDs from the nested structure
                let allTicketIds = [];
                if (order.tickets && Array.isArray(order.tickets)) {
                // Flatten the nested ticketIds arrays from all category objects
                order.tickets.forEach(category => {
                    if (category.ticketIds && Array.isArray(category.ticketIds)) {
                    allTicketIds = [...allTicketIds, ...category.ticketIds];
                    }
                });
                }
                
                return {
                OrderId: order.orderId,
                TicketQuantity: allTicketIds.length,
                TotalCost: order.totalAmount,
                Status: order.status,
                ticketIds: allTicketIds,
                eventId: order.eventId,
                eventDateId: order.eventDateId,
                tickets: [],
                isExpanded: false,
                EventName: '',
                Venue: '',
                EventDate: null
                };
            });
            console.log("Processed Order List:", this.orderList);
        },

        // Fetch additional details from other services
        async fetchOrderDetails() {
        try {
            // Process each order to get event details and ticket details
            await Promise.all(this.orderList.map(async (order) => {
            // Fetch event details
            try {
                const eventResponse = await axios.get(`/api/events/events/${order.eventId}`);
                
                // Process event data
                if (eventResponse.data && eventResponse.data.Event && eventResponse.data.Event.length > 0) {
                const eventData = eventResponse.data.Event[0];
                order.EventName = eventData.Name;
                order.Venue = eventData.Venue;
                order.EventDate = eventData.Date;
                }
            } catch (eventError) {
                console.error(`Error fetching event details for order ${order.OrderId}:`, eventError);
                order.EventName = 'Event Information Unavailable';
                order.Venue = 'Venue Information Unavailable';
            }
            
            // Fetch ticket details first
            if (order.ticketIds && order.ticketIds.length > 0) {
                try {
                const ticketPromises = order.ticketIds.map(ticketId => 
                    axios.get(`${this.apiGatewayUrl}/tickets/${ticketId}`)
                );
                
                const ticketResponses = await Promise.all(ticketPromises);
                
                // Process ticket data
                const ticketsWithBasicInfo = ticketResponses.map(response => {
                    const ticketData = response.data;
                    return {
                    ticketId: ticketData._id,
                    catId: ticketData.cat_id,
                    categoryName: `Category ${ticketData.cat_id}`, // Default value, will be updated
                    price: 0, // Default value, will be updated
                    seatInfo: ticketData.seat_info,
                    status: ticketData.status,
                    isTransferable: ticketData.is_transferable,
                    qrCode: ticketData.qr_code || ""
                    };
                });
                
                // Now fetch category details for each ticket
                const ticketsWithCategoryPromises = ticketsWithBasicInfo.map(async (ticket) => {
                    try {
                    // Use the specific category endpoint you've shown
                    const categoryResponse = await axios.get(
                    `https://personal-ibno2rmi.outsystemscloud.com/Event/rest/EventAPI/events/dates/categories/${ticket.catId}`,
                    { 
                        headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                        }
                    }
                    );
                    
                    // Extract category information from response
                    if (categoryResponse.data && 
                        categoryResponse.data.Result && 
                        categoryResponse.data.Result.Success &&
                        categoryResponse.data.TicketCategory) {
                        
                        console.log("Cat data: ", categoryResponse.data);
                        const categoryData = categoryResponse.data.TicketCategory;
                        ticket.categoryName = categoryData.Cat || `Category ${ticket.catId}`;
                        ticket.price = categoryData.Price || 0;
                    }
                    } catch (catError) {
                    console.error(`Error fetching category ${ticket.catId} details:`, catError);
                    }
                    return ticket;
                });
                
                // Wait for all category information to be retrieved
                order.tickets = await Promise.all(ticketsWithCategoryPromises);
                
                } catch (ticketError) {
                console.error(`Error fetching ticket details for order ${order.OrderId}:`, ticketError);
                }
            }
            }));
            
            console.log('Orders with complete details:', this.orderList);
        } catch (error) {
            console.error('Error fetching order details:', error);
        }
        },

        formatDates(dates) {
            if (!dates) return '';
            return new Date(dates).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        },
        // FRONTEND METHODS
        async toggleEdit() {
            if (this.isEditing) {
                console.log("Before update:", this.user.mobile); // Debugging log
                await this.updateMobileNumber();
            }
            this.isEditing = !this.isEditing;
        },
        async updateMobileNumber() {
            try {
                let userId = this.user?._id || auth.getUser()?._id; // Fallback check

                if (!userId) {
                    console.error("User ID is missing! Cannot update mobile number.");
                    return;
                }
                const url = `${this.apiGatewayUrl}/user/${userId}`;
                console.log("Sending request to:", url);
                const response = await axios.put(url, { mobile: this.user.mobile || "" }, {
                    headers: { "Content-Type": "application/json" }
                });
                console.log("API Response:", response.data);
                if (response.status === 200) {
                    console.log("Mobile number updated successfully:", response.data);
                    
                    // Store the latest user data
                    auth.setUser(response.data);
                    
                    // Fetch updated user data
                    this.fetchUserData();
                } else {
                    console.error("Failed to update mobile number:", response.data.error);
                }
            } catch (error) {
                console.error("Error updating mobile number:", error);
            }
        },
        async fetchUserData() {
            try {
                let userId = this.user?._id || auth.getUser()?._id; // Double-check user ID

                if (!userId) {
                    console.error("User ID is missing! Cannot fetch user data.");
                    return;
                }

                const response = await axios.get(`${this.apiGatewayUrl}/user/${userId}`);
                
                if (response.status === 200) {
                    console.log("Fetched latest user data:", response.data);
                    this.user = response.data;
                    auth.setUser(response.data); // Store updated user data
                }
            } catch (error) {
                console.error("Error fetching user data:", error);
            }
        },
        openTab(event, tabName) {
            // Remove active class from all tabs and content
            document.querySelectorAll('.tablinks, .tabcontent').forEach(element => {
                element.classList.remove('active');
            });
            // Add active class to clicked tab and corresponding content
            event.currentTarget.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        },
        toggleMenu(ticketId) {
            const index = this.openMenus.indexOf(ticketId);
            if (index === -1) {
                this.openMenus.push(ticketId);
            } else {
                this.openMenus.splice(index, 1);
            }
        },
        handleOption(action, ticket) {
            this.selectedTicket = ticket;
            if (action === 'resale') {
                this.showResalePopup = true; // Show the resale confirmation modal
                console.log('Resell Ticket clicked');
            } else if (action === 'transfer') {
                console.log("Transfer Ticket clicked");
                this.showTransferPopup = true;
            }
            this.selectedTicket = ticket;
            this.disabledMenus = { ...this.disabledMenus, [ticket.ticketId]: true };
        },
        confirmResale() {
            if (this.isAgreed && this.selectedTicket) {
                this.ticketStatuses[this.selectedTicket.ticketId] = {
                isQrVisible: false,
                status: "TICKET IS BEING RESOLD"
                };
                this.closePopup();
            } else {
                console.log('Agreement not checked or no ticket selected');
            }
        },
        closePopup() {
            this.showResalePopup = false;
            this.showTransferPopup = false;
            this.openMenus= [];
        },
        closeMenu() {
            // this.isMenuOpen = false;
            this.openMenus= [];
        },
        confirmTransfer() {
            if ( this.email && this.isAgreed && this.selectedTicket) {
                this.ticketStatuses[this.selectedTicket.ticketId] = {
                isQrVisible: false,
                status: "TICKET IS BEING TRANSFERRED"
                };
                this.closePopup();
            } else {
                console.log('Please fill in all the details');
            }
        },
        async validateTicket() {
            try {
                const validateData = {
                    recipientEmail: this.email,
                    senderEmail: this.user.email,
                };

                const response = await axios.post(`http://localhost:8004/validateTransfer/${this.selectedTicket.ticketId}`, validateData);

                console.log("Validate Response:", response.data);
            } catch (error) {
                console.error("Payment Error:", error.response?.data || error.message);
            }
        },
        async transferTicket(acceptedChoice) {
            try {
                const transferData = {
                    accepted: acceptedChoice, // change "true" to correct variable
                    recipient_email: true, // change "true" to correct variable
                    sender_id: true, // change "true" to correct variable
                    sender_email: true, // change "true" to correct variable
                };
                const response = await axios.post(`http://localhost:8011/transfer/${ticketId}`, transferData); // change "ticketId" to correct variable

                console.log("Transfer Response:", response.data);
            } catch (error) {
                console.error("Payment Error:", error.response?.data || error.message);
            }
        },
        showExpandedNotification(notification) {
            this.selectedNotification = notification; // Set the clicked notification
            this.isModalOpen = true; // Open the modal
        },
        
        closeModal() {
            this.isModalOpen = false; // Close the modal
            this.selectedNotification = null; // Reset selected notification
        }

    },
    computed: {
        upcomingOrders() {
            const now = new Date();
            return this.orderList.filter(order => new Date(order.EventDate) > now);
        },
        pastOrders() {
            const now = new Date();
            return this.orderList.filter(order => new Date(order.EventDate) <= now);
        }
    }
}
</script>

<style scoped>
/* ARROW CHEVRON RELATED */
.toggle-button {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
}

.icon {
    margin-left: 8px;
    color: black;
    /* Adjust color if needed */
}

/* ORDER CARD RELATED */
.order-card {
    border-bottom: 1px solid #ddd;
    padding: 10px;
}

.order-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
}

button {
    background: none;
    border: none;
    font-size: 16px;
}

.rotate {
    transform: rotate(180deg);
}

.container {
    padding: 20px;
}

.card {
    max-width: 600px;
    margin: 0 auto;
}

.bannerImg {
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
        url("../assets/images/background_profile.png");
    background-repeat: no-repeat;
    background-size: cover;
    height: 60vh;
    width: 100%;
}

.content-wrapper {
    display: flex;
    justify-content: center;
    gap: 20px;
    position: relative;
    margin-top: -50px;
}

.profile-box {
    flex: 0 0 auto;
    width: 20%;
    background-color: white;
    padding: 20px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 2;
}

.orders-box {
    flex: 0 0 auto;
    width: 70%;
    background-color: white;
    padding: 20px;
    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
}

.label {
    color: #808080;
}

.profile-heading {
    color: #2A68E1;
    text-align: center;
    font-size: 24px;
}

.event-heading {
    color: #2A68E1;
    text-align: center;
    font-size: 24px;
    margin-bottom: 20px;
}

/* Tabs container */
.tabs {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
    position: relative;
}

/* Tab buttons */
.tablinks {
    background-color: #f1f1f1;
    border: none;
    outline: none;
    padding: 15px 100px;
    cursor: pointer;
    font-size: 16px;
    border-radius: 10px;
    margin: 0 10px;
    transition: background-color 0.3s ease, color 0.3s ease;
    color: black;
}

.tablinks.active {
    background-color: #2A68E1;
    color: white;
}

.tablinks:hover {
    background-color: #d9d9d9;
}


.tabcontent {
    display: none;
}

.tabcontent.active {
    display: block;
}

/* QR CODE RELATED */
.qr-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    /* Match card width */
    gap: 16px;
    /* Add spacing between cards */
    width: 100%;
    /* Use full width for better responsiveness */
    margin: auto;
    /* Center the grid */
    justify-items: start;
    /* Align items to the left */
}

.qr-image {
    display: block;
    /* Makes the image a block element */
    margin-left: auto;
    /* Centers image horizontally */
    margin-right: auto;
    /* Centers image horizontally */
    max-width: 100%;
    /* Adjust size for better fit */
    height: auto;
    /* Maintain aspect ratio */
}


.qr-card p {
    margin: 5px;
}

/* 3 dot related */
.qr-card {
    position: relative;
    padding: 16px;
    border: 1px solid #ddd;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    /* Make card width responsive */
    max-width: 300px;
    /* Set maximum width */
}

.menu-container {
    position: absolute;
    top: 10px;
    right: 10px;
}

.menu-icon {
    font-size: 20px;
    cursor: pointer;
    margin-right: 10px;
}

.menu-dropdown {
    position: absolute;
    top: 25px;
    right: 0;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
    padding: 5px;
    z-index: 10;
}

.menu-dropdown p {
    margin: 0;
    padding: 8px 12px;
    cursor: pointer;
    white-space: nowrap;
}

.menu-dropdown p:hover {
    background: #f0f0f0;
}

/* RESALE MODAL RELATED */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    text-align: center;
    width: 500px;
    position: relative;
    /* Keep the close button (X) positioned */
}

.modal-content>h3 {
    margin-top: 10px;
}

.confirm-button {
    background: #2A68E1;
    /* Blue for confirm button */
    color: white;
    border: none;
    padding: 10px;
    margin-top: 10px;
    cursor: pointer;
    width: 100%;
    border-radius: 5px;
}

/* STYLING CHECKBOX */
.checkbox-container {
    display: flex;
    align-items: center;
    margin-top: 10px;
}

.checkbox-container input {
    margin-right: 10px;
}

.confirm-button:disabled {
    background: #d6d6d6;
    /* Disabled button color */
    cursor: not-allowed;
}

/* X BUTTON ON MODAL */
.close-button {
    position: absolute;
    top: 10px;
    right: 20px;
    font-size: 24px;
    cursor: pointer;
    color: #333;
}

.close-button:hover {
    color: #ff0000;
    /* Change color on hover */
}

/* RESALE TICKET POPUP */
.form-group {
    margin-bottom: 12px;
    text-align: left;
}

.form-group label {
    display: block;
    font-weight: bold;
    font-size: 12px;
}

.form-group input {
    width: 100%;
    padding: 5px;
    margin-top: 5px;
    border-radius: 5px;
    border: 1px solid #ccc;
    font-size: 12px;
}

/* EDITABLE MOBILE PHONE */
.mobile-input {
    border: 1px solid #ccc;
    padding: 5px;
    width: 150px;
}

.icon-button {
    margin-right: 10px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    color: black;
}

.icon-button:hover {
    color: dark grey;
}

/* Divider Line Under Mobile Number */
.divider {
    border: none;
    border-top: 1px solid #ddd;
    margin: 10px 0;
}

.notifications-section {
    margin-top: 10px;
}

/* Notifications List */
.notifications-list {
    margin-top: 10px;
}


/* Individual Notification Item */
.notification-item {
    background-color: #f9f9f9; /* Light background for each notification */
    padding: 10px; /* Adds spacing inside each notification */
    border-radius: 8px; /* Rounded corners for a modern look */
    font-size: 14px;
    color: #333;
    margin-bottom: 10px; /* Adds spacing between notifications */
}

.notification-item:hover {
    background-color: #e6e6e6; /* Slightly darker background on hover */
}

/* Notifications Label */
.notifications-label {
    font-size: 1em;
    color: #808080;
    margin-bottom: 10px;
    display: block; /* Ensures the label stays on its own line */
}

/* Notification Modal */
.notification-modal {
    position: fixed; /* Keeps the modal fixed in place */
    top: 50%; /* Centers vertically */
    left: 50%; /* Centers horizontally */
    transform: translate(-50%, -50%); /* Adjusts for modal's own dimensions */
    z-index: 3; /* Ensures it appears above other elements */
    background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent background */
    width: 100vw; /* Full viewport width for the overlay */
    height: 100vh; /* Full viewport height for the overlay */
    display: flex; /* Flexbox for centering content */
    justify-content: center; /* Centers horizontally */
    align-items: center; /* Centers vertically */
}
/* Modal Content Box */
/* Modal Content Box */
.modal-content {
    background-color: white; /* Modal box background color */
    padding: 20px; /* Adds spacing inside the modal box */
    border-radius: 8px; /* Rounded corners for a modern look */
    width: 80%; /* Width of the modal box (adjustable) */
    max-width: 400px; /* Maximum width for larger screens */
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3); /* Adds a shadow for depth */
    overflow-wrap: break-word; /* Ensures long words break to fit within the container */
    word-wrap: break-word; /* Legacy support for word wrapping */
    overflow-y: auto; /* Adds scroll if content exceeds modal height */
    max-height: 80vh; /* Limits height to prevent overflow outside viewport */
}


</style>