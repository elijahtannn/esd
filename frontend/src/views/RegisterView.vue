<template>

    <NavBar/>

    <!-- CDN -->
    <head>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    </head>

    <div class="background-container">
        <img src="../assets/images/Login_Background.png" class="background-img">

        <!-- Register Block -->
        <div class="login-box p-5">
            <h3 class="text-center" style="font-size: 24px;">REGISTER</h3>
            <!-- Input field - Name -->
            <div class="row">
                <label for="name" class="input-label">
                    <i class="fa-solid fa-user icon"></i>
                    Name
                </label>
                <div class="input-container">
                    <input type="text" id="name" class="input-field" required  placeholder="Enter your name"/>
                </div>
            </div>
            <!-- Input field - Email -->
            <div class="row">
                <label for="email" class="input-label">
                    <i class="fa-solid fa-envelope icon"></i>
                    Email
                </label>
                <div class="input-container">
                    <input type="email" id="email" class="input-field" required  placeholder="Enter your email"/>
                </div>
            </div>
            <!-- Input field - Mobile -->
            <div class="row">
                <label for="mobile" class="input-label">
                    <i class="fa-solid fa-phone icon"></i>
                    Mobile
                </label>
                <div class="input-container">
                    <input type="number" id="mobile" class="input-field" required  placeholder="Enter your mobile number"/>
                </div>
            </div>
            <!-- Input field - Password -->
            <div class="row">
                <label for="password" class="input-label">
                    <i class="fa-solid fa-user icon"></i>
                    Password
                </label>
                <div class="input-container">
                    <input type="password" id="password" class="input-field" required  placeholder="Enter your password"/>
                </div>
            </div>

            <!-- Submit Button -->
            <div class='row'>
                <button class="login-btn">REGISTER</button>
            </div>


            <!-- Login with google -->
            <div class='row mt-3'>
                <button class="btn">
                    <img src='../assets/images/google icon.png' width="15%"> Sign in with Google
                </button>
            </div>

            <!-- insert line here -->
            <hr>


            <!-- Dont Have an existing account? -->
            <div class="row">
                <span class="small-text">Are you an existing user?</span>
                <span class="small-text">Login <router-link to="/login">here</router-link></span>
            </div>
            
        </div>
    </div>    

</template>

<script>

import NavBar from "../components/nav-bar.vue";

export default {
    name: 'register',
    components: {
        NavBar
    },
    data() {
        return {

        }
    },
    methods: {

    },
    mounted() {

    }
}
</script>

<style scoped>

.background-container {
    position: relative;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
}

.background-img {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: cover; 
    z-index: -1; 
}

.login-box {
    position: absolute;
    top: 50%;
    right: 10%;
    transform: translateY(-50%);
    width: 30vw;
    padding: 20px;
    background: white;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.login-box > h3 {
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

.login-btn {
    width: 100%;
    padding: 8px;
    background-color: #2A68E1;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 14px;
    cursor: pointer;
}

.login-btn:hover {
    background-color: #1e4da8;
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
        width:16px;
        height: 16px;
    }

    .btn:hover {
        background-color: #e0e0e0;
    }
</style>