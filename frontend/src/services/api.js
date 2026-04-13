const API_BASE_URL = "/api";

class ApiService {
  async _handleResponse(response) {
    if (!response.ok) {
      try {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        );
      } catch (e) {
        if (e instanceof SyntaxError) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        throw e;
      }
    }
    return await response.json();
  }

  async getGames() {
    const response = await fetch(`${API_BASE_URL}/games/`);
    if (!response.ok) {
      throw new Error(`Failed to fetch games: ${response.statusText}`);
    }
    return await response.json();
  }

  async createGame(playerName) {
    const response = await fetch(`${API_BASE_URL}/games/?player_name=${playerName}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    return this._handleResponse(response);
  }

  async joinGame(gameId, playerName) {
    const response = await fetch(
      `${API_BASE_URL}/games/${gameId}/join/?player_name=${playerName}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    return this._handleResponse(response);
  }

  // WebSocket connection
  connectToGame(gameId, playerName) {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/game/${gameId}?player_name=${playerName}`;
    return new WebSocket(wsUrl);
  }
}

export default new ApiService();
