import praw
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pymongo
import uuid

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

def get_last_crawl_time(db):
    """ Get the last crawl time from the database """
    last_post = db.memes.find_one(sort=[("crawled_at", pymongo.DESCENDING)])
    if last_post:
        return last_post["crawled_at"]
    return None

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
            "created_utc": datetime.utcfromtimestamp(post.created_utc),
            "crawled_at": datetime.utcnow()
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

def generate_report(post_data):
    """ Generate a report of the top 20 posts as a string """
    report_lines = ["Top 20 Trending Memes in the Last 24 Hours:\n"]
    for idx, post in enumerate(post_data, start=1):
        line = (
            f"{idx}. Title: {post['title']}\n"
            f"   URL: {post['url']}\n"
            f"   Upvotes: {post['upvotes']} | Comments: {post['comments_count']}\n"
            f"   Posted on: {post['created_utc']}\n"
        )
        report_lines.append(line)
    return "\n".join(report_lines)

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
            last_crawl_time = get_last_crawl_time(db)
            if last_crawl_time and datetime.utcnow() - last_crawl_time < timedelta(minutes=5):
                print("Crawl was done within the last 5 minutes. Skipping crawl.")
                return

            # top_posts = crawl_top_posts(reddit, db)
            # report = generate_report(top_posts)
            # print(report)
            # with open("top_memes_report.txt", "w") as file:
            #     file.write(report)
            # print("Report saved as 'top_memes_report.txt'.")
        print("Crawler finished")
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()