import os
from apify_client import ApifyClient
import pandas as pd
import streamlit as st


def scrape_profile(url, max_posts):
    # 1. Clean up old data file if present
    if os.path.exists("social_data.xlsx"):
        try:
            os.remove("social_data.xlsx")
        except:
            pass

    # 2. Retrieve Apify API Token from Streamlit Secrets or Environment Variable
    api_token = st.secrets.get("APIFY_TOKEN") or os.getenv("APIFY_TOKEN")

    if not api_token:
        print("APIFY_TOKEN missing! Set it in Streamlit Secrets or .env file.")
        pd.DataFrame({"Post_No": [0]}).to_excel("social_data.xlsx", index=False)
        return

    # 3. Initialize Apify Client
    client = ApifyClient(api_token)

    # 4. Configure input for the Apify Instagram Scraper actor
    run_input = {
        "directUrls": [url],
        "resultsLimit": max_posts,
    }

    audit_results = []

    try:
        print(f"Scraping {url} via Apify...")

        # 5. Run the actor and fetch dataset items
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

        # 6. Map Apify response data to your dashboard's required schema
        for idx, item in enumerate(dataset_items):
            # Extract follower count (Apify returns owner object metadata)
            follower_count = (
                item.get("ownerFollowersCount")
                or item.get("owner", {}).get("followersCount")
                or 0
            )

            # Extract likes, comments, and caption safely
            likes = item.get("likesCount", 0)
            comments = item.get("commentsCount", 0)
            caption = item.get("caption", "No Caption")

            audit_results.append(
                {
                    "Post_No": idx + 1,
                    "Likes": likes,
                    "Comments": comments,
                    "Caption": caption[:100] if caption else "",
                    "Followers": follower_count,
                }
            )

        # 7. Save to social_data.xlsx if data exists, else save fallback error indicator
        if audit_results:
            pd.DataFrame(audit_results).to_excel(
                "social_data.xlsx", index=False
            )
            print("Data saved successfully to social_data.xlsx")
        else:
            pd.DataFrame({"Post_No": [0]}).to_excel(
                "social_data.xlsx", index=False
            )

    except Exception as e:
        print(f"Apify Scraping Error: {e}")
        pd.DataFrame({"Post_No": [0]}).to_excel("social_data.xlsx", index=False)