import requests
import json
import base64
import feedparser
import os
from dotenv import load_dotenv
from datetime import datetime
import ravgem

# --- Configuration ---
# Spotify API credentials (stored in environment .env file)
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Blog RSS Feeds (replace with actual blog RSS feed URLs)
# TODO: Find Daf Yomi blog links for daily updates.
BLOG_RSS_FEEDS = [
    'https://example.com/blog/feed/', # Replace with a real RSS feed URL
    'https://anotherblog.org/rss/' # Replace with another real RSS feed URL
]

# --- Sefaria API Functions ---

def get_today_daf_yomi():
    """
    Fetches today's Daf Yomi reference from the Sefaria API.
    """
    print("Fetching today's Daf Yomi reference...")
    try:
        # The Sefaria API endpoint for today's Daf Yomi
        # This will return metadata including the `text` field with the reference,
        # e.g., "Shabbat.21a"
        response = requests.get("https://www.sefaria.org/api/calendars")
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        calendar_data = response.json()
        daf = ''
        for l in calendar_data['calendar_items']:
            if l["title"]["en"] == "Daf Yomi":
                daf = (l)

        if daf and daf.get('ref'):
            daf_ref = daf["ref"]
            print(f"Today's Daf Yomi reference: {daf_ref}")
            return daf_ref
        else:
            print("Daf Yomi reference not found in Sefaria calendar data.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Daf Yomi reference from Sefaria: {e}")
        return None

def get_sefaria_text(text_ref):
    """
    Fetches the full text and translations for a given Sefaria text reference.
    e.g., text_ref = "Shabbat.21a"
    """
    if not text_ref:
        return None

    print(f"Fetching text for: {text_ref}...")
    try:
        # Sefaria API endpoint for text content.
        # `pad=0` removes padding (extra context around the requested text)
        response = requests.get(f"https://www.sefaria.org/api/texts/{text_ref}?pad=0")
        response.raise_for_status()
        text_data = response.json()

        # You'll get different language versions here.
        # 'text' usually contains Hebrew, 'he' contains Hebrew, 'en' contains English.
        # The structure can be nested (e.g., list of lists for Talmud).
        print(f"Successfully fetched text for {text_ref}.")
        return text_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Sefaria text for {text_ref}: {e}")
        return None

# --- Spotify API Functions ---

def get_spotify_access_token(client_id, client_secret):
    """
    Gets an access token for the Spotify API using the Client Credentials Flow.
    This token is used for making authorized requests.
    """
    print("Getting Spotify access token...")
    auth_url = "https://accounts.spotify.com/api/token"
    # Encode client ID and secret for the Authorization header
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_auth_string}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        token_info = response.json()
        print("Spotify access token obtained.")
        return token_info.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify access token: {e}")
        return None

def search_spotify_podcasts(query, access_token, market='US', limit=5):
    """
    Searches for Spotify podcast episodes related to the query.
    """
    if not access_token:
        print("No Spotify access token available.")
        return []

    print(f"Searching Spotify for podcast episodes related to: '{query}'...")
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "episode", # Specify type as 'episode' to search for episodes
        "market": market,
        "limit": limit
    }

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        episodes = search_results.get('episodes', {}).get('items', [])
        print(f"Found {len(episodes)} Spotify podcast episodes.")
        return episodes
    except requests.exceptions.RequestException as e:
        print(f"Error searching Spotify podcasts: {e}")
        return []

# --- Blog Post Functions (via RSS) ---
'''
def get_blog_posts_from_rss(feed_urls, limit_per_feed=3):
    """
    Fetches recent blog posts from a list of RSS feed URLs.
    """
    all_posts = []
    for url in feed_urls:
        print(f"Fetching posts from RSS feed: {url}...")
        try:
            feed = feedparser.parse(url)
            # You can add logic here to filter by date if needed
            for entry in feed.entries[:limit_per_feed]:
                # Extract relevant information
                post = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': getattr(entry, 'published', getattr(entry, 'updated', 'N/A')),
                    'summary': getattr(entry, 'summary', getattr(entry, 'description', 'N/A'))
                }
                all_posts.append(post)
            print(f"Successfully fetched {len(feed.entries[:limit_per_feed])} posts from {url}.")
        except Exception as e:
            print(f"Error fetching RSS feed from {url}: {e}")
    print(f"Total blog posts fetched: {len(all_posts)}")
    return all_posts
'''
# --- Main Pipeline Execution ---

def run_pipeline():
    """
    Orchestrates the fetching of data from all sources.
    """
    pipeline_data = {}

    # 1. Get Daf Yomi Data
    today_daf_ref = get_today_daf_yomi()
    sefaria_text_data = None
    if today_daf_ref:
        sefaria_text_data = get_sefaria_text(today_daf_ref)
        pipeline_data['sefaria_daf_yomi'] = {
            'reference': today_daf_ref,
            'text_data': sefaria_text_data
        }
    else:
        pipeline_data['sefaria_daf_yomi'] = {'reference': 'N/A', 'text_data': 'N/A'}
        print("Skipping Spotify search as Daf Yomi reference is unavailable.")

    # 2. Get Spotify Podcast Episodes (related to today's Daf Yomi if available)
    spotify_access_token = get_spotify_access_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    spotify_podcast_episodes = []
    if spotify_access_token and today_daf_ref:
        # Use the Daf Yomi reference as part of the search query
        search_query = f"Daf Yomi {today_daf_ref.replace('.', ' ')} Jewish Learning"
        spotify_podcast_episodes = search_spotify_podcasts(search_query, spotify_access_token)
    elif spotify_access_token:
        # Fallback if Daf Yomi ref isn't available, search generally
        spotify_podcast_episodes = search_spotify_podcasts("Daf Yomi Jewish podcast", spotify_access_token)
    
    pipeline_data['spotify_podcasts'] = spotify_podcast_episodes

    # # 3. Get Blog Posts
    # blog_posts = get_blog_posts_from_rss(BLOG_RSS_FEEDS)
    # pipeline_data['blog_posts'] = blog_posts

    print("\n--- Pipeline Data Summary ---")
    print(f"Sefaria Daf Yomi Fetched: {'Yes' if sefaria_text_data else 'No'}")
    print(f"Spotify Podcasts Fetched: {len(spotify_podcast_episodes)}")
    text = ravgem.ravgem_chat(today_daf_ref)
    print(text)
    # print(f"Blog Posts Fetched: {len(blog_posts)}")

    # You can now process or store 'pipeline_data' as needed.
    # For demonstration, we'll print a snippet of the data.
    # print("\n--- Raw Fetched Data (Snippet) ---")
    # print(json.dumps(pipeline_data, indent=2, ensure_ascii=False)[:1000] + "...") # Print first 1000 chars

# Run the pipeline
if __name__ == "__main__":
    # IMPORTANT: Replace 'YOUR_SPOTIFY_CLIENT_ID' and 'YOUR_SPOTIFY_CLIENT_SECRET'
    # with your actual Spotify API credentials before running.
    # Also, update BLOG_RSS_FEEDS with relevant blog RSS feed URLs.
    run_pipeline()
