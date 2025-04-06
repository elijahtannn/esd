<template>
    <div>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <div>
            <NavBar />
            <!-- Waiting for Resale Modal -->
            <div v-if="isResaleModalVisible" class="modal-overlay">
                <div class="modal-content">
                    <p>{{ resaleMessage }}</p>
                    <div v-if="isResaleInProgress" class="spinner"></div>
                    <button v-else @click="isResaleModalVisible = false">Close</button>
                </div>
            </div>
            <div v-if="user">
                <!-- Banner -->
                <div class="container-fluid bannerImg banner mx-0 p-5">
                    <div class="row">
                        <div class="col-12">
                            <div>
                                <p class="bannerText">Hello,<br> {{ user.name }}</p>
                            </div>
                        </div>
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
                            <span class="notifications-label">Notifications:</span>
                            
                            <!-- Debug info -->
                            <div v-if="pendingTransferTickets.length === 0" class="debug-info">
                                No pending transfers found
                            </div>
                            
                            <!-- Notifications List -->
                            <div class="notifications-list">
                                <div
                                    v-for="ticket in pendingTransferTickets"
                                    :key="ticket._id"
                                    class="notification-item"
                                    @click="showExpandedNotification(ticket)">
                                    <div class="notification-content">
                                        <strong>Pending Ticket Transfer</strong>
                                        <p>Ticket ID: {{ ticket._id }}</p>
                                        <p>Seat: {{ ticket.seat_info }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Divider Line Between Notifications and Interested Events -->
                        <hr class="divider" />

                        <div class="interested-events-section">
                            
                            <div v-if="interestedEvents.length > 0" class="interested-event-list">
                                <div 
                                    class="interested-event-item interested-event"
                                    @click="showInterestedEventsModal = true"
                                >
                                    <div class="interested-event-content">
                                        <strong>Interested Events</strong>
                                        <p>You're interested in {{ interestedEvents.length }} event(s).</p>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="no-interested-events">
                                <p>No interested events</p>
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
                            <div v-if="loadingMsg">Your orders are loading please hold on ...</div>
                            <div v-if="upcomingOrders.length === 0 && loadingMsg == false">No orders available</div>
                            <div v-if="loadingMsg == false">
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

                                                <span style="font-size: 15px; color: grey;">Total Cost: ${{ order.TotalCost.toFixed(2) }}</span><br>
                                                    
                                                    <span v-if="hasRefundedTickets(order)" class="resold-ticket-info">
                                                    <i class="fas fa-check-circle" style="color: #4CAF50;"></i> 
                                                    <span style="color: #4CAF50; font-weight: 500;">
                                                        {{ getRefundedTicketsCount(order) }} ticket(s) successfully resold and refunded
                                                    </span>
                                                </span>
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
                                                        <span class="menu-icon" :class="{ 'disabled': ticket.status !== 'SOLD' || !ticket.isTransferable }" @click="toggleMenu(ticket)">
                                                            &#x22EE; <!-- Vertical three dots -->
                                                        </span>
                                                        <div v-if="openMenus.includes(ticket)" class="menu-dropdown">
                                                            <p @click="handleOption('resale', ticket)">Resell Ticket</p>
                                                            <p @click="handleOption('transfer', ticket)">Transfer Ticket</p>
                                                        </div>
                                                    </div>
                                                    <!--QR code image -->
                                                    <div>
                                                        <img v-if="ticket.qrCode" :src="ticket.qrCode" alt="QR Code" class="qr-image"/>
                                                        <img v-else src="../assets/images/dummy QR code.png" alt="Fallback QR Code" class="qr-image"/>
                                                    </div>
                                                    <!-- TICKET ON HOLD TEXT -->
                                                    <div>
                                                        <div v-if="ticket.status == 'RESALE' " class="ticket-status">
                                                            <p
                                                                style="background-color:#2A68E1; color: white; margin-top:30px; padding: 5px; text-align: center;">
                                                                <strong>ON HOLD:</strong> TICKET IS BEING RESOLD
                                                            </p>
                                                        </div>
                                                        <div v-if="ticket.status == 'PENDING_TRANSFER' " class="ticket-status">
                                                            <p
                                                                style="background-color:#2A68E1; color: white; margin-top:30px; padding: 5px; text-align: center;">
                                                                <strong>ON HOLD:</strong> TICKET IS BEING TRANSFERRED
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <p>#{{ ticket.ticketId }}</p>
                                                    <p>Type: {{ ticket.categoryName }}</p>
                                                    <p>Seat: {{ ticket.seatInfo }}</p>
                                                    <p v-if="ticket.price !== undefined">Price: ${{ ticket.price }}</p>
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
                
                <!-- MOVED MODALS TO MAIN CONTAINER LEVEL -->
                
                <!-- Expanded Notification Modal -->
                <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
                    <div class="modal-content">
                        <span class="close-button" @click="closeModal">&times;</span>
                        <h3>Pending Transfer</h3>
                        <br>
                        <div v-if="selectedNotification">
                            <p><strong>Ticket ID:</strong> #{{ selectedNotification._id }}</p>
                            <p><strong>Category:</strong> Category {{ selectedNotification.cat_id }}</p>
                            <p><strong>Seat:</strong> {{ selectedNotification.seat_info }}</p>
                            <p><strong>From:</strong> {{ selectedNotification.owner_email }}</p>
                            
                            <div class="button-group">
                                <button 
                                    @click="handleTransferResponse(true)" 
                                    class="accept-button"
                                >
                                    Accept
                                </button>
                                <button 
                                    @click="handleTransferResponse(false)" 
                                    class="reject-button"
                                >
                                    Reject
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Interested Events Modal -->
                <div v-if="showInterestedEventsModal" class="modal-overlay" @click.self="showInterestedEventsModal = false">
                    <div class="modal-content">
                        <span class="close-button" @click="showInterestedEventsModal = false">&times;</span>
                        <h3>Interested Events</h3>
                        <br>
                        <div v-if="interestedEvents.length === 0" class="no-events">
                            <p>No interested events found.</p>
                        </div>
                        <div v-else class="interested-events-list">
                            <div 
                                v-for="event in interestedEvents" 
                                :key="event.id" 
                                class="interested-event-item"
                            >
                                <div class="event-details">
                                    <strong>{{ event.name }}</strong>
                                    <div v-if="event.dates && event.dates.length > 0">
                                        <div v-for="(dateInfo, index) in event.dates" :key="index" class="event-date-row">
                                            <p>
                                                {{ formatDates(dateInfo.date) }}
                                            </p>
                                        </div>
                                    </div>
                                    <div v-else>
                                        <p>No dates available</p>
                                    </div>
                                </div>
                                <button 
                                    class="remove-event-btn" 
                                    @click="removeInterestedEvent(event.id)"
                                >
                                    Remove
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

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

                <!-- Error Popup Modal -->
                <div v-if="showErrorPopup" class="modal-overlay" @click.self="closeErrorPopup">
                    <div class="modal-content error-popup">
                        <span class="close-button" @click="closeErrorPopup">&times;</span>
                        <div class="error-content">
                            <i class="fas fa-exclamation-circle error-icon"></i>
                            <h3>Transfer Validation Failed</h3>
                            <p>{{ errorMessage }}</p>
                            <button @click="closeErrorPopup" class="confirm-button">OK</button>
                        </div>
                    </div>
                </div>

                <!-- Transfer Processing Modal -->
                <div v-if="isTransferModalVisible" class="modal-overlay">
                    <div class="modal-content">
                        <p>{{ transferMessage }}</p>
                        <div v-if="isTransferInProgress" class="spinner"></div>
                        <button v-else @click="isTransferModalVisible = false">Close</button>
                    </div>
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

import { auth } from '../stores/auth';
import axios from 'axios';
import { Toast, Modal } from 'bootstrap';

export default {
    name: 'profile',
    components: {
        NavBar, Toasts
    },
    data() {
        return {
            isModalOpen: false,
            selectedNotification: null,
            unreadCount: 1,
            notifications: [{ id: 1, message: "You have a new message!jgahgjhjrhtuihbersuibyuithythyivuhtrbytruibghygyg" },
            { id: 2, message: "Your order has been shippedlkrjybijtryimjbinjhyifjhoijbtyuoguihugmofb!" }],
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
            ticketStatus: "",
            orderList: [],
            eventList: [],
            ticketList: [],
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL,
            openMenus: [],
            loadingMsg: true,
            pendingTransferTickets: [],
            interestedEvents: [],
            showInterestedEventsModal: false,
            showErrorPopup: false,
            errorMessage: '',
            pollingInterval: null,
            isResaleModalVisible: false,
            resaleMessage: "Your ticket is being listed for resale... Please do not exit or refresh the page.",
            isResaleInProgress: true,
            isTransferModalVisible: false,
            transferMessage: "Your ticket transfer is being processed... Please do not exit or refresh the page.",
            isTransferInProgress: true,
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
        },
    },
    mounted() {

        const userData = auth.getUser();

        if (!userData || (!userData._id && !userData.id)) {
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

        this.fetchPendingTransfers();
        this.fetchInterestedEvents();
    this.startTicketStatusPolling();
    },

watch: {
    user(newUser) {
        if (newUser) {
            this.fetchInterestedEvents();
        }
    }
},

    methods: {
        hasRefundedTickets(order) {
            return order.hasRefundedTickets || 
            (order.refundedTicketIds && order.refundedTicketIds.length > 0);
        },
        
        getRefundedTicketsCount(order) {
            if (order.refundedTicketsCount !== undefined) {
                return order.refundedTicketsCount;
            }
            
            if (!order.refundedTicketIds) {
                return 0;
            }
            
            return order.refundedTicketIds.length;
        },
        
        toggleExpand(order) {
            order.isExpanded = !order.isExpanded;
        },

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
                
                await this.fetchOrderDetails();
            } catch (error) {
                console.error('Error fetching orders:', error);
            }
        },

        processOrders(rawOrders) {
            console.log("Processing Orders", rawOrders);
            this.orderList = rawOrders.map(order => {
                
                let allTicketIds = [];
                if (order.tickets && Array.isArray(order.tickets)) {
                order.tickets.forEach(category => {
                    if (category.ticketIds && Array.isArray(category.ticketIds)) {
                    allTicketIds = [...allTicketIds, ...category.ticketIds];
                    }
                });
                }
                
                let allRefundedTicketIds = [];
                if (order.refunded_ticket_ids && Array.isArray(order.refunded_ticket_ids)) {
                order.refunded_ticket_ids.forEach(category => {
                    if (category.ticketIds && Array.isArray(category.ticketIds)) {
                    allRefundedTicketIds = [...allRefundedTicketIds, ...category.ticketIds];
                    }
                });
                }
                
                return {
                OrderId: order.orderId,
                TicketQuantity: allTicketIds.length + allRefundedTicketIds.length,
                TotalCost: order.totalAmount,
                Status: order.status,
                ticketIds: allTicketIds,
                refundedTicketIds: allRefundedTicketIds,
                hasRefundedTickets: allRefundedTicketIds.length > 0,
                refundedTicketsCount: allRefundedTicketIds.length,
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
            const eventResponse = await axios.get(`/api/events/events/${order.eventId}`);

            // Process event data
            if (eventResponse.data && eventResponse.data.Event && eventResponse.data.Event.length > 0) {
                // Match the correct eventDate object using eventDateId
                const matchingEventDate = eventResponse.data.Event.find(eventItem => {
                    return eventItem.EventDateId === order.eventDateId;
                });

                if (matchingEventDate) {
                    order.EventName = matchingEventDate.Name;
                    order.Venue = matchingEventDate.Venue;
                    order.EventDate = matchingEventDate.Date;
                } else {
                    order.EventName = 'Event Information Unavailable';
                    order.Venue = 'Venue Information Unavailable';
                }
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
                    `${this.apiGatewayUrl}/events/dates/categories/${ticket.catId}`,
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

            this.showToast('orderLoadDone')

            this.loadingMsg = false;
        } catch (error) {
            console.error('Error fetching order details:', error);
        }
        },

        formatDates(dates) {
            if (!dates) return '';
            return new Date(dates).toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        },

        formatTime(timeString) {
            if (!timeString) return '';
            
            // Handle ISO time string format (HH:MM:SS)
            const timeParts = timeString.split(':');
            if (timeParts.length >= 2) {
                let hours = parseInt(timeParts[0]);
                const minutes = timeParts[1];
                const ampm = hours >= 12 ? 'PM' : 'AM';
                
                // Convert to 12-hour format
                hours = hours % 12;
                hours = hours ? hours : 12; // the hour '0' should be '12'
                
                return `${hours}:${minutes} ${ampm}`;
            }
            
            return timeString; // Return as-is if parsing fails
        },
        
        truncateText(text, maxLength) {
            if (!text) return '';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
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
                let userId = this.user?._id || this.user?.id || auth.getUser()?._id; // Fallback check

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

                    this.showToast('updateMobile')

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
                let userId = this.user?._id|| this.user?.id || auth.getUser()?._id; // Double-check user ID

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
        confirmResale() {
            if (this.isAgreed && this.selectedTicket) {
                const ticketId = this.selectedTicket.ticketId;
                const catId = this.selectedTicket.catId;

                // Find the order that contains this ticket
                const orderWithTicket = this.orderList.find(order => 
                    order.tickets.some(ticket => ticket.ticketId === ticketId)
                );
                
                let eventId = null;
                if (orderWithTicket) {
                    eventId = orderWithTicket.eventId;
                }
                
                console.log("Confirming resale with params:", { ticketId, catId, eventId });

                this.resaleMessage = "Your ticket is being listed for resale... Please do not exit or refresh the page.";
                this.isResaleModalVisible = true;
                this.isResaleInProgress = true;

                // Call resell API
                this.resellTicket(ticketId, catId, eventId);
                
                // Close the popup and disable the menu
                this.closePopup();

                
                
            } else {
                alert("Please agree with the Terms and Conditions");
                console.log('Agreement not checked or no ticket selected');
            }
        },
        handleOption(action, ticket) {
            console.log('Handle option called:', action, ticket);
            
            // Make sure we store the full ticket object with all necessary properties
            this.selectedTicket = ticket;
            
            if (action === 'resale') {
                this.showResalePopup = true;
                console.log('Resell Ticket clicked, selected ticket:', this.selectedTicket);
            } else if (action === 'transfer') {
                console.log("Transfer Ticket clicked, selected ticket:", this.selectedTicket);
                this.showTransferPopup = true;
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
                this.validateTicket();
            } else {
                alert('Please fill in all the details');
            }
        },
        async validateTicket() {
            try {
                const validateData = {
                    recipientEmail: this.email,
                    senderEmail: this.user.email,
                };
                const response = await axios.post(
                    `${this.apiGatewayUrl}/validateTransfer/${this.selectedTicket.ticketId}`, 
                    validateData
                );
                
                console.log("Validate Response:", response.data);
                
                if (response.data.can_transfer) {
                    this.closePopup();
                    window.location.reload();
                    this.showToast('transferTicket')
                    
                } else {
                    this.showToast('transferTicketError')

                    // Show error popup instead of alert
                    this.errorMessage = response.data.message;
                    this.showErrorPopup = true;
                    this.closePopup(); // Close the transfer popup
                }
            } catch (error) {
                
                this.showToast('transferTicketError')
                // Handle validation errors with popup
                this.errorMessage = error.response?.data?.message || "An error occurred during validation";
                this.showErrorPopup = true;
                this.closePopup(); // Close the transfer popup
                console.error("Validation Error:", error.response?.data || error.message);
            }
        },
        confirmTransfer() {
            if (this.email && this.isAgreed && this.selectedTicket) {
                this.validateTicket();
            } else {
                alert('Please fill in all the details and agree to the terms');
            }
        },
        async resellTicket(ticketId, catId, eventId) {
            try {
                // Check if we have all required parameters
                if (!ticketId || !catId) {
                    console.error("Missing required parameters for resell", { ticketId, catId });
                    return;
                }
                
                // Extract eventId from the current order if not provided
                let eventIdToUse = eventId;
                if (!eventIdToUse) {
                    // Find the order containing this ticket
                    const orderWithTicket = this.orderList.find(order => 
                        order.tickets.some(ticket => ticket.ticketId === ticketId)
                    );
                    
                    if (orderWithTicket) {
                        eventIdToUse = orderWithTicket.eventId;
                    } else {
                        console.error("Could not find order with ticket:", ticketId);
                        return;
                    }
                }
                
                // Prepare data for API call
                const resaleData = {
                    ticket_id: ticketId,
                    cat_id: catId,
                    eventId: eventIdToUse
                };

                // Make sure we're using the correct URL (from environment or API gateway)
                const resaleUrl = `${this.apiGatewayUrl}/resell-ticket`;
                console.log("Sending resale request to:", resaleUrl, resaleData);

                const response = await axios.post(resaleUrl, resaleData);

                console.log("Resale Response:", response.data);

                this.resaleMessage = "Resale listed successfully! Your ticket is now being resold.";
                this.isResaleInProgress = false;
                this.isResaleModalVisible = false;
                
                // Refresh orders instead of full page reload
                await this.fetchOrders();
                
                this.showToast('resaleTicket');
                return response.data;
            } catch (error) {
                this.showToast('resaleTicketError');

                this.resaleMessage = "Resale failed. Please try again later.";
                this.isResaleInProgress = false;
                this.isResaleModalVisible = false;
                console.error("Resale Error:", error.response?.data || error.message);
                throw error;
            }
        },
        showExpandedNotification(ticket) {
            console.log('Opening notification for ticket:', ticket); // Debug log
            this.selectedNotification = ticket;
            this.isModalOpen = true;
        },
        
        closeModal() {
            this.isModalOpen = false;
            this.selectedNotification = null;
        },

        async fetchPendingTransfers() {
            try {
                const response = await axios.get(
                    `${this.apiGatewayUrl}/tickets/pending/${this.user.email}`
                );
                
                // Get pending transfers
                this.pendingTransferTickets = response.data;

                // Fetch owner (sender) email for each ticket
                for (let ticket of this.pendingTransferTickets) {
                    try {
                        // Assuming you have an endpoint to get user details by ID
                        const userResponse = await axios.get(`${this.apiGatewayUrl}/user/${ticket.owner_id}`);
                        ticket.owner_email = userResponse.data.email;
                    } catch (error) {
                        console.error(`Error fetching owner email for ticket ${ticket._id}:`, error);
                        ticket.owner_email = 'Unknown sender';
                    }
                }

                console.log("Pending transfers with owner emails:", this.pendingTransferTickets);
            } catch (error) {
                console.error("Error fetching pending transfers:", error);
            }
        },

        async handleTransferResponse(accepted) {
            try {
                if (!this.selectedNotification) {
                    console.error('No notification selected');
                    return;
                }

                // Store necessary data before closing modal
                const notificationData = {
                    _id: this.selectedNotification._id,
                    owner_id: this.selectedNotification.owner_id,
                    owner_email: this.selectedNotification.owner_email
                };

                // For rejections, we want a simpler flow
                if (!accepted) {
                    // Close modal first
                    this.closeModal();
                    
                    // Make the API call
                    await axios.post(
                        `${this.apiGatewayUrl}/transfer/${notificationData._id}`,
                        {
                            accepted: false,
                            recipient_email: this.user.email,
                            sender_id: notificationData.owner_id,
                            sender_email: notificationData.owner_email
                        }
                    );

                    // Remove from pending transfers list
                    this.pendingTransferTickets = this.pendingTransferTickets.filter(
                        ticket => ticket._id !== notificationData._id
                    );
                    
                    return;
                }

                // For acceptances, show the loading modal
                this.isTransferModalVisible = true;
                this.isTransferInProgress = true;
                this.transferMessage = "Your ticket transfer is being processed... Please do not exit or refresh the page.";

                // Close the confirmation modal
                this.closeModal();

                console.log('Processing transfer for ticket:', notificationData);

                const transferData = {
                    accepted: true,
                    recipient_email: this.user.email,
                    sender_id: notificationData.owner_id,
                    sender_email: notificationData.owner_email
                };

                const response = await axios.post(
                    `${this.apiGatewayUrl}/transfer/${notificationData._id}`,
                    transferData
                );

                console.log('Transfer response:', response.data);
            
                if (response.data.success) {
                    // Remove the "ON HOLD" status for this ticket
                    const updatedStatuses = { ...this.ticketStatuses };
                    delete updatedStatuses[notificationData._id];
                    this.ticketStatuses = updatedStatuses;
                    localStorage.setItem("ticketStatuses", JSON.stringify(updatedStatuses));

                    // Remove the notification from the list
                    this.pendingTransferTickets = this.pendingTransferTickets.filter(
                        ticket => ticket._id !== notificationData._id
                    );

                    // Update the transfer message
                    this.transferMessage = "Transfer completed successfully! The ticket is now in your orders.";
                    this.isTransferInProgress = false;

                    // Fetch updated orders
                    await this.fetchOrders();

                    // Hide the modal after a short delay
                    setTimeout(() => {
                        this.isTransferModalVisible = false;
                    }, 2000);
                } else {
                    this.isTransferModalVisible = false;
                    this.errorMessage = "Failed to process transfer response. Please try again.";
                    this.showErrorPopup = true;
                }
            } catch (error) {
                console.error("Error processing transfer response:", error);
                this.isTransferModalVisible = false;
                this.errorMessage = error.response?.data?.message || "An error occurred while processing your response. Please try again.";
                this.showErrorPopup = true;
            }
        },

        async fetchInterestedEvents() {
        try {
            const userId = this.user?._id || this.user?.id;
            if (!userId) {
                console.error('No user ID available');
                return;
            }

            const response = await axios.get(
                `${this.apiGatewayUrl}/user/${userId}/interested-events`
            );

            // Fetch detailed event information for each interested event
            const eventDetailsPromises = response.data.interested_events.map(async (eventId) => {
                try {
                    const eventResponse = await axios.get(
                        `${this.apiGatewayUrl}/events/${eventId}`
                    );

                    // Process the response data according to the actual API structure
                    if (eventResponse.data && eventResponse.data.Event && eventResponse.data.Event.length > 0) {
                        // The API actually returns multiple date objects in the Event array
                        // Each with the same event info but different dates
                        const eventItems = eventResponse.data.Event;
                        
                        // Extract event info from the first item (common info)
                        const firstEventData = eventItems[0];
                        
                        // Extract all dates from all returned event objects
                        const allDates = eventItems.map(event => ({
                            date: event.Date,
                            startTime: event.StartTime,
                            endTime: event.EndTime,
                            eventDateId: event.EventDateId
                        }));
                        
                        return {
                            id: eventId,
                            name: firstEventData.Name,
                            dates: allDates,
                            venue: firstEventData.Venue,
                            description: firstEventData.Description
                        };
                }
            } catch (error) {
                    console.error(`Error fetching event ${eventId} details:`, error);
                    return null;
                }
            });

            // Wait for all event details to be fetched
            const detailedEvents = await Promise.all(eventDetailsPromises);
            
            // Filter out any null results
            this.interestedEvents = detailedEvents.filter(event => event !== null);
        } catch (error) {
            console.error('Error fetching interested events:', error);
        }
        },

        async removeInterestedEvent(eventId) {
            try {
                const userId = this.user?._id || this.user?.id;
                if (!userId) {
                    console.error('No user ID available');
                    return;
                }

                const response = await axios.delete(
                    `${this.apiGatewayUrl}/user/${userId}/interested-events/${eventId}`
                );

                if (response.status === 200) {
                    // Remove the event from local state
                    this.interestedEvents = this.interestedEvents.filter(
                        event => event.id !== eventId
                    );

                    // If no more interested events, close the modal
                    if (this.interestedEvents.length === 0) {
                        this.showInterestedEventsModal = false;
                    }
                }
            } catch (error) {
                console.error('Error removing interested event:', error);
            }
        },

        closeErrorPopup() {
            this.showErrorPopup = false;
            this.errorMessage = "";
        },

        // Modify the startTicketStatusPolling method to only show "TICKET IS BEING TRANSFERRED" 
        // for tickets that the user is sending, not receiving
        async startTicketStatusPolling() {
            // Remove the polling interval since we don't want automatic refreshes
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
        },

        stopTicketStatusPolling() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
        },
        showToast(toastId){
            // show toast 
            const toastElement = document.getElementById(toastId);
            const toastInstance = Toast.getOrCreateInstance(toastElement);
            toastInstance.show();
        },

    },
    created () {
        const storedStatuses = localStorage.getItem("ticketStatuses");
        if (storedStatuses) {
            this.ticketStatuses = JSON.parse(storedStatuses);
        }
    },
    beforeDestroy() {
        this.stopTicketStatusPolling();
    },
    beforeRouteLeave(to, from, next) {
        this.stopTicketStatusPolling();
        next(); 
    }
}
</script>

<style scoped>

.disabled {
    pointer-events: none; 
    opacity: 0.5; 
    cursor: not-allowed;
}

.resold-ticket-info {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 0;
  font-size: 15px;
}
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
    gap: 16px;
    width: 100%;
    margin: auto;
    justify-items: start;
}

.qr-image {
    margin-top: 20px;
    display: block;
    margin-left: auto;
    margin-right: auto;
    max-width: 100%;
    height: auto;
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
    max-width: 300px;
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
    width: 90%;
    position: relative;
    max-width: 800px;
}

.modal-content>h3 {
    margin-top: 10px;
}

.confirm-button {
    background: #2A68E1;
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

/* Individual Notification Item */
.notification-item {
    background-color: #f9f9f9;
    padding: 10px; 
    border-radius: 8px; 
    font-size: 14px;
    color: #333;
    margin-bottom: 10px; 
}

.notification-item:hover {
    background-color: #e6e6e6; 
}

/* Notifications Label */
.notifications-label {
    font-size: 1em;
    color: #808080;
    margin-bottom: 10px;
    display: block; 
}

/* Notification Modal */
.notification-modal {
    position: fixed; 
    top: 50%; 
    left: 50%; 
    transform: translate(-50%, -50%); 
    z-index: 3; 
    background-color: rgba(0, 0, 0, 0.5); 
    width: 100vw; 
    height: 100vh; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
}

/* Modal Content Box */
.modal-content {
    background-color: white; 
    padding: 20px; 
    border-radius: 8px; 
    width: 80%; 
    max-width: 400px; 
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3); 
    overflow-wrap: break-word; 
    word-wrap: break-word; 
    overflow-y: auto; 
    max-height: 80vh; 
}

.button-group {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin-top: 30px;
}

.button-group button {
    min-width: 120px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.button-group button:hover {
    opacity: 0.9;
}

/* Interested Events Styling */
.interested-events-section {
    margin-top: 10px;
}

.interested-events-label {
    font-size: 1em;
    color: #808080;
    margin-bottom: 10px;
    display: block;
}

.interested-event {
    background-color: #f0f4ff;
    cursor: pointer;
}

.interested-event:hover {
    background-color: #e6edf8;
}

.no-interested-events {
    color: #808080;
    font-size: 0.9em;
}

/* Interested Events Modal Styles */
.interested-events-list {
    max-height: 300px;
    overflow-y: auto;
}

.interested-event-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-bottom: 1px solid #eee;
}

.remove-event-btn {
    background-color: #ff4d4d;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.remove-event-btn:hover {
    background-color: #ff3333;
}

.no-events {
    text-align: center;
    color: #888;
    padding: 20px;
}

.remove-event-btn {
    margin-left: 20px;
    min-width: 100px;
    white-space: nowrap;
    font-size: 14px;
    align-self: flex-start;
    margin-top: 15px;
    padding: 8px 16px;
}

.event-date-row {
  margin-bottom: 5px;
  padding-top: 0;
  padding-bottom: 0;
}

.event-date-row p {
  margin: 5px 0;
}

.error-popup {
    max-width: 400px !important;
    padding: 30px !important;
}

.error-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.error-icon {
    color: #ff4d4d;
    font-size: 48px;
    margin-bottom: 20px;
}

.error-content h3 {
    color: #333;
    margin-bottom: 15px;
}

.error-content p {
    color: #666;
    margin-bottom: 20px;
}

.error-content .confirm-button {
    background-color: #2A68E1;  
    width: auto;
    min-width: 100px;
    padding: 10px 20px;
}

.error-content .confirm-button:hover {
    background-color: #1d4ba8;  
}

button {
    font-size: 16px;
}

/* Update the accept and reject button styles */
.accept-button {
    background-color: #2A68E1;
    color: white;
    border: none;
    padding: 10px 40px;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    min-width: 120px;
}

.reject-button {
    background-color: white;
    color: #2A68E1;
    border: 2px solid #2A68E1;
    padding: 10px 40px;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    min-width: 120px;
}

.button-group {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin-top: 30px;
}

.accept-button:hover {
    background-color: #1d4ba8;
}

.reject-button:hover {
    background-color: #f8f9fa;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
}
.modal-content {
    background: white;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
}
.spinner {
    width: 30px;
    height: 30px;
    border: 4px solid #ccc;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: auto;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

</style>