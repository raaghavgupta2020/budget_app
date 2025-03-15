from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URL, DB_NAME
from .routes import user, entry

app = FastAPI(title="Budget App API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
# Update the startup event in app/main.py
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
        # Ping the server to confirm connection is working
        await app.mongodb_client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        
        app.mongodb = app.mongodb_client[DB_NAME]
        
        # Create indexes for better performance
        await app.mongodb["users"].create_index("username", unique=True)
        await app.mongodb["entries"].create_index([("username", 1), ("date", -1)])
    except Exception as e:
        print(f"Error connecting to MongoDB Atlas: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Include routers
app.include_router(user.router, tags=["users"], prefix="/user")
app.include_router(entry.router, tags=["entries"])

@app.get("/")
async def root():
    return {"message": "Welcome to Budget App API"}