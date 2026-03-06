import os
import re
import isodate
from trending_shorts_finder import YouTubeTrendingFinder

def debug_trending_logic():
    print("=== [DEBUG] Trending Logic Analysis ===")
    finder = YouTubeTrendingFinder()
    if not finder.api_key:
        print("[-] API Key missing")
        return

    # 1. Trending Chart 분석 (Top 50만 샘플링)
    print("\n1. Analyzing Top 50 Trending Chart...")
    try:
        request = finder.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode="KR",
            maxResults=50
        )
        response = request.execute()
        items = response.get('items', [])
        
        passed_ko = 0
        passed_dur = 0
        passed_ai = 0
        
        for item in items:
            title = item['snippet']['title']
            desc = item['snippet']['description']
            dur_str = item['contentDetails']['duration']
            channel = item['snippet']['channelTitle']
            tags = item['snippet'].get('tags', [])
            
            # Filter 1: Korean
            has_ko = bool(re.search(r'[\uac00-\ud7a3]', title + desc))
            if has_ko: passed_ko += 1
            
            # Filter 2: Duration (기준 240초)
            dur = isodate.parse_duration(dur_str).total_seconds()
            is_short = dur <= 240
            if is_short: passed_dur += 1
            
            # Filter 3: AI
            is_ai, kw = finder.is_ai_content(title, desc, tags, channel)
            if is_ai: passed_ai += 1
            
            if is_ai:
                print(f"[O] '{title[:30]}...' | Dur: {dur}s | Ko: {has_ko} | AI: {is_ai} ({kw})")
        
        print(f"\n[Summary - Chart Top 50]")
        print(f"- Total: 50")
        print(f"- Passed Korean: {passed_ko}")
        print(f"- Passed Duration: {passed_dur}")
        print(f"- Passed AI/Anim: {passed_ai}")

    except Exception as e:
        print(f"[-] Error: {e}")

    # 2. Supplemental Search 분석
    print("\n2. Analyzing Supplemental Search ('AI 애니메이션')...")
    try:
        search_req = finder.youtube.search().list(
            q="AI 애니메이션",
            part="id",
            type="video",
            maxResults=20,
            regionCode="KR",
            relevanceLanguage="ko"
        )
        search_res = search_req.execute()
        vids = [it['id']['videoId'] for it in search_res.get('items', [])]
        
        print(f"[*] Found {len(vids)} candidates from supplemental search.")
        
        # 상세 정보 확인
        detail_req = finder.youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(vids)
        )
        detail_res = detail_req.execute()
        
        passed_search = 0
        for item in detail_res.get('items', []):
            title = item['snippet']['title']
            desc = item['snippet']['description']
            is_ai, kw = finder.is_ai_content(title, desc, item['snippet'].get('tags', []), item['snippet']['channelTitle'])
            has_ko = bool(re.search(r'[\uac00-\ud7a3]', title + desc))
            
            if is_ai and has_ko:
                passed_search += 1
            else:
                print(f"[X] Fail: {title[:30]}... | Ko: {has_ko} | AI: {is_ai}")
        
        print(f"Final Passed in Supplemental Sample: {passed_search}")

    except Exception as e:
        print(f"[-] Search Error: {e}")

if __name__ == "__main__":
    debug_trending_logic()
