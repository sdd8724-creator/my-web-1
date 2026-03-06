import streamlit as st
import os
from trending_shorts_finder import YouTubeTrendingFinder

def test_streamlit_context():
    # Attempt to simulate how streamlit_app.py gets the key
    api_key = st.secrets.get("secrets", {}).get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    print(f"[*] API Key found: {'Yes' if api_key else 'No'}")
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        finder = YouTubeTrendingFinder()
        print("[*] Initializing finder...")
        results = finder.get_trending_videos(max_duration=240, region_code='KR', language='ko')
        print(f"[*] Found {len(results)} videos.")
        for v in results[:3]:
            print(f"  - {v['title']} ({v['view_count']} views)")

if __name__ == "__main__":
    try:
        test_streamlit_context()
    except Exception as e:
        print(f"[!] Error: {e}")
