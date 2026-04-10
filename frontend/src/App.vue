<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
};
</script>

<style>
@font-face {
  font-family: "Silkscreen";
  src: url("fonts/Silkscreen-Regular.ttf");
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}

html,
body {
  background-color: #000000;
  color: #00ff00;
  font-family: "Courier New", monospace;
  overflow: hidden;
}

#app {
  display: flex;
  flex-direction: column;
}
</style>
