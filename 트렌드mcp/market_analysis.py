import mcp
from mcp.client.streamable_http import streamablehttp_client
from config import bright_data_url,naver_url
from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio
import re


today=datetime.now()
min_date = today - relativedelta(years=1,months=6)

# what : 창업 트렌드/시장규모/고객유형/경쟁사
async def get_market_analysis(url,persona, what, max_results=2):
    answer = []
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            today = datetime.now()
            params = {"query": f"{persona} {what}", "engine": "google", "min_date": min_date}
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

            all_content = "⎯⎯ 다음 자료 ⎯⎯".join(collected_texts)
            all_content = re.sub(r'!\[.*?\]\([^)]+\)', '', all_content)
            all_content = re.sub(r'\(http[^)]+\)', '', all_content)
            all_content = re.sub(r'\n+', ' ', all_content)
            answer.append(all_content)
    return "\n".join(answer)





# market_size= asyncio.run(get_market_analysis(bright_data_url,"네일샵","시장분석"))
# print(market_size)


