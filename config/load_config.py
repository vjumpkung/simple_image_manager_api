import os
import dotenv

dotenv.load_dotenv(override=True)

PORT = int(os.getenv("PORT")) or 8000  # port for running app
SECRET = os.getenv("SECRET")  # for jwt signing
API_NAME = os.getenv("API_NAME") or "Catalog API"  # api name
API_DESCRIPTION = os.getenv("API_DESCRIPTION") or ""  # api description
RELOAD = "true" == os.getenv("RELOAD")
HOST = os.getenv("HOST") or "127.0.0.1"  # host for running app
