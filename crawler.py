#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("Script started")

import praw
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_mongo():
    """ Connect to MongoDB and return the database object """
    try:
        print("Connecting to MongoDB...")
        client = MongoClient(os.environ.get("MONGO_URI"))
        print("Connected to MongoDB")
        return client.meme_data
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def crawl_top_posts(reddit, db):
    """ Crawl the top 20 posts from r/memes in the past 24 hours """
    try:
        print("Crawling top posts from r/memes...")
        subreddit = reddit.subreddit('memes')
        top_posts = subreddit.top(time_filter="day", limit=20)

        post_data = []
        for post in top_posts:
            post_entry = {
                "_id": post.id,  # Use Reddit post ID as unique identifier
                "title": post.title,
                "url": post.url,
                "upvotes": post.score,
                "comments_count": post.num_comments,
                "created_utc": datetime.utcfromtimestamp(post.created_utc),
            }
            post_data.append(post_entry)
            print(f"Post crawled: {post_entry}")

        # Insert into MongoDB
        if post_data:
            print("Inserting posts into MongoDB...")
            db.posts.insert_many(post_data)
            print("Posts inserted into MongoDB")
        else:
            print("No posts to insert")
    except Exception as e:
        print(f"Error crawling posts: {e}")

# Example usage
if __name__ == "__main__":
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
            print("Emptying the posts collection...")
            db.posts.delete_many({})
            print("Posts collection emptied")
            crawl_top_posts(reddit, db)
        print("Crawler finished")
    except Exception as e:
        print(f"Error in main execution: {e}")