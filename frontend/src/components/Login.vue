<template>
  <div class="login-container">
    <div class="terminal-window">
      <div class="terminal-header">isoproto@system:~$</div>
      <div class="terminal-content">
        <h1>ISOPROTO v0.1</h1>
        <p class="terminal-text">> Enter username to login:</p>
        <input
          v-model="username"
          type="text"
          placeholder="username"
          @keyup.enter="handleLogin"
          class="terminal-input"
        />
        <button @click="handleLogin" class="terminal-btn">
          {{ loading ? "...logging in" : "login" }}
        </button>
        <p v-if="error" class="terminal-error">> ERROR: {{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Login",
  data() {
    return {
      username: "",
      loading: false,
      error: null,
    };
  },
  methods: {
    handleLogin() {
      if (!this.username.trim()) {
        this.error = "username required";
        return;
      }

      this.loading = true;
      this.error = null;

      localStorage.setItem("playerName", this.username);
      setTimeout(() => {
        this.$router.push("/home");
      }, 300);
    },
  },
};
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #000000;
  padding: 20px;
}

.terminal-window {
  width: 100%;
  max-width: 600px;
  background-color: #000000;
  border: 1px solid #00ff00;
  font-family: "Courier New", monospace;
  color: #00ff00;
}

.terminal-header {
  background-color: #001a00;
  border-bottom: 1px solid #00ff00;
  padding: 8px 12px;
  font-size: 12px;
  color: #00aa00;
}

.terminal-content {
  padding: 16px;
}

h1 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #00ff00;
}

.terminal-text {
  margin: 8px 0;
  font-size: 13px;
}

.terminal-input {
  width: 100%;
  margin: 12px 0;
  padding: 8px;
  background-color: #001a00;
  border: 1px solid #00ff00;
  color: #00ff00;
  font-family: "Courier New", monospace;
  font-size: 13px;
}

.terminal-input:focus {
  outline: 1px solid #00ff00;
}

.terminal-btn {
  background-color: #001a00;
  border: 1px solid #00ff00;
  color: #00ff00;
  padding: 8px 16px;
  margin-top: 12px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  cursor: pointer;
}

.terminal-btn:hover:not(:disabled) {
  background-color: #003300;
}

.terminal-btn:disabled {
  opacity: 0.7;
}

.terminal-error {
  color: #ff0000;
  margin-top: 12px;
  font-size: 12px;
}
</style>
