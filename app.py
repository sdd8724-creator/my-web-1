import streamlit as st
import os
from datetime import datetime, timedelta, timezone
from trending_shorts_finder import YouTubeTrendingFinder

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="유튜브 트렌딩 파인더", layout="wide")
st.title("📺 YouTube Shorts 트렌딩 분석기")

# 2. API 키 설정 (스트림릿 Secrets 또는 환경 변수)
def load_api_key():
    # 1. Streamlit Secrets 확인 (Cloud 배포용)
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    
    # 2. .env 또는 시스템 환경 변수 확인 (로컬 실행용)
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("GOOGLE_API_KEY")

api_key = load_api_key()

if not api_key:
    st.error("API 키 설정이 올바르지 않습니다. .env 파일이나 스트림릿 Secrets를 확인해주세요.")
    st.stop()

# API 키를 환경 변수로 설정하여 Finder에서 인식하게 함
os.environ["GOOGLE_API_KEY"] = api_key
try:
    finder = YouTubeTrendingFinder()
except Exception as e:
    st.error(f"YouTube 서비스 초기화 중 오류: {e}")
    st.stop()

# 3. 사이드바 - 설정창
st.sidebar.header("🔍 검색 설정")
mode = st.sidebar.radio("작동 모드", ["인기 급상승(Trending)", "직접 검색(Search)"])

search_query = "AI 애니메이션"
if mode == "직접 검색(Search)":
    search_query = st.sidebar.text_input("검색어 입력", value="AI 애니메이션")

period = st.sidebar.selectbox("기간 설정", ["all", "today", "week", "month"])
sort_order = st.sidebar.selectbox("정렬 기준", ["viewCount", "relevance", "date"])
max_duration = st.sidebar.slider("최대 영상 길이 (초)", 10, 600, 240)

# 4. 분석 실행 버튼
if st.sidebar.button("분석 시작하기"):
    region_code = 'KR'
    published_after = None
    
    # 날짜 계산 로직 (기존 코드 유지)
    if mode == "직접 검색(Search)" and period != 'all':
        now = datetime.now(timezone.utc)
        if period == 'today':
            delta = timedelta(days=1)
        elif period == 'week':
            delta = timedelta(days=7)
        elif period == 'month':
            delta = timedelta(days=30)
        else:
            delta = None
        
        if delta:
            published_after = (now - delta).strftime('%Y-%m-%dT%H:%M:%SZ')

    with st.spinner("유튜브 데이터를 가져오는 중입니다..."):
        try:
            if mode == "직접 검색(Search)":
                search_depth = 300
                results = finder.get_search_results(
                    query=search_query,
                    max_duration=max_duration,
                    max_results=search_depth,
                    published_after=published_after,
                    region_code=region_code,
                    language='ko',
                    order=sort_order
                )
            else:
                results = finder.get_trending_videos(
                    max_duration=max_duration,
                    region_code=region_code,
                    language='ko'
                )

            # 5. 결과 출력
            st.success(f"총 {len(results)}개의 영상을 찾았습니다!")
            
            if results:
                for idx, video in enumerate(results):
                    with st.container():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(video.get('thumbnail', ''), use_container_width=True)
                        with col2:
                            st.subheader(video.get('title', '제목 없음'))
                            st.write(f"채널: {video.get('channel', '알 수 없음')}")
                            st.write(f"조회수: {video.get('view_count', 0):,}회 | {video.get('published_at', '')} 업로드")
                            st.video(f"https://www.youtube.com/watch?v={video.get('video_id')}")
                        st.divider()
            else:
                st.info("검색 결과가 없습니다.")
                
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

else:
    st.info("왼쪽 설정창에서 조건을 선택하고 '분석 시작하기' 버튼을 눌러주세요.")