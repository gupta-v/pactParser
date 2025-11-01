from pymongo import MongoClient
from pymongo.database import Database
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.concurrency import run_in_threadpool
import os

class DatabaseSettings(BaseSettings):
    """
    Reads the MongoDB connection string from an environment variable.
    
    We'll set MONGO_CONNECTION_STRING in our .env file locally,
    and it will be set by Docker/deployment environment later.
    
    Default value is for our local docker-compose setup.
    """
    MONGO_CONNECTION_STRING: str = "mongodb://localhost:27017"
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Initialize settings
settings = DatabaseSettings()

# Create a single, reusable client instance
# This is recommended by MongoDB docs
try:
    client = MongoClient(settings.MONGO_CONNECTION_STRING)
    # Ping the server to confirm a successful connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    # In a real app, you might want to exit if the DB connection fails
    client = None

async def get_db() -> Database:
    """
    Dependency injector function to get the database instance.
    This is now an async function.
    """
    if client is None:
        raise Exception("MongoDB client is not initialized. Check connection.")
    
    db = client["pactparser_db"]
    return db

# --- THIS IS FOR CELERY (SYNC) ---
def get_db_sync() -> Database:
    """
    A synchronous function to get the database instance.
    Used by Celery workers.
    """
    if client is None:
        raise Exception("MongoDB client is not initialized. Check connection.")
        
    db = client["pactparser_db"]
    return db
# --- END ADDITION ---

async def create_indexes():
    """
    Ensures that the critical indexes are created in MongoDB.
    """
    if client:
        try:
            db = await get_db() # Use await
            # Run the blocking I/O in a threadpool
            await run_in_threadpool(db.contracts.create_index, "contract_id", unique=True)
            await run_in_threadpool(db.contracts.create_index, "status")
            await run_in_threadpool(db.contracts.create_index, "confidence_score")
            await run_in_threadpool(db.contracts.create_index, "created_at")
            
            print("✅ MongoDB indexes ensured.")
        except Exception as e:
            print(f"⚠️ Warning: Failed to create indexes. {e}")