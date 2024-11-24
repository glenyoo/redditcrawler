# Reddit Meme Crawler Bot

This project is a Reddit Meme Crawler Bot that fetches the top 20 trending memes from the r/memes subreddit and sends a report via a Telegram bot. The report includes charts for the top memes by upvotes and comments, a posting times distribution chart, and text and CSV reports.

## Features

- Fetches the top 20 trending memes from r/memes.
- Generates charts for:
  - Top 20 Memes by Upvotes
  - Top 20 Memes by Comments
  - Posting Times Distribution
- Generates text and CSV reports.
- Sends the report via a Telegram bot.

## Prerequisites

- Python 3.7+
- Telegram bot token
- MongoDB instance
- Reddit API credentials

## Setup

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/reddit-meme-crawler.git
    cd reddit-meme-crawler
    ```

2. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Create a `.env` file in the root directory with the following content:**

    ```properties
    MONGO_URI="your_mongo_uri"
    REDDIT_CLIENT_ID="your_reddit_client_id"
    REDDIT_CLIENT_SECRET="your_reddit_client_secret"
    REDDIT_USER_AGENT="your_reddit_user_agent"
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    ```

4. **Run the bot:**

    ```sh
    python crawler.py
    ```

## Usage

1. **Start the bot on Telegram:**

    Search for the bot on Telegram using the username [@RedditTopMeme_Bot](https://t.me/RedditTopMeme_Bot) and start a chat.

2. **Commands:**

    - `/start`: Sends a welcome message explaining the bot's functionality.
    - `/generate`: Fetches the top 20 trending memes from r/memes, generates the reports and charts, and sends them via Telegram.

## Example

When you send the `/generate` command, the bot will respond with a message formatted like this:

Reddit Top 20 Meme Report

Top 20 Memes by Upvotes (Image)
Top 20 Memes by Comments (Image) 
Posting Times Distribution (Image) 
Reddit Top 20 Meme Report (Text) 
Reddit Top 20 Meme Report (CSV)

Report generated at: 2024-11-24 16:14 SGT

## License

This project is licensed under the MIT License.