<template>

    <NavBar />

    <head>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    </head>


    <div class="background-container">
        <!-- Background Image -->
        <img src="../assets/images/Login_Background.png" class="background-img">

        <!-- White Box (Login Form) -->
        <div class="login-box p-5">
            <h3 class="text-center" style="font-size: 24px;">LOGIN</h3>
            <!-- Login with google -->
            <div class='row mt-3'>
                <button class="btn" @click="handleGoogleLogin">
                    <img src='../assets/images/google icon.png' width="15%"> Sign in with Google
                </button>
            </div>

            <!-- insert line here -->
        </div>
    </div>



</template>

<script>

import NavBar from "../components/nav-bar.vue";

export default {
    name: 'login',
    components: {
        NavBar
    },
    data() {
        return {
            apiGatewayUrl: import.meta.env.VITE_API_GATEWAY_URL
        }
    },
    methods: {
        async handleGoogleLogin() {
            try {
                window.location.href = `${this.apiGatewayUrl}/login`;
            } catch (error) {
                console.error('Error initiating Google login:', error);
            }
        }
    },
    mounted() {
        // Handle the redirect from Google login
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id');
        const email = urlParams.get('email');

        if (userId && email) {
            // Store user info in localStorage
            localStorage.setItem('user_id', userId);
            localStorage.setItem('user_email', email);
            
            // Redirect to home page and clean up URL parameters
            this.$router.push('/home');
        }
    }
}
</script>

<style scoped>
.background-container {
    position: relative;
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.background-img {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: -1;
}

.login-box {
    width: 30vw;
    padding: 20px;
    background: white;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.login-box>h3 {
    color: #2A68E1;
    font-size: 20px;
}

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


.forgetPW {
    color: gray;
    text-decoration: none;
    font-size: 12px;
}

.forgetPW:hover {
    color: #2A68E1;
}


.small-text {
    font-size: 12px;
}

.btn {
    width: 100%;
    padding: 8px;
    font-size: 14px;
    border: 1px solid #dcdcdc;
    font-size: 12px;
    padding: 8px;
    cursor: pointer;
}

.btn img {
    width: 16px;
    height: 16px;
}

.btn:hover {
    background-color: #e0e0e0;
}
</style>