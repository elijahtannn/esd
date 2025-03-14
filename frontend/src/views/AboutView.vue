<template>
    <NavBar/>

    <!-- Banner -->
    <div class="container-fluid bannerImg banner mx-0 p-5">
      <div class="row">
        <div class="col-8">
          <div>
            <p class="bannerText">find out more about Eventiva</p>
            <p style="color:white;">Let us share more about ourselves!</p>
          </div>
        </div>
        <div class="col-4"></div>
      </div>
    </div>

    <!-- Stats to showcase -->
    <div class="container text-center p-5">
      <div class="row">
        <div class="col">
          <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">82</h1>
          <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Events Completed</p>
        </div>
        <div class="col">
          <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">5,898</h1>
          <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Tickets Sold</p>
        </div>
        <div class="col">
          <h1 style="font-weight: 700; font-size: 56px; color:var(--main-blue)">209</h1>
          <p style="text-transform: uppercase;  color:var(--main-blue); margin-top:-10px;">Artists Involved</p>
        </div>
      </div>
    </div>


    <!-- Who are we? -->
    <div class="container-fluid">
        <div class="row p-5" style="background-color: var(--light-blue);">
            <div class="col">
                <img src="../assets/about_us.png" width="100%" height="100%" style="object-fit: cover;">
            </div>
            <div class="col p-5">
                <h3 style="color:var(--main-blue); text-transform: uppercase;">Who are we?</h3>
                <p style="line-height: 30px;">At Eventiva, we are passionate about revolutionizing the way you experience live events. We believe that attending concerts, sports games, theater performances, and festivals should be a joyous experience from start to finish, which is why we've created a seamless and user-friendly platform for fans to easily browse, purchase, resell, and transfer tickets. Whether you're a music enthusiast, a sports aficionado, or someone who loves attending festivals, we aim to make every ticket-buying experience hassle-free and enjoyable. Our platform is designed to simplify the process of finding and securing tickets, ensuring that you can focus on what matters most—creating unforgettable memories at your favorite events.</p>
            </div>
        </div>
    </div>

    <!-- Vision and mission -->
    <div class="container-fluid p-5 mb-4">
        <div class="row p-5">
            <div class="col me-3 border-end">
                <h3 style="color:var(--main-blue); text-transform: uppercase;">vision</h3>
                <p style="margin-top: 10px;line-height: 30px;">To become the leading platform for seamless ticketing experiences, empowering fans worldwide to effortlessly connect with their favorite live events, while fostering a vibrant community that celebrates the joy of shared entertainment.</p>
            </div>
            <div class="col ms-3">
                <h3 style="color:var(--main-blue); text-transform: uppercase;">mission</h3>
                <p style="margin-top: 10px;line-height: 30px;">To provide a user-friendly, secure, and innovative platform where fans can easily browse, purchase, resell, and transfer tickets for concerts and events, ensuring a hassle-free experience that enhances the overall enjoyment of live entertainment.</p>
            </div>
        </div>
    </div>

    <!-- Key Features -->
    <div class="container-fluid text-center">
        <div class="row g-5 p-5" style="background-color: var(--light-blue);">
            <h3 style="color:var(--main-blue); text-transform: uppercase;">Explore our key features!</h3>
            <div class="col m-2 p-5">
                <i class="bi bi-bag-fill" style="font-size: 50px;"></i>
                <h5>Easy Browsing and Purchase</h5>
                <p style="line-height: 30px;">Our intuitive interface allows you to quickly find and purchase tickets for your favorite events. Whether you're looking for a specific concert, a sports match, or a festival, our platform makes it easy to discover and secure tickets on the fly.</p>
            </div>
            <div class="col m-2 p-5">
                <i class="bi bi-arrow-left-right" style="font-size: 50px;"></i>
                <h5>Resell and Transfer Tickets</h5>
                <p style="line-height: 30px;">We understand that plans can change, which is why we offer a straightforward process for reselling and transferring tickets. This includes support for tickets that are typically non-refundable, giving you more control over your ticket purchases. Note that this is subjective and differs on a case by case basis.</p>
            </div>
            <div class="col m-2 p-5">
                <i class="bi bi-window-fullscreen" style="font-size: 50px;"></i>
                <h5>User-Friendly Interface</h5>
                <p style="line-height: 30px;">Our website is designed with the user in mind. We strive to provide a clean, intuitive, and responsive interface that works seamlessly across all devices, ensuring that you can manage your tickets anywhere, anytime.</p>
            </div>
            <div class="col m-2 p-5">
                <i class="bi bi-cash-stack" style="font-size: 50px;"></i>
                <h5>Secure Transactions</h5>
                <p style="line-height: 30px;">We prioritize the security and integrity of every transaction. Our platform uses robust security measures to protect your personal and financial information, giving you confidence in every purchase.</p>
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
}
</script>

<style scoped>
.bannerImg {
  background-image: linear-gradient(to right, rgba(0, 0, 0, 0.9), rgba(255, 255, 255, 0.1)),
    url("../assets/about_us.png");
  background-repeat: no-repeat;
  background-size: cover;
  height: 60vh;
  width: 100%;
}
</style>