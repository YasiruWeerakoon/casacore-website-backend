import motor.motor_asyncio
from config import settings # Import our settings

class Database:
    """
    Manages the connection to the MongoDB database.
    """
    def __init__(self, db_url: str, db_name: str):
        print("Initializing database connection...")
        self.db_name = db_name
        try:
            # Create a Motor client (this is the correct async driver)
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                db_url,
                maxPoolSize=10,
                minPoolSize=5,
                timeoutMS=30000, 
                serverSelectionTimeoutMS=10000 
            )
            
            # This is the FIX:
            # We explicitly get our database by name, no guessing.
            self.db = self.client[self.db_name]
            
            print(f"Database client initialized. Pointing to '{self.db_name}'.")
            
        except Exception as e:
            print(f"Error initializing database client: {e}")
            self.client = None
            self.db = None

    async def get_db(self):
        """
        Returns the database instance.
        """
        if self.db is not None:
            return self.db
        else:
            print("Database connection not established.")
            return None

    async def close(self):
        """
        Closes the database connection.
        """
        if self.client:
            self.client.close()
            print("Database connection closed.")
            
    async def ping(self):
        """
        Pings the database to check the connection.
        """
        if self.db is not None:
            try:
                # Ping the 'admin' database, a more reliable ping
                await self.client.admin.command("ping")
                print("Database ping successful.")
                return True
            except Exception as e:
                print(f"Database ping failed: {e}")
                return False
        return False

# Create a single instance of the Database class
# We now pass *both* the URL and the DB_NAME from our settings
db_manager = Database(
    db_url=settings.DATABASE_URL, 
    db_name=settings.DB_NAME
)

# --- Define Collection Getters ---
# These functions make it easy to get our collections
async def get_db_connection():
    return await db_manager.get_db()

async def get_product_collection():
    db = await get_db_connection()
    if db:
        return db.get_collection("products")
    return None

async def get_user_collection():
    db = await get_db_connection()
    if db:
        return db.get_collection("users")
    return None

async def get_order_collection():
    db = await get_db_connection()
    if db:
        return db.get_collection("orders")
    return None