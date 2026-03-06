import os
import re
import isodate
from trending_shorts_finder import YouTubeTrendingFinder

class DetailedDiagnose(YouTubeTrendingFinder):
    def get_video_details_verbose(self, video_ids, max_duration=240, region_code=None, only_korean=False):
        results = []
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(batch_ids)
            )
            response = request.execute()
            items = response.get('items', [])
            for item in items:
                snippet = item.get('snippet', {})
                content_details = item.get('contentDetails', {})
                title = snippet.get('title', '')
                description = snippet.get('description', '')
                tags = snippet.get('tags', [])
                channel_title = snippet.get('channelTitle', '')
                
                # Check Korean
                has_korean = bool(re.search(r'[\uac00-\ud7a3]', title + description))
                if only_korean and not has_korean:
                    # print(f"[Skip] No Korean: {title[:30]}")
                    continue
                
                # Check Duration
                duration_str = content_details.get('duration')
                try:
                    duration_seconds = isodate.parse_duration(duration_str).total_seconds()
                except: duration_seconds = 0
                
                if duration_seconds > max_duration:
                    # print(f"[Skip] Too Long ({duration_seconds}s): {title[:30]}")
                    continue
                
                # Check AI Content
                is_valid, matched_kw = self.is_ai_content(title, description, tags, channel_title)
                
                if not is_valid:
                    # AI 콘텐츠가 아니라고 판단된 것들 중 혹시 AI 채널인지 확인하기 위해 채널명 출력
                    # print(f"[Skip] Not AI: {title[:30]} | Channel: {channel_title}")
                    continue
                
                results.append(title)
        return results

def run_detailed_diagnose():
    print("--- Detailed Trending Diagnosis ---")
    finder = DetailedDiagnose()
    if not finder.api_key:
        print("API Key missing")
        return

    # 인기 급상승 200개를 가져와서 필터링 과정을 모니터링
    video_ids = []
    request = finder.youtube.videos().list(
        part="id",
        chart="mostPopular",
        regionCode="KR",
        maxResults=50
    )
    response = request.execute()
    video_ids = [item['id'] for item in response.get('items', [])]
    
    print(f"Analyzing Top 50 Trending Videos...")
    
    # 각 스텝별로 필터링 통과 개수 확인
    for item in response.get('items', []):
        vid_id = item['id']
        det = finder.youtube.videos().list(part="snippet,contentDetails", id=vid_id).execute()['items'][0]
        title = det['snippet']['title']
        channel = det['snippet']['channelTitle']
        desc = det['snippet']['description']
        tags = det['snippet'].get('tags', [])
        dur = isodate.parse_duration(det['contentDetails']['duration']).total_seconds()
        
        is_ai, kw = finder.is_ai_content(title, desc, tags, channel)
        has_ko = bool(re.search(r'[\uac00-\ud7a3]', title + desc))
        
        status = "PASSED" if is_ai and has_ko and dur <= 240 else "FAILED"
        reason = ""
        if not is_ai: reason += "NotAI "
        if not has_ko: reason += "NoKorean "
        if dur > 240: reason += f"TooLong({dur}s) "
        
        if status == "PASSED" or "NotAI" not in reason: # AI인데 다른 이유로 잘린 것들 위주로 보기
             print(f"[{status}] {title[:40]} | {channel} | Reason: {reason} | KW: {kw}")

if __name__ == "__main__":
    run_detailed_diagnose()
