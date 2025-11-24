from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings, loading from a .env file.
    """
    # This tells pydantic to load from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # This variable MUST match the one in your .env file
    DATABASE_URL: str
    
    # We will explicitly define our database name here
    # This fixes the AttributeError
    DB_NAME: str = "casacore_db"

# Create one instance of Settings that our app can use
settings = Settings()