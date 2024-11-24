#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpraw
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import uuid
from telegram import Bot, Update, InputMediaPhoto, InputMediaDocument
from telegram.ext import Application, CommandHandler, CallbackContext
import asyncio
import pytz
import csv
import matplotlib.pyplot as plt
import seaborn as sns

# Load environment variables from .env
load_dotenv()

def connect_to_mongo():
    """ Connect to MongoDB and return the database object """
    try:
        print("Connecting to MongoDB...")
        MONGO_URI = os.getenv("MONGO_URI")
        client = MongoClient(MONGO_URI)
        print("Connected to MongoDB")
        return client.meme_data
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def is_recent_crawl(db):
    """ Check if there is a recent crawl in the past 5 minutes """
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    recent_crawl = db.memes.find_one({"crawled_at": {"$gte": recent_time}})
    if recent_crawl:
        print(f"Recent crawl detected at {recent_crawl['crawled_at']}.")
        return True
    print("No recent crawl detected.")
    return False

async def crawl_top_posts(reddit, db):
    """ Crawl the top 20 posts from r/memes in the past 24 hours """
    subreddit = await reddit.subreddit("memes")
    top_posts = subreddit.top(time_filter="day", limit=20)

    post_data = []
    async for post in top_posts:
        post_entry = {
            "_id": str(uuid.uuid4()),  # Generate a new unique identifier
            "reddit_id": post.id,  # Store the Reddit post ID separately
            "title": post.title,
            "url": post.url,
            "upvotes": post.score,
            "comments_count": post.num_comments,
            "created_utc": datetime.fromtimestamp(post.created_utc, timezone.utc),
            "crawled_at": datetime.now(timezone.utc)
        }
        post_data.append(post_entry)

        # Insert into MongoDB
        try:
            db.memes.insert_one(post_entry)
            print(f"Inserted: {post.title}")
        except Exception as e:
            print(f"Error inserting post: {post.title}, {e}")

    print(f"Stored {len(post_data)} posts from r/memes.")
    return post_data

def generate_text_report(post_data, file_path="top_memes_report.txt"):
    """ Generate and save a text report of the top 20 posts """
    report_lines = ["Reddit Top 20 Meme Report\n"]
    report_lines.append("Top 20 Trending Memes in the Last 24 Hours:\n")
    for idx, post in enumerate(post_data, start=1):
        line = (
            f"{idx}. Title: {post['title']}\n"
            f"   URL: {post['url']}\n"
            f"   Upvotes: {post['upvotes']} | Comments: {post['comments_count']}\n"
            f"   Posted on: {post['created_utc']}\n"
        )
        report_lines.append(line)
    
    # Convert the current time to Singapore time
    sg_timezone = pytz.timezone("Asia/Singapore")
    sg_time = datetime.now(sg_timezone)
    report_lines.append(f"\nReport generated at: {sg_time.strftime('%Y-%m-%d %H:%M SGT')}\n")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(report_lines))
    print(f"Text report saved as '{file_path}'.")
    return file_path

def generate_csv_report(post_data, file_path="top_memes_report.csv"):
    """ Generate and save a CSV report of the top 20 posts """
    sg_timezone = pytz.timezone("Asia/Singapore")
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["Title", "URL", "Upvotes", "Comments", "Posted On"])
        # Write data rows
        for post in post_data:
            created_sg_time = post['created_utc'].astimezone(sg_timezone).strftime('%Y-%m-%d %H:%M:%S %Z')
            writer.writerow([post['title'], post['url'], post['upvotes'], post['comments_count'], created_sg_time])
    print(f"CSV report saved as '{file_path}'.")
    return file_path

def generate_charts(post_data):
    """ Generate and save charts for analysis """
    # Convert post_data to a DataFrame
    import pandas as pd
    sg_timezone = pytz.timezone("Asia/Singapore")
    df = pd.DataFrame(post_data)

    # Convert created_utc to Singapore time
    df['created_sg'] = df['created_utc'].apply(lambda x: x.astimezone(sg_timezone))
    df['created_hour_sg'] = df['created_sg'].dt.hour

    # Engagement metrics (upvotes and comments)
    plt.figure(figsize=(10, 6))
    sns.barplot(x='upvotes', y='title', data=df.sort_values('upvotes', ascending=False))
    plt.title('Top 20 Memes by Upvotes')
    plt.xlabel('Upvotes')
    plt.ylabel('Title')
    plt.tight_layout()
    plt.savefig('upvotes_chart.png')
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.barplot(x='comments_count', y='title', data=df.sort_values('comments_count', ascending=False))
    plt.title('Top 20 Memes by Comments')
    plt.xlabel('Comments')
    plt.ylabel('Title')
    plt.tight_layout()
    plt.savefig('comments_chart.png')
    plt.close()

    # Posting times for patterns
    plt.figure(figsize=(10, 6))
    sns.histplot(df['created_hour_sg'], bins=24, kde=False)
    plt.title('Posting Times Distribution (SGT)')
    plt.xlabel('Hour of Day (SGT)')
    plt.ylabel('Number of Posts')
    plt.tight_layout()
    plt.savefig('posting_times_chart.png')
    plt.close()

    print("Charts generated and saved.")

