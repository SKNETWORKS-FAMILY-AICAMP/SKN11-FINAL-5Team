# pip install "mcp[cli]"
# 도구 : Available tools: getVideoDetails, searchVideos, getTranscripts, getRelatedVideos, getChannelStatistics, getChannelTopVideos, getVideoEngagementRatio, getTrendingVideos, compareVideos

# getTrendingVideos → 인기 영상 목록 얻기
# getVideoDetails → 각 영상의 상세 태그/통계/설명까지 추가 조회



import mcp
from mcp.client.streamable_http import streamablehttp_client
import json
import base64
from config import GOOGLE_API_KEY, SMITHERY_API_KEY
import re

config = {
    "youtubeTranscriptLang": "ko",
    "youtubeApiKey": GOOGLE_API_KEY
}

config_b64 = base64.b64encode(json.dumps(config).encode()).decode()

url = f"https://server.smithery.ai/@icraft2170/youtube-data-mcp-server/mcp?config={config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"

YOUTUBE_CATEGORY_KR_DICT = {
    1:  "영화 및 애니메이션",
    2:  "자동차 및 차량",
    10: "음악",
    15: "반려동물 및 동물",
    17: "스포츠",
    19: "여행 및 이벤트",
    20: "게임",
    22: "인물 & 블로그",
    23: "코미디",
    24: "엔터테인먼트",
    25: "뉴스 및 정치",
    26: "Howto & Style (요리/스타일/먹방 등)",
    27: "교육",
    28: "과학 및 기술",
}

categoryId=None

def parse_duration(iso_duration):
    """ISO8601 PT#H#M#S → "M분 S초" 또는 "H시간 M분 S초" 변환"""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return "?"
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    if h:
        return f"{h}시간 {m}분 {s}초"
    return f"{m}분 {s}초" if m or s else "0초"


async def main():
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. 인기(트렌딩) 영상 TOP 5 가져오기
            trending_input = {
                "regionCode": "KR",
                "maxResults": 1,
            }

            if categoryId is not None:
                trending_input["categoryId"] = str(categoryId)

            trending_result = await session.call_tool("getTrendingVideos", trending_input)
            trending_json = trending_result.content[0].text
            trending_videos = json.loads(trending_json)

            # 2. videoId만 추출해서 getVideoDetails로 상세정보 받아오기
            video_ids = [item["id"] for item in trending_videos]
            details_result = await session.call_tool("getVideoDetails", {"videoIds": video_ids})
            details_json = details_result.content[0].text
            details_dict = json.loads(details_json) # dict(videoId → 상세정보)

            output_lines = []
            output_lines.append("🔥 유튜브 인기 영상 TOP 10 상세\n")
            for rank, video_id in enumerate(video_ids, 1):
                detail = details_dict.get(video_id)
                if not detail:
                    output_lines.append(f"top{rank}. 정보 없음\n")
                    continue

                snippet    = detail.get("snippet", {})
                statistics = detail.get("statistics", {})

                print("snippet",snippet)
                print("statistics",statistics)
                #contentDetails = detail.get("contentDetails", {})
                tags       = snippet.get("tags", [])
                title      = snippet.get("title")
                channel    = snippet.get("channelTitle")
                # duration_iso = detail.get("duration", "")
                # duration_str = parse_duration(duration_iso)
                description= snippet.get("description", "").strip()
                view       = statistics.get("viewCount")
                like       = statistics.get("likeCount")
                comment    = statistics.get("commentCount")
                published  = snippet.get("publishedAt")

                output_lines.append(
                    f"top{rank}. [{title}]\n"
                    f"채널: {channel}\n"
                    f"영상링크: https://youtube.com/watch?v={video_id}\n"
                    # f"영상길이: {duration_str}\n"
                    f"태그: {', '.join(tags) if tags else '(없음)'}\n"
                    f"설명: {description}\n"
                    f"조회수: {view}\n"
                    f"좋아요수: {like}\n"
                    f"댓글수: {comment}\n"
                    f"업로드일: {published}\n"
                )
            
            print("\n".join(output_lines))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
