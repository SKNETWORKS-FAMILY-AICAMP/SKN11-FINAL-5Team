import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
from config import SMITHERY_API_KEY
from datetime import datetime
import re
import base64

#  SMITHERY_API_KEY = e94738a7-0a18-43a1-9674-8378d161b423
bright_data_url = (
    f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

def get_season(month):
    if month in [3, 4, 5]:      return "봄"
    elif month in [6, 7, 8]:    return "여름"
    elif month in [9, 10, 11]:  return "가을"
    else:                       return "겨울"


async def get_trending_nail_trend(url, max_results=2):
    answer = []
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            today = datetime.now()
            season = get_season(today.month)
            query = f"{today.year}년 {season} 네일 트렌드"
            params = {"query": query, "engine": "google"}
            search_result = await session.call_tool("search_engine", params)
            text = search_result.content[0].text

            url_pattern = re.compile(r"\(http[^)]+\)")
            url_candidates = url_pattern.findall(text)
            links = [s[1:-1] for s in url_candidates]

            try:
                links = links[6:] # 구글 부가링크 제외
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


if __name__ == "__main__":
    nail_trend = asyncio.run(get_trending_nail_trend(bright_data_url))
  

    # 이걸 gpt에게 넘기기
    print("\n💡 네일 트렌드\n", nail_trend) 
   