async def send_combined_report_via_telegram(chat_id, chart_files, report_files, chart_captions, report_captions, article_header, article_footer):
    """ Send the combined report files via Telegram """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = Bot(token=bot_token)
    try:
        # Send the header
        await bot.send_message(chat_id=chat_id, text=article_header)
        
        # Send the charts
        media_group = []
        for file_path, caption in zip(chart_files, chart_captions):
            with open(file_path, "rb") as file:
                media_group.append(InputMediaPhoto(file, caption=caption))
        await bot.send_media_group(chat_id=chat_id, media=media_group)
        
        # Send the reports
        for file_path, caption in zip(report_files, report_captions):
            with open(file_path, "rb") as file:
                await bot.send_document(chat_id=chat_id, document=file, caption=caption)
        
        # Send the footer
        await bot.send_message(chat_id=chat_id, text=article_footer)
        
        print("Combined report sent via Telegram.")
    except Exception as e:
        print(f"Failed to send combined report: {e}")

async def run_crawler(update: Update, context: CallbackContext):
    """ Run the crawler and send the reports via Telegram """
    try:
        chat_id = update.effective_chat.id
        print(f"Starting crawler for chat_id: {chat_id}")
        reddit = asyncpraw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT")
        )
        print("Reddit instance created")
        db = connect_to_mongo()
        if db is not None:
            generate_new_reports = False
            report_file_paths = ["top_memes_report.txt", "top_memes_report.csv"]
            report_captions = ["Reddit Top 20 Meme Report (Text)", "Reddit Top 20 Meme Report (CSV)"]
            chart_files = ["upvotes_chart.png", "comments_chart.png", "posting_times_chart.png"]
            chart_captions = ["Top 20 Memes by Upvotes", "Top 20 Memes by Comments", "Posting Times Distribution"]
            if is_recent_crawl(db):
                print("Recent crawl detected. Skipping new crawl.")
                for report_file_path in report_file_paths:
                    if not os.path.exists(report_file_path):
                        print(f"Report file '{report_file_path}' does not exist. Generating new report.")
                        generate_new_reports = True
                        break
                for chart_file in chart_files:
                    if not os.path.exists(chart_file):
                        print(f"Chart file '{chart_file}' does not exist. Generating new charts.")
                        generate_new_reports = True
                        break
                if not generate_new_reports:
                    sg_timezone = pytz.timezone("Asia/Singapore")
                    sg_time = datetime.now(sg_timezone)
                    article_header = "Reddit Top 20 Meme Report\n\n"
                    article_footer = f"\nReport generated at: {sg_time.strftime('%Y-%m-%d %H:%M SGT')}\n"
                    await send_combined_report_via_telegram(chat_id, chart_files, report_file_paths, chart_captions, report_captions, article_header, article_footer)
                    return

            top_posts = await crawl_top_posts(reddit, db)
            text_report_path = generate_text_report(top_posts)
            csv_report_path = generate_csv_report(top_posts)
            generate_charts(top_posts)
            sg_timezone = pytz.timezone("Asia/Singapore")
            sg_time = datetime.now(sg_timezone)
            article_header = "Reddit Top 20 Meme Report\n\n"
            article_footer = f"\nReport generated at: {sg_time.strftime('%Y-%m-%d %H:%M SGT')}\n"
            await send_combined_report_via_telegram(chat_id, chart_files, report_file_paths, chart_captions, report_captions, article_header, article_footer)
        print("Crawler finished")
    except Exception as e:
        print(f"Error in main execution: {e}")

async def start(update: Update, context: CallbackContext):
    """ Send a welcome message when the /start command is issued """
    await update.message.reply_text(
        "Welcome to the Reddit Meme Bot! This bot finds the top 20 trending memes from Reddit.\n"
        "Use the /generate command to get the latest report."
    )

def main():
    """ Start the bot """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(bot_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", run_crawler))

    # Start the Bot
    application.run_polling()
    print("Bot started. Waiting for commands...")

if __name__ == "__main__":
    print("Bot started. Waiting for commands...")
    main()