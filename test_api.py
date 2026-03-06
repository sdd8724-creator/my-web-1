import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        return

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part="snippet",
            chart="mostPopular",
            regionCode="KR",
            maxResults=5
        )
        response = request.execute()
        print("API Connection Successful!")
        print(f"Fetched {len(response.get('items', []))} trending videos.")
        for item in response.get('items', []):
            print(f"- {item['snippet']['title']}")
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    test_api()
