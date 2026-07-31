import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from scraper_logic import scrape_profile
from streamlit_extras.metric_cards import style_metric_cards

# Load environment variables
load_dotenv()
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="INSTA-AUDITOR PRO", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Auditor Settings")
    target_url = st.text_input("Profile URL", "https://www.instagram.com/nike/")
    num_posts = st.slider("Posts to analyze", 1, 25, 10)
    run_btn = st.button("🚀 RUN COMPREHENSIVE AUDIT")

st.title("📊 Social Media Audit Dashboard")

# --- AUDIT EXECUTION ---
if run_btn:
    with st.status("🕵️ Fetching posts via Apify...") as status:
        # Call Apify function directly (synchronous)
        scrape_profile(target_url, num_posts)
        status.update(label="Audit Complete!", state="complete")

    if os.path.exists("social_data.xlsx"):
        df = pd.read_excel("social_data.xlsx")

        # Clean column names (remove hidden spaces)
        df.columns = [str(col).strip() for col in df.columns]

        # Check if scraper extracted valid data
        if "Post_No" in df.columns:
            real_data = df[df["Post_No"] != 0]
        else:
            real_data = pd.DataFrame()

        if real_data.empty:
            st.error(
                "Scraper couldn't read post data. Please check your APIFY_TOKEN in Streamlit Secrets."
            )
        else:
            # Stats calculation
            fols = (
                int(df["Followers"].iloc[0]) if "Followers" in df.columns else 0
            )
            avg_l = (
                real_data["Likes"].mean() if "Likes" in real_data.columns else 0
            )
            eng_rate = (avg_l / fols * 100) if fols > 0 else 0

            # Metrics display
            c1, c2, c3 = st.columns(3)
            c1.metric("Followers", f"{fols:,}")
            c2.metric("Engagement Rate", f"{eng_rate:.2f}%")
            c3.metric("Avg Likes", f"{avg_l:,.0f}")
            style_metric_cards(background_color="#1a1c23")

            # AI Report
            st.subheader("🤖 Groq AI Auditor Report")
            if groq_api_key:
                client = Groq(api_key=groq_api_key)
                prompt = f"Audit this Instagram data: {real_data.to_string()}. Summarize content strategy."

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                )
                placeholder = st.empty()
                full_res = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
            else:
                st.warning(
                    "Please add your GROQ_API_KEY to Streamlit secrets or .env file."
                )

            st.dataframe(real_data)