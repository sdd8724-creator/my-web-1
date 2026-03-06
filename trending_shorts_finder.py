import os
import sys
import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv
import isodate
import re

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

class YouTubeTrendingFinder:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.youtube = None
        if self.api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        self.ai_keywords = [
            'sora', 'kling', 'luma', 'pika', 'kaiber', 'runway gen', 'gen-2', 'gen-3',
            'flux', 'midjourney', 'comfyui', 'stable video diffusion', 'svd', 'deforum', 
            'viggle', 'hailuo', 'minimax', 'haiper', 'dreammachine', 'jimeng', 'aigc',
            'animated ai', 'ai animation', 'ai film', 'ai movie', 'synthetic media', 
            'generative video', 'ai 애니메이션', '소라 ai', '클링 ai', '루마 ai', '단편영화', 
            'ai 스토리', 'ai 웹툰', 'ai 만화', '인공지능 애니메이션', 'ai 영상', 'ai 생성', 'ai 실사화',
            'unreal engine', 'unreal animation', 'blender 3d', 'cgi animation', '3d animation',
            'vfx', 'visual effects', 'ai 룩북', 'ai 쇼츠', 'ai 비디오', 'ai 제작', 'ai 작업물'
        ]
        
        self.animation_keywords = [
            'animation', 'anime', 'animated', 'storytelling', 'story', 'cartoon',
            '애니메이션', '애니', '만화', '스토리텔링', '동화', '웹툰', 'render',
            '시네마틱', 'cinematic', '연재', '에피소드', 'episode', 'series'
        ]
        
        self.exclude_keywords = [
            'mv', 'm/v', 'official video', 'music video', 'official music video',
            'provided to youtube', '- topic', 'topic channel', 'lyrics', '가사',
            'live performance', 'fancam', '직캠', '뮤직비디오', '아이돌', 'idol',
            'dance practice', 'challenge', '챌린지', 'official audio', 'visualizer', 
            'karaoke', 'mr', 'bgm', 'instrumental', 'soundtrack', 'ost',
            'vlog', '브이로그', '먹방', 'asmr', '리액션', 'reaction',
            '뉴스', 'news', '속보', '스포츠', 'sports', 'football', 'soccer', '축구',
            'gameplay', '게임플레이', '모바일 게임', 'walkthrough'
        ]

    def is_ai_content(self, title, description, tags, channel_title):
        full_text = f"{title} {description} {' '.join(tags or [])} {channel_title}".lower()
        # 공백 제거 버전도 확인하여 'ai애니' 같은 경우 탐지
        text_no_space = full_text.replace(" ", "")
        
        # 명백한 외국어 문자 (Hindi, Arabic 등) 포함 여부 확인
        # Devanagari (Hindi): \u0900-\u097F
        # Arabic: \u0600-\u06FF
        has_foreign_script = bool(re.search(r'[\u0900-\u097f\u0600-\u06ff]', full_text))
        
        kws = self.ai_keywords + self.animation_keywords
        for kw in kws:
            if kw in full_text or kw.replace(" ", "") in text_no_space:
                return True, kw, has_foreign_script
        return False, None, has_foreign_script

    def get_search_results(self, query, max_duration=240, max_results=50, published_after=None, region_code='KR', language='ko', order='viewCount'):
        if not self.youtube: return []
        all_results = []
        next_page_token = None
        total_fetched = 0
        target_count = 15
        try:
            while len(all_results) < target_count and total_fetched < max_results:
                search_params = {
                    "q": query,
                    "part": "id",
                    "type": "video",
                    "order": order,
                    "maxResults": 50,
                    "pageToken": next_page_token
                }
                if region_code and region_code != 'all':
                    search_params["regionCode"] = region_code
                    search_params["relevanceLanguage"] = 'ko' if region_code == 'KR' else 'en'
                if published_after:
                    search_params["publishedAfter"] = published_after

                search_request = self.youtube.search().list(**search_params)
                search_response = search_request.execute()
                items = search_response.get('items', [])
                if not items: break
                batch_ids = [item['id']['videoId'] for item in items if 'videoId' in item.get('id', {})]
                if not batch_ids: break
                total_fetched += len(batch_ids)
                batch_results = self.get_video_details(batch_ids, max_duration, region_code, language, order)
                all_results.extend(batch_results)
                if len(all_results) >= target_count: break
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token: break
            return all_results
        except Exception as e:
            print(f"Error in get_search_results: {e}")
            return []

    def get_video_details(self, video_ids, max_duration=240, region_code=None, language='ko', order='viewCount'):
        results = []
        id_index_map = {vid: i for i, vid in enumerate(video_ids)}
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
                stats = item.get('statistics', {})
                title = snippet.get('title', '')
                description = snippet.get('description', '')
                vid_id = item.get('id')
                
                duration_str = content_details.get('duration')
                if not duration_str: continue
                try:
                    duration_seconds = isodate.parse_duration(duration_str).total_seconds()
                except: continue
                if duration_seconds > max_duration: continue

                is_valid, matched_kw, has_foreign_script = self.is_ai_content(
                    title, description, snippet.get('tags', []), snippet.get('channelTitle', '')
                )
                if not is_valid: 
                    continue

                # 언어 필터링 강화
                channel_title = snippet.get('channelTitle', '')
                has_hangul_title = bool(re.search(r'[\uac00-\ud7a3]', title))
                has_hangul_anywhere = bool(re.search(r'[\uac00-\ud7a3]', title + description + channel_title))
                
                if language == 'ko':
                    # 한국 영상 모드:
                    # 1. 힌디어나 아랍어 같은 외국 문자가 포함되어 있으면 즉시 제외
                    if has_foreign_script:
                        continue
                    
                    # 2. 제목에 한글이 반드시 포함되어야 함 (사용자 요청 사항)
                    if not has_hangul_title:
                        continue
                elif language == 'foreign':
                    # 외국 영상 모드: 한글이 포함된 영상은 제외
                    if has_hangul_anywhere:
                        continue
                # language == 'all' 이면 필터링 없음
                
                print(f"[*] Found AI-related: {title[:50]}... (KW: {matched_kw})")
                
                # 날짜 파싱 (예: 2024-03-06T...)
                pub_date = snippet.get('publishedAt', '')
                formatted_date = pub_date[:10] if pub_date else ''
                
                results.append({
                    "video_id": vid_id,
                    "title": title,
                    "channel": snippet.get('channelTitle'),
                    "view_count": int(stats.get('viewCount', 0)),
                    "duration_seconds": int(duration_seconds),
                    "thumbnail": snippet.get('thumbnails', {}).get('high', {}).get('url'),
                    "matched_keyword": matched_kw,
                    "published_at": formatted_date,
                    "url": f"https://www.youtube.com/watch?v={vid_id}" if duration_seconds > 60 else f"https://www.youtube.com/shorts/{vid_id}",
                    "original_index": id_index_map.get(vid_id, 999)
                })
        if order == 'viewCount':
            results.sort(key=lambda x: x['view_count'], reverse=True)
        else:
            results.sort(key=lambda x: x['original_index'])
        return results

    def get_trending_videos(self, max_duration=240, max_results=600, region_code='KR', language='ko'):
        if not self.youtube: return []
        
        all_results = []
        existing_ids = set()
        
        try:
            # 1단계: 실제 인기 급상승 차트 분석 (가장 신뢰도 높음)
            print(f"[*] Analyzing YouTube Trending Chart (Top {max_results})...")
            trending_ids = []
            next_page_token = None
            total_checked = 0
            while total_checked < max_results:
                request = self.youtube.videos().list(
                    part="id",
                    chart="mostPopular",
                    regionCode=region_code if region_code else 'KR',
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                items = response.get('items', [])
                if not items: break
                trending_ids.extend([item['id'] for item in items])
                total_checked += len(items)
                next_page_token = response.get('nextPageToken')
                if not next_page_token: break
                
            # 인기 차트 영상은 언어 필터를 적용하여 가져옴
            results_from_chart = self.get_video_details(trending_ids, max_duration, region_code, language=language, order='viewCount')
            for v in results_from_chart:
                if v['video_id'] not in existing_ids:
                    all_results.append(v)
                    existing_ids.add(v['video_id'])

            # 2단계: 결과가 부족할 경우(15개 미만), AI 쇼츠 전용 검색 쿼리 결합
            if len(all_results) < 15:
                print(f"[*] Found only {len(all_results)} from chart. Fetching supplemental AI shorts (Last 30 days)...")
                
                # 최근 30일 이내의 영상만 검색하도록 설정하여 "옛날 영상" 배제
                published_after = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                # 여러 키워드로 검색하여 풍성한 결과 확보 (최신순 결합)
                supplemental_queries = ["AI 애니메이션", "AI 쇼츠", "#shorts AI", "AI Shorts"]
                for query in supplemental_queries:
                    if len(all_results) >= 20: break # 충분히 모이면 종료
                    
                    search_results = self.get_search_results(
                        query=query,
                        max_duration=max_duration,
                        max_results=300, # 검색 깊이를 300으로 상향 (필터 통과 가능성 높임)
                        published_after=published_after, # 필터 추가
                        region_code=region_code,
                        language=language,
                        order='viewCount'
                    )
                    for v in search_results:
                        if v['video_id'] not in existing_ids:
                            all_results.append(v)
                            existing_ids.add(v['video_id'])

            # 조회수 순으로 재정렬
            all_results.sort(key=lambda x: x['view_count'], reverse=True)
            return all_results
            
        except Exception as e:
            print(f"Error in get_trending_videos: {e}")
            return all_results
