import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
from config import SMITHERY_API_KEY,GOOGLE_API_KEY
from datetime import datetime
import re
import base64

app_store_url = (
    "https://server.smithery.ai/@JiantaoFu/appinsightmcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)
amazon_url = (
    f"https://server.smithery.ai/@SiliconValleyInsight/amazon-product-search/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

bright_data_url = (
    f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)


youtube_config = {
    "youtubeTranscriptLang": "ko",
    "youtubeApiKey": GOOGLE_API_KEY
}
youtube_config_b64 = base64.b64encode(json.dumps(youtube_config).encode()).decode()
youtube_url = f"https://server.smithery.ai/@icraft2170/youtube-data-mcp-server/mcp?config={youtube_config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"



# 한국 App Store에서 "신규 인기 앱"
async def get_trending_new_app(url):
    answer = []
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            #🇰🇷 앱스토어 신규인기앱
            params = {
                "collection": "newapplications",
                "country": "kr",
                #"num": max_results,
            }
               
         
            result = await session.call_tool("app-store-list", params)
            apps = json.loads(result.content[0].text)
                
            if isinstance(apps, dict):
                apps = apps.get("apps", [])
            for i, app in enumerate(apps, 1):
                answer.append(f"{i}. {app.get('title')} | {app.get('genre')}")
    return "\n".join(answer)      


async def get_trending_amazon_products(url=amazon_url, max_results=20):
    answer = []
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            search_input = {
                "query": f"아마존 top {max_results} 트렌딩 상품이 뭐야?",
                "maxResults": max_results,
            }
            result = await session.call_tool("find_products_to_buy", search_input)
            result_text = result.content[0].text

            # 무조건 plain text 파서만 사용
            products = parse_amazon_plain_text_products(result_text, max_results=max_results)
            for idx, item in enumerate(products, 1):
                title = item.get("title", "제목없음")
                price = item.get("price", "(가격정보없음)")
               
                answer.append(
                    f"{idx}. {title} - 가격: {price}\n"
                )
    return "\n".join(answer)


async def get_trending_beautyshop(url, query, max_results=2):
    answer = []
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            today = datetime.now()
            params = {"query": query, "engine": "google"}
            search_result = await session.call_tool("search_engine", params)
            text = search_result.content[0].text

            url_pattern = re.compile(r"\(http[^)]+\)")
            url_candidates = url_pattern.findall(text)
            links = [s[1:-1] for s in url_candidates]

            try:
                links = links[6:] # 구글 부가링크 제외
                print(links)
                if len(links) < 1:
                    raise ValueError
            except Exception:
                return "\n[!] URL 추출을 위한 검색 결과가 너무 적습니다.\n검색어를 더 구체적으로 바꾸거나, 다른 키워드로 재시도해 주세요."

            # 2. 본문 수집 (에러 없는 2개까지)
            collected_texts = []
            count = 0
            for url_ in links:
                if count >= max_results:
                    break
                try:
                    scrape_result = await session.call_tool("scrape_as_markdown", {"url": url_})
                    if not getattr(scrape_result, "isError", False):
                        content = (scrape_result.content[0].text or '').strip()
                        if len(content)<=100:
                            continue
                        collected_texts.append(content)
                        count += 1
                except Exception as e:
                    continue

            if not collected_texts:
                return "[!] 본문 추출에 모두 실패했습니다. 질문이나 키워드를 바꿔보세요."

            all_content = "-----------------------------".join(collected_texts)
            all_content = re.sub(r'!\[.*?\]\([^)]+\)', '', all_content)
            all_content = re.sub(r'\(http[^)]+\)', '', all_content)
            all_content = re.sub(r'\n+', ' ', all_content)
            answer.append(all_content)
    return "\n".join(answer)

async def get_trending_youtube_videos(
    youtube_url: str,
    region_code: str = "KR",
    max_results: int = 10,
    category_id: int | None = None
) -> str:
  
    async with streamablehttp_client(youtube_url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            trending_input = {
                "regionCode": region_code,
                "maxResults": max_results,
            }
            if category_id is not None:
                trending_input["categoryId"] = str(category_id)

            trending_result = await session.call_tool("getTrendingVideos", trending_input)
            trending_json = trending_result.content[0].text
            trending_videos = json.loads(trending_json)

            video_ids = [item["id"] for item in trending_videos]
            details_result = await session.call_tool("getVideoDetails", {"videoIds": video_ids})
            details_json = details_result.content[0].text
            details_dict = json.loads(details_json)

            output_lines = []
            output_lines.append(f"🔥 유튜브 인기 영상 TOP {max_results} 상세\n")
            for rank, video_id in enumerate(video_ids, 1):
                detail = details_dict.get(video_id)
                if not detail:
                    output_lines.append(f"top{rank}. 정보 없음\n")
                    continue

                snippet    = detail.get("snippet", {})
                statistics = detail.get("statistics", {})
                content_details = detail.get("contentDetails", {})

                tags       = snippet.get("tags", [])
                title      = snippet.get("title")
                channel    = snippet.get("channelTitle")
                duration_iso = content_details.get("duration") or ""
                duration_str = parse_duration(duration_iso)
                description= snippet.get("description", "").strip()
                view       = statistics.get("viewCount")
                like       = statistics.get("likeCount")
                comment    = statistics.get("commentCount")
                published  = snippet.get("publishedAt")

                output_lines.append(
                    f"top{rank}. [{title}]\n"
                    f"채널: {channel}\n"
                    f"영상링크: https://youtube.com/watch?v={video_id}\n"
                    f"영상길이: {duration_str}\n"
                    f"태그: {', '.join(tags) if tags else '(없음)'}\n"
                    f"설명: {description}\n"
                    f"조회수: {view}\n"
                    f"좋아요수: {like}\n"
                    f"댓글수: {comment}\n"
                    f"업로드일: {published}\n"
                )

            return "\n".join(output_lines)


def parse_amazon_plain_text_products(raw_text, max_results=5):
    lines = raw_text.splitlines()
    products = []
    curr = {}
    for line in lines:
        line = line.strip()
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            if curr:
                products.append(curr)
                if len(products) >= max_results:
                    break
                curr = {}
            curr['title'] = m.group(2)
        elif line.startswith("Price:"):
            curr['price'] = line.replace("Price:", "").strip()
        elif line.startswith("Image:"):
            curr['image'] = line.replace("Image:", "").strip()
        elif line.startswith("Product Link:"):
            curr['product_url'] = line.replace("Product Link:", "").strip()
        elif line and not line.startswith("Found "):
            if 'short_desc' not in curr:
                curr['short_desc'] = line
    if curr and len(products) < max_results:
        products.append(curr)
    return products[:max_results]

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

def parse_duration(iso_duration):
    """ISO8601 PT#H#M#S → 'M분 S초' 또는 'H시간 M분 S초' 변환"""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not match:
        return "?"
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    if h:
        return f"{h}시간 {m}분 {s}초"
    return f"{m}분 {s}초" if m or s else "0초"

if __name__ == "__main__":
    # new_app_trend=asyncio.run(get_trending_new_app(app_store_url))
    # amazon_product_trend= asyncio.run(get_trending_amazon_products(amazon_url,max_results=10))
    query="2025년 네일샵 창업 트렌드"
    nail_trend = asyncio.run(get_trending_beautyshop(bright_data_url,query))
    # youtube_trend = asyncio.run(get_trending_youtube_videos(youtube_url))


    # 이걸 gpt에게 넘기기
    # print("💡 신규 인기앱 트렌드\n", new_app_trend)
    # print("\n💡 아마존 트렌드 상품\n", amazon_product_trend)
    print("\n💡 네일 트렌드\n", nail_trend) 
    # print("\n💡 유튜브 트렌드\n", youtube_trend)