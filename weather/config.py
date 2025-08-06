import os

# Default to environment variable, fallback to hardcoded (for dev only)
class Config:

    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_dev_key_here")
