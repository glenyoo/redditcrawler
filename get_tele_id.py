import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables from .env file
load_dotenv()

# Get the bot token from environment variables
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the bot
bot = Bot(token=bot_token)

# Function to get updates and print chat IDs
async def get_chat_ids():
    print("Fetching updates...")
    updates = await bot.get_updates()
    if not updates:
        print("No updates found.")
    for update in updates:
        chat_id = update.message.chat.id
        print(f"Chat ID: {chat_id}")

if __name__ == "__main__":
    print("Starting script...")
    asyncio.run(get_chat_ids())
    print("Script finished.")
