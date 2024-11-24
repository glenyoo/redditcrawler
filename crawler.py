#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import praw
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import uuid
from telegram import Bot
import asyncio
import pytz
import csv

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
    return db.memes.find_one({"crawled_at": {"$gte": recent_time}}) is not None

def crawl_top_posts(reddit, db):
    """ Crawl the top 20 posts from r/memes in the past 24 hours """
    subreddit = reddit.subreddit("memes")
    top_posts = subreddit.top(time_filter="day", limit=20)

    post_data = []
    for post in top_posts:
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
    report_lines = ["Top 20 Trending Memes in the Last 24 Hours:\n"]
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
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["Title", "URL", "Upvotes", "Comments", "Posted On"])
        # Write data rows
        for post in post_data:
            writer.writerow([post['title'], post['url'], post['upvotes'], post['comments_count'], post['created_utc']])
    print(f"CSV report saved as '{file_path}'.")
    return file_path

async def send_report_via_telegram(file_path, caption):
    """ Send the report file via Telegram """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot = Bot(token=bot_token)
    try:
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=chat_id, document=file, caption=caption)
        print(f"Report '{file_path}' sent via Telegram.")
    except Exception as e:
        print(f"Failed to send '{file_path}': {e}")

def main():
    try:
        print("Starting crawler...")
        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT")
        )
        print("Reddit instance created")
        db = connect_to_mongo()
        if db is not None:
            if is_recent_crawl(db):
                print("Recent crawl detected. Skipping new crawl.")
                report_file_paths = ["top_memes_report.txt", "top_memes_report.csv"]
                for report_file_path in report_file_paths:
                    if not os.path.exists(report_file_path):
                        print(f"Report file '{report_file_path}' does not exist. Generating new report.")
                        top_posts = crawl_top_posts(reddit, db)
                        if report_file_path.endswith(".txt"):
                            generate_text_report(top_posts, report_file_path)
                        elif report_file_path.endswith(".csv"):
                            generate_csv_report(top_posts, report_file_path)
                    asyncio.run(send_report_via_telegram(report_file_path, "Top 20 Trending Memes"))
                return

            top_posts = crawl_top_posts(reddit, db)
            text_report_path = generate_text_report(top_posts)
            csv_report_path = generate_csv_report(top_posts)
            asyncio.run(send_report_via_telegram(text_report_path, "Top 20 Trending Memes (Text)"))
            asyncio.run(send_report_via_telegram(csv_report_path, "Top 20 Trending Memes (CSV)"))
        print("Crawler finished")
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()