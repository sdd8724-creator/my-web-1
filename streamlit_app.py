import streamlit as st
import os
import re
from datetime import datetime, timedelta, timezone
from trending_shorts_finder import YouTubeTrendingFinder

# 페이지 설정 (모바일 최적화 및 타이틀)
st.set_page_config(
    page_title="YouTube AI Content Finder",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (모바일 대응 및 디자인)
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .video-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .video-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 10px;
        color: #f8fafc;
    }
    .channel-name {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    .ai-tag {
        background: rgba(99, 102, 241, 0.2);
        color: #a5b4fc;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    @media (max-width: 640px) {
        .video-title { font-size: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# API 키 및 세션 상태 초기화
@st.cache_resource
def get_finder():
    # st.secrets에서 API 키 로드 (없으면 환경변수 시도)
    api_key = st.secrets.get("secrets", {}).get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("API Key가 설정되지 않았습니다. st.secrets 또는 .env를 확인해주세요.")
        return None
    
    # YouTubeTrendingFinder 인스턴스 생성 시 API 키 직접 전달
    # (내부적으로 os.getenv를 쓰기도 하지만, 명확성을 위해 직접 전달하거나 환경변수 강제 설정)
    os.environ["GOOGLE_API_KEY"] = api_key
    finder = YouTubeTrendingFinder()
    if not finder.youtube:
        st.error("YouTube API 연결에 실패했습니다. API 키를 확인해주세요.")
    return finder

finder = get_finder()
if finder:
    st.sidebar.success("✅ API Connected")
else:
    st.sidebar.error("❌ API Not Connected")

# 헤더
st.title("🎬 YouTube AI Content Finder")
st.markdown("대한민국 인기 급상승 영상 및 키워드 기반 AI 콘텐츠를 탐색합니다.")

# 사이드바 설정
st.sidebar.header("🔍 탐색 설정")
mode = st.sidebar.radio("탐색 모드", ["인기 급상승", "키워드 검색"])
language = st.sidebar.radio("영상 언어", ["한국 영상", "외국 영상", "전체(Global)"], index=0)

search_query = "AI 애니메이션"
period = "최근 1개월"
sort_order = "인기순"

if mode == "키워드 검색":
    search_query = st.sidebar.text_input("검색 키워드", value="AI 애니메이션")
    period = st.sidebar.selectbox("검색 기간", ["전체 기간", "지난 24시간", "최근 1주일", "최근 1개월"])
    sort_order = st.sidebar.selectbox("정렬 기준", ["인기순", "최신순"])

max_duration = st.sidebar.slider("최대 영상 길이 (초)", 10, 600, 240)

# 검색 버튼 및 로직
if st.sidebar.button("탐색 시작"):
    if not finder:
        st.stop()
        
    with st.spinner("유튜브 데이터를 분석 중입니다... 잠시만 기다려주세요."):
        # 파라미터 변환
        period_map = {"전체 기간": "all", "지난 24시간": "today", "최근 1주일": "week", "최근 1개월": "month"}
        sort_map = {"인기순": "viewCount", "최신순": "date"}
        lang_map = {"한국 영상": "ko", "외국 영상": "foreign", "전체(Global)": "all"}
        
        published_after = None
        if mode == "키워드 검색" and period_map[period] != 'all':
            now = datetime.now(timezone.utc)
            delta_map = {"today": 1, "week": 7, "month": 30}
            delta = timedelta(days=delta_map[period_map[period]])
            published_after = (now - delta).strftime('%Y-%m-%dT%H:%M:%SZ')

        # 데이터 가져오기
        if mode == "키워드 검색":
            results = finder.get_search_results(
                query=search_query,
                max_duration=max_duration,
                max_results=300,
                published_after=published_after,
                region_code='KR',
                language=lang_map[language],
                order=sort_map[sort_order]
            )
        else:
            results = finder.get_trending_videos(
                max_duration=max_duration,
                region_code='KR',
                language=lang_map[language]
            )

        # 결과 표시
        if not results:
            st.warning("검색 결과가 없습니다. 조건을 변경해보세요.")
        else:
            st.success(f"총 {len(results)}개의 콘텐츠를 발견했습니다!")
            
            # 2열 레이아웃
            cols = st.columns(2)
            for idx, video in enumerate(results):
                with cols[idx % 2]:
                    st.markdown(f"""
                        <div class="video-card">
                            <a href="{video['url']}" target="_blank" style="text-decoration:none;">
                                <img src="{video['thumbnail']}" style="width:100%; border-radius:10px;">
                                <div class="video-title">{video['title']}</div>
                                <div class="channel-name">{video['channel']} | 조회수 {video['view_count']:,}회</div>
                                <div style="font-size:0.75rem; color:#94a3b8; margin-top:5px;">{video['published_at']} 업로드</div>
                                <div style="margin-top:10px;">
                                    <span class="ai-tag">#{video['matched_keyword']}</span>
                                </div>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)

else:
    st.info("왼쪽 사이드바에서 조건을 설정하고 '탐색 시작'을 눌러주세요.")

# 푸터
st.markdown("---")
st.caption("Powered by Streamlit & YouTube Data API v3")
