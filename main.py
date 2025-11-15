from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app instance
app = FastAPI()

# --- CORS (Cross-Origin Resource Sharing) ---
# This is CRITICAL to allow your React frontend
# to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Your First API Endpoint ---
# This is a "route" just like a webpage
@app.get("/")
def read_root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the CasaCore Backend! 🌱🧱"}

@app.get("/api/test")
def test_api():
    """
    A test endpoint to make sure our API is working.
    """
    return {"status": "success", "data": "Your FastAPI backend is running!"}