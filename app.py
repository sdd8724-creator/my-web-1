from flask import Flask, render_template, request, jsonify
import os
from trending_shorts_finder import YouTubeTrendingFinder

app = Flask(__name__)
finder = YouTubeTrendingFinder()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    is_connected = finder.youtube is not None
    return jsonify({
        "status": "success" if is_connected else "error",
        "is_connected": is_connected
    })

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    mode = data.get('mode', 'trending') # 'trending' or 'search'
    search_query = data.get('search_query', 'AI 애니메이션')
    period = data.get('period', 'all') # 'all', 'today', 'week', 'month'
    region = 'KR' # 항상 한국 지역으로 고정
    sort_order = data.get('sort_order', 'viewCount')
    max_duration = int(data.get('max_duration', 240))
    use_ai_filter = data.get('use_ai_filter', True)
    exclude_music = data.get('exclude_music', True)
    language = data.get('language', 'ko') # 'ko', 'foreign', 'all'
    
    from dotenv import load_dotenv
    load_dotenv()
    
    region_code = 'KR'
    published_after = None
    if mode == 'search' and period != 'all':
        from datetime import datetime, timedelta, timezone
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
            # YouTube API requires RFC 3339 format (no timezone offset like +00:00)
            published_after = (now - delta).strftime('%Y-%m-%dT%H:%M:%SZ')
            
    if mode == 'search':
        search_depth = 300
        results = finder.get_search_results(
            query=search_query,
            max_duration=max_duration,
            max_results=search_depth,
            published_after=published_after,
            region_code=region_code,
            language=language,
            order=sort_order
        )
    else:
        results = finder.get_trending_videos(
            max_duration=max_duration,
            region_code=region_code,
            language=language
        )
    
    return jsonify({
        "status": "success",
        "count": len(results),
        "results": results
    })

