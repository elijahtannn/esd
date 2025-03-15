<template>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <div>
        <NavBar/>
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
                    <p><span class="label">Id:</span> <br> {{ user.id }}</p>
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
                    <div id="Upcoming" class="tabcontent active order-card">
                        <hr>
                        <div class="order-header" @click="isExpanded = !isExpanded">
                            <div>
                                <p><strong>Lady Gaga in Singapore</strong></p>
                                <p>18 May 2025, National Stadium</p>
                                <p><strong>Order Information:</strong> #4452</p>
                                <p><strong>Ticket Quantity:</strong> 4</p>
                                <p><strong>Total Cost:</strong> $300</p>
                            </div>
                            <button class="toggle-button">
                                <i :class="['fa-solid', isExpanded ? 'fa-chevron-up' : 'fa-chevron-down', 'icon']"></i>
                            </button>
                        </div>
                        <div v-if="isExpanded" class="order-details">
                            <!-- QR cards -->
                            <div class="qr-cards">
                                <div class="qr-card">
                                    <!-- Three-dot menu -->
                                    <div class="menu-container">
                                        <span class="menu-icon" @click="toggleMenu">
                                            &#x22EE; <!-- Vertical three dots -->
                                        </span>
                                        <div v-if="isMenuOpen" class="menu-dropdown">
                                            <p @click="handleOption('resale')">Resell Ticket</p>
                                            <p @click="handleOption('transfer')">Transfer Ticket</p>
                                        </div>
                                    </div>

                                    <img src="../assets/images/dummy QR code.png" class="qr-image">
                                    <p>#101</p>
                                    <p>Type: Category 1</p>
                                    <p>Price: $80</p>
                                    <p>Seat: #88</p>
                                </div>
                            </div>
                        </div>
                        <!-- Resale Confirmation Modal -->
                        <div v-if="showResalePopup" class="modal-overlay">
                            <div class="modal-content">
                                <!-- Close (X) Button -->
                                <span class="close-button" @click="closePopup">&times;</span>

                                <h3>Are you sure you want to resell your ticket?</h3>
                                <p><strong>Ticket ID:</strong> #101</p>
                                <p><strong>Type:</strong> Category 1</p>
                                <p><strong>Price:</strong> $80</p>
                                <p><strong>Seat:</strong> #88</p>
                                <hr>
                                <!-- Mandatory Checkbox for Agreement -->
                                <div class="checkbox-container">
                                    <input type="checkbox" id="agreeCheckbox" v-model="isAgreed" />
                                    <label for="agreeCheckbox">
                                        I agree that a refund will only be issued once the resale process is complete and the transaction is finalized.
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
                                <p><strong>Ticket ID:</strong> #101</p>
                                <p><strong>Type:</strong> Category 1</p>
                                <p><strong>Price:</strong> $80</p>
                                <p><strong>Seat:</strong> #88</p>
                                <hr>

                                <!-- Input Form for Recipient's Information -->
                                <div class="form-group">
                                    <label for="recipientName">Recipient's Name:</label>
                                    <input type="text" id="recipientName" v-model="recipientName" placeholder="Enter recipient's name" />
                                </div>
                                <div class="form-group">
                                    <label for="eventivaAccount">Recipient's Eventiva Account ID:</label>
                                    <input type="text" id="eventivaAccount" v-model="eventivaAccount" placeholder="Enter Eventiva Account ID" />
                                </div>
                                <div class="form-group">
                                    <label for="phoneNumber">Recipient's Phone Number:</label>
                                    <input type="text" id="phoneNumber" v-model="phoneNumber" placeholder="Enter phone number" />
                                </div>

                                <!-- Mandatory Checkbox for Agreement -->
                                <div class="checkbox-container">
                                    <input type="checkbox" id="agreeCheckbox" v-model="isAgreed" />
                                    <label for="agreeCheckbox" style="font-size: 14px;">
                                        I agree that transfer will only be completed once both parties has accepted the transfer. Once the transfer is complete, it cannot be undone or transferred back to me.                                    </label>
                                </div>
                                <button @click="confirmTransfer" class="confirm-button">CONFIRM</button>
                            </div>
                        </div>

                    </div>

                    <div id="History" class="tabcontent">
                        <hr>
                        <h3>Event History</h3>
                        <p>No past events available.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import NavBar from "../components/nav-bar.vue";
import { auth } from '../stores/auth';

export default {
    name: 'profile',
    components: {
        NavBar
    },
    data() {
        return {
            user: null,
            isExpanded: false,
            isMenuOpen: false,
            showResalePopup: false,
            isAgreed: false,
            showTransferPopup: false,
            recipientName: '',
            eventivaAccount: '',
            phoneNumber: '',
            isEditing: false,
        }
    },
    mounted() {
        const userData = auth.getUser();
        if (userData) {
            this.user = userData;
        }
    },
    methods: {
        toggleEdit() {
            this.isEditing = !this.isEditing;
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
        toggleMenu() {
            this.isMenuOpen = !this.isMenuOpen;
        },
        handleOption(action) {
            if (action === 'resale') {
                this.showResalePopup = true; // Show the resale confirmation modal
                console.log('Resell Ticket clicked')
            } else if (action === 'transfer') {
                console.log("Transfer Ticket clicked");
                this.showTransferPopup = true;
            }
            this.isMenuOpen = false; // Close menu after selection
        },
        confirmResale() {
            if (this.isAgreed) {
                // Proceed with resale
                console.log('Resale confirmed');
                
                // Close the modal after confirmation
                this.closePopup();
            } else {
                console.log('Agreement not checked');
            }
        },
        closePopup() {
            this.showResalePopup = false;
            this.showTransferPopup = false;
        },
        closeMenu() {
            this.isMenuOpen = false;
        },
        confirmTransfer() {
            if (this.recipientName && this.eventivaAccount && this.phoneNumber && this.isAgreed) {
                // Proceed with ticket transfer
                console.log('Ticket transfer confirmed');
                console.log(`Recipient: ${this.recipientName}, Account ID: ${this.eventivaAccount}, Phone: ${this.phoneNumber}`);
                // You can add your logic for transfer confirmation here

                // Close the modal after confirmation
                this.closePopup();
            } else {
                console.log('Please fill in all the details');
            }
        },
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
    color: black; /* Adjust color if needed */
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
    z-index: 2; 
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
    margin-bottom:20px ;
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
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    width: 50%;
}

.qr-image {
  display: block; /* Makes the image a block element */
  margin-left: auto; /* Centers image horizontally */
  margin-right: auto; /* Centers image horizontally */
  width: 250px; /* Adjust size for better fit */
  height: auto; /* Maintain aspect ratio */
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
    width: 300px;
}

.menu-container {
    position: absolute;
    top: 10px;
    right: 10px;
}

.menu-icon {
    font-size: 20px;
    cursor: pointer;
    margin-right:10px;
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
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    text-align: center;
    width: 500px;
    position: relative; /* Keep the close button (X) positioned */
}

.modal-content > h3 {
    margin-top: 10px;
}

.confirm-button {
    background: #2A68E1; /* Blue for confirm button */
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
    background: #d6d6d6; /* Disabled button color */
    cursor: not-allowed;
}

/* X BUTTON ON MODAL */
.close-button {
    position: absolute; 
    top: 10px; 
    right: 10px; 
    font-size: 24px; 
    cursor: pointer; 
    color: #333; 
}

.close-button:hover {
    color: #ff0000; /* Change color on hover */
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

</style>