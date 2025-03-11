<template>
  <NavBar/>
</template>

<script>

import NavBar from "../components/nav-bar.vue";

export default {
  name: 'home',
  components: {
    NavBar
  },
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
</style>