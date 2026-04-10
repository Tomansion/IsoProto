from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from controllers.games import router as games_router
from ws.game_ws import router as game_ws_router

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the games router
app.include_router(games_router, prefix="/api/games", tags=["games"])

# Include the game WebSocket router
app.include_router(game_ws_router, tags=["game"])


@app.get("/")
async def root():
    # Serve index.html if static folder exists (Docker), otherwise return JSON
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_path):
        return FileResponse(static_path)
    return {"ok": True}


# Catch-all route for SPA - must come after API routes
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Serve static files or index.html for SPA routing"""
    static_base = os.path.join(os.path.dirname(__file__), "static")
    file_path = os.path.join(static_base, full_path)

    # If the file exists, serve it
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # If it looks like a static asset (has file extension), return 404
    if "." in os.path.basename(full_path):
        return {"error": "Not found"}, 404

    # For routes without extensions, serve index.html for SPA routing
    index_path = os.path.join(static_base, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"error": "Not found"}, 404


# Mount static files if the folder exists (for Docker deployment)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
