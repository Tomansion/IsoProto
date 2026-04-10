# IsoProto

Tower Defense Isometric game.

## Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the frontend
npm run serve
```

The frontend will be available at http://localhost:5173.

### Backend

```bash
cd backend

# Optional but recommended: create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn main:app --reload
```

The backend will be available at http://localhost:8000, the API documentation will be available at http://localhost:8000/docs.

## Deployment

```bash
# Build the docker image
docker build -t starbarge .

# Run the docker container
docker run -p 8000:8000 starbarge
```

### Persistent Data with Docker Volumes

To persist the game data (maps and database) between container restarts, use Docker volumes:

```bash
# Create a named volume for persistent data
docker volume create starbarge-data

# Run the container with the volume mounted
docker run -p 8000:8000 -v starbarge-data:/app/backend/data starbarge
```

Alternatively, you can mount a local directory:

```bash
# Run the container with a local directory mount
docker run -p 8000:8000 -v $(pwd)/data:/app/backend/data starbarge
```

This ensures your map data and game files persist even after the container is stopped and removed.

## Code Quality

This project uses automated code quality checks on pull requests:

- **Black** for Python code formatting
- **Prettier** for frontend code formatting
- **CSpell** for spell checking

### Formatting Code

**Backend (Python):**

```bash
cd backend
pip install black
black .
```

**Frontend (JavaScript/Vue):**

```bash
cd frontend
npm run prettier:write
```

### Spell Checking

```bash
npm install -g cspell
cspell .
```

Add any project-specific words to `cspell.json` if needed.

## Development process

1. Assign yourself to an issue.
2. Create a branch (can be done from the issue page)
3. Make your changes and push to the branch.
4. Create a pull request and request a review from another team member.
5. Make sure all automated checks pass (code formatting, spell checking, etc.). If any checks fail, fix the issues and push the changes to the branch.
6. Once the pull request is approved, merge it into the main branch.

## FLow & Gameplay

Players can "log in" by providing a username.
Players can create a game, the name of the game is the name of the username of the player that created the game.
Players can list and join an existing game.
On game creation, a 100x100 map is generated.
Some trees are placed on the map using Perlin noise, the center of the map is cleared to make room for the base.
A home base is placed at the center of the map.
Enemies spawn at the edges of the map and try to reach the home base, if they reach it, the base takes damage, if the base's health reaches 0, the game is lost.
Players can place towers on the map, towers automatically attack enemies in range.
The game is won when a certain number of waves are defeated.