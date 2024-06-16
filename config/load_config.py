import os
import dotenv
import json

dotenv.load_dotenv(override=True)

PORT = os.getenv("PORT") or "8000"  # port for running app
SECRET = os.getenv("SECRET")  # for jwt signing
API_NAME = os.getenv("API_NAME") or "Simple Image Uploader"  # api name
API_DESCRIPTION = os.getenv("API_DESCRIPTION") or ""  # api description
RELOAD = "true" == os.getenv("RELOAD")
HOST = os.getenv("HOST") or "127.0.0.1"  # host for running app
PRODUCTION = "true" == os.getenv("PRODUCTION")  # production mode
DATABASE_URI = os.getenv("DATABASE_URI") or "sqlite://database.db"  # database uri

with open("choices.json", "r", encoding="utf8") as f:
    CHOICES = json.load(f)
