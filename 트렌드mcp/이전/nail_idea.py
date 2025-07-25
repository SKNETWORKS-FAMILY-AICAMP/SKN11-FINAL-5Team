import re
import asyncio
import mcp
from mcp.client.streamable_http import streamablehttp_client
from config import SMITHERY_API_KEY
from datetime import datetime

base_url = (
    f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

def get_season(month):
    # 월에 따라 봄/여름/가을/겨울 반환
    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:  # 12, 1, 2
        return "겨울"
    
async def main():
    async with streamablehttp_client(base_url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            today = datetime.now()
            season = get_season(today.month)
            query = f"{today.year}년 {season} 네일 트렌드"
            params = {"query": query, "engine": "google"}
            search_result = await session.call_tool("search_engine", params)
            text = search_result.content[0].text

            # 1. URL 추출 및 필터링
            url_pattern = re.compile(r"\(http[^)]+\)")
            url_candidates = url_pattern.findall(text)
            links = [s[1:-1] for s in url_candidates]

            try:
                links = links[6:] # 구글 부가링크 제외
                if len(links) < 1:
                    raise ValueError
            except Exception:
                print("\n[!] URL 추출을 위한 검색 결과가 너무 적습니다.")
                print("검색어를 더 구체적으로 바꾸거나, 다른 키워드로 재시도해 주세요.")
                return

            # 2. 본문 수집 (에러 없는 3개까지)
            collected_texts = []
            valid = 2
            valid_count = 0
            for url in links:
                if valid_count >= valid:
                    break
                try:
                    scrape_result = await session.call_tool("scrape_as_markdown", {"url": url})
                    if not getattr(scrape_result, "isError", False):
                        content = (scrape_result.content[0].text or '').strip()
                        collected_texts.append(content)
                        valid_count += 1
                    else:
                        raise Exception("본문 추출 에러(사이트 차단/403 등)")
                except Exception as e:
                    print(f"[본문 추출 오류] {url} :: {e}")

            # 3. 결과 출력
            all_content = "-----------------------------".join(collected_texts)
            all_content = re.sub(r'!\[.*?\]\([^)]+\)', '', all_content)
            all_content = re.sub(r'\(http[^)]+\)', '', all_content)
            all_content = re.sub(r'\n+', ' ', all_content)
            
            # 결과
            print(all_content)

if __name__ == "__main__":
    asyncio.run(main())
