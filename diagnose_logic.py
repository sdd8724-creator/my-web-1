import os
from trending_shorts_finder import YouTubeTrendingFinder

def diagnose():
    print("--- Starting Diagnosis ---")
    finder = YouTubeTrendingFinder()
    
    if not finder.api_key:
        print("[-] Error: API Key not loaded in YouTubeTrendingFinder")
        return

    print(f"[+] API Key loaded: {finder.api_key[:5]}...")
    
    print("[*] Testing get_trending_videos...")
    # 필터를 조금 완화해서 테스트 (AI 필터는 유지하되 길이는 넉넉하게)
    results = finder.get_trending_videos(max_duration=600, only_korean=True)
    
    print(f"[*] Found {len(results)} videos in trending (filtered by AI keywords)")
    for v in results[:3]:
        print(f"  - {v['title']} (KV: {v['matched_keyword']})")

    print("[*] Testing get_search_results for 'AI 애니메이션'...")
    search_results = finder.get_search_results(query="AI 애니메이션", max_duration=600)
    print(f"[*] Found {len(search_results)} videos in search results")
    for v in search_results[:3]:
        print(f"  - {v['title']} (KV: {v['matched_keyword']})")

if __name__ == "__main__":
    diagnose()
