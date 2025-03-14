<template>
    <NavBar/>

    <!-- Banner -->
    <div class="container-fluid bannerImg banner mx-0 p-5">
      <div class="row">
        <div class="col-8">
          <div>
            <p class="bannerText">Our door is always open for you</p>
            <p style="color:white;">Reach out and we are more than happy to help you!</p>
          </div>
        </div>
        <div class="col-4"></div>
      </div>
    </div>


    <div class="container my-5">
        <div class="row text-center">
            <div class="col bg-body-secondary p-5 m-2">
                <i class="bi bi-telephone-fill" style="font-size:45px; color:var(--main-blue);color:var(--main-blue);"></i>
                <h4 style=" text-transform: uppercase;">Call Us</h4>
                <p>Contact us at 9853 5235</p>
                <p style="margin-top: -10px;">Opening Hours: 9am-9pm</p>
                <p style="margin-top: -10px;">Excluding weekends and Public Holidays</p>
            </div>
            <div class="col bg-body-secondary p-5 m-2">
                <i class="bi bi-envelope-at-fill" style="font-size:50px;color:var(--main-blue);"></i>
                <h4 style="text-transform: uppercase;">Email Us</h4>
                <p>Email your queries at </p>
                <p style="margin-top: -10px;"><a href="mailto:queries@eventiva.com">queries@eventiva.com</a></p>
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
    url("../assets/contact_us.png");
  background-repeat: no-repeat;
  background-size: cover;
  height: 60vh;
  width: 100%;
}

</style>