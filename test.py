from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv(dotenv_path=".env")

# Get the connection string from .env
connection_string = os.getenv("MONGO_URI")

client = MongoClient(connection_string)
db = client.meme_data
if db is not None:
    print("Connected to MongoDB!")

# Debugging environment variables
print("REDDIT_CLIENT_ID:", os.getenv("REDDIT_CLIENT_ID"))
print("REDDIT_CLIENT_SECRET:", os.getenv("REDDIT_CLIENT_SECRET"))
print("REDDIT_USER_AGENT:", os.getenv("REDDIT_USER_AGENT"))
