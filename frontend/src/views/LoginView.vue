<template>

<head>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
</head>


<!-- Your HTML Content Here -->
    <div class="background-container">
        <!-- Background Image -->
        <img src="../assets/images/Login_Background.png" class="background-img">

        <!-- White Box (Login Form) -->
        <div class="login-box">
            <h3 class="text-center" style="font-size: 24px;">LOGIN</h3>
            <!-- Input field - Email -->
            <div class="row">
                <label for="email" class="input-label">
                    <i class="fa-solid fa-envelope icon"></i>
                    Email
                </label>
                <div class="input-container">
                    <input type="email" id="email" class="input-field" required />
                </div>
            </div>
            <!-- Input field - Password -->
            <div class="row">
                <label for="password" class="input-label">
                    <i class="fa-solid fa-user icon"></i>
                    Password
                </label>
                <div class="input-container">
                    <input type="password" id="password" class="input-field" required />
                    <!-- Forget Password -->
                    <div class="forget-password-container">
                        <div class="text-end">
                            <a href="#" class="forgetPW">Forget Password?</a>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Submit Button -->
            <div class='row'>
                <button class="login-btn">LOGIN</button>
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
                <span class="small-text">Don't have an existing account?</span>
                <span class="small-text">Sign Up <a href="signup.html">here</a></span>
            </div>
            
        </div>
    </div>
</template>

<script>
export default {
    name: 'login',
    data() {
        return {
            // Your component data here
        }
    },
    methods: {
        // Your component methods here
    },
    mounted() {
        // Lifecycle hook: mounted
    }
}
</script>

<style scoped>
/* Your CSS styles here */
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
    width: 320px;
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
    width: 100%; /* Match the login button width */
    padding: 8px; /* Same padding */
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