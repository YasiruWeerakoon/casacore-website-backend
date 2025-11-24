import uvicorn
import motor.motor_asyncio
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator
from typing import Optional, List, Annotated
from bson import ObjectId
import datetime

# ------------------------------------------------------------------
# 1. SETTINGS
# ------------------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )
    DATABASE_URL: str
    DB_NAME: str = "casacore_db"

settings = Settings()

# ------------------------------------------------------------------
# 2. DATABASE
# ------------------------------------------------------------------
class Database:
    def __init__(self, db_url: str, db_name: str):
        print("Initializing database connection...")
        self.db_name = db_name
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                db_url,
                maxPoolSize=10,
                minPoolSize=5,
                timeoutMS=30000, 
                serverSelectionTimeoutMS=10000 
            )
            self.db = self.client[self.db_name]
            print(f"Database client initialized. Pointing to '{self.db_name}'.")
        except Exception as e:
            print(f"Error initializing database client: {e}")
            self.client = None
            self.db = None

    async def get_db(self):
        if self.db is not None:
            return self.db
        return None

    async def close(self):
        if self.client:
            self.client.close()
            print("Database connection closed.")
            
    async def ping(self):
        if self.db is not None:
            try:
                await self.client.admin.command("ping")
                print("Database ping successful.")
                return True
            except Exception as e:
                print(f"Database ping failed: {e}")
                return False
        return False
    
    def get_product_collection(self):
        if self.db is not None:
            return self.db.get_collection("products")
        return None

db_manager = Database(
    db_url=settings.DATABASE_URL, 
    db_name=settings.DB_NAME
)

# ------------------------------------------------------------------
# 3. PYDANTIC MODELS
# ------------------------------------------------------------------

PyObjectId = Annotated[str, BeforeValidator(str)]

class ProductModel(BaseModel):
    """
    Blueprint for Product response.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    description: str = Field(...)
    
    # --- FIX IS HERE ---
    # Changed gt=0 (Greater Than) to ge=0 (Greater or Equal)
    # This allows price to be 0.0 without crashing the app
    price: float = Field(..., ge=0) 
    
    stock_quantity: int = Field(..., ge=0)
    category: str = Field(...)
    image_urls: List[str] = []
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "name": "Tiny Thorny",
                "description": "A tiny cute cactus.",
                "price": 890.00,
                "stock_quantity": 50,
                "category": "Cactus",
                "image_urls": ["https://placehold.co/400x400"]
            }
        }

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock_quantity: int
    category: str
    image_urls: Optional[List[str]] = []

# ------------------------------------------------------------------
# 4. APP LIFESPAN
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI app starting up...")
    db = await db_manager.get_db()
    if db is None:
        print("FATAL ERROR: Could not connect to database.")
    else:
        print("Database connection established.")
    yield
    print("FastAPI app shutting down...")
    await db_manager.close()

# ------------------------------------------------------------------
# 5. CREATE THE APP
# ------------------------------------------------------------------
app = FastAPI(
    lifespan=lifespan,
    title="CasaCore API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# 6. API ENDPOINTS
# ------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to the CasaCore Backend! 🌱🧱"}

@app.get("/api/test-db")
async def test_database_connection():
    if await db_manager.ping():
        return {"status":"success","message":"Database connection is working!"}
    else:
        return {"status":"error","message":"Database connection failed."}

@app.post("/api/products", response_model=ProductModel, status_code=status.HTTP_201_CREATED)
async def create_product(product_data: ProductCreate):
    product_collection = db_manager.get_product_collection()
    if product_collection is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    product_dict = product_data.model_dump()
    product_dict["created_at"] = datetime.datetime.now()

    new_product = await product_collection.insert_one(product_dict)
    created_product = await product_collection.find_one({"_id": new_product.inserted_id})
    
    return created_product

@app.get("/api/products", response_model=List[ProductModel])
async def get_all_products():
    product_collection = db_manager.get_product_collection()
    if product_collection is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    products = []
    async for product in product_collection.find():
        products.append(product)
    
    return products

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)