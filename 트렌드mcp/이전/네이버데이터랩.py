# import mcp
# from mcp.client.streamable_http import streamablehttp_client
# import json, base64, asyncio
# from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, SMITHERY_API_KEY
# from datetime import datetime

# config = {
#     "NAVER_CLIENT_ID": NAVER_CLIENT_ID,
#     "NAVER_CLIENT_SECRET": NAVER_CLIENT_SECRET
# }
# config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
# url = (
#     f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp"
#     f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
# )

# async def main():
#     today = datetime.now()
#     year, month = today.year, today.month
#     date_str = f"{year}년 {month}월 네일아트 트렌드"

#     async with streamablehttp_client(url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()
#             queries = [
#                 ("search_blog", {"query": date_str}),
#                 ("datalab_search", {
#                     "startDate": f"{year}-{str(month).zfill(2)}-01",
#                     "endDate": today.strftime("%Y-%m-%d"),
#                     "timeUnit": "month",
#                     "keywordGroups": [
#                         {"groupName": "네일아트", "keywords": ["네일아트"]},
#                         {"groupName": "젤네일", "keywords": ["젤네일"]},
#                         {"groupName": "시럽네일", "keywords": ["시럽네일"]}
#                     ],
#                     "device": "pc",
#                 }),
#             ]
#             results = []
#             for tool_name, payload in queries:
#                 try:
#                     result = await session.call_tool(tool_name, payload)
#                     results.append((tool_name, result))
#                 except Exception as ex:
#                     results.append((tool_name, f"Error: {ex}"))

#             for tool_name, result in results:
#                 print(f"\n[== {tool_name} 결과 ==]")
#                 try:
#                     if hasattr(result, "content") and result.content:
#                         text = result.content[0].text
#                         # datalab_search 원본 전체 출력
#                         if tool_name == "datalab_search":
#                             print("Raw datalab_search response:")
#                             print(text)
#                         if tool_name == "datalab_search":
#                             res = json.loads(text)
#                             if "results" in res:
#                                 for group in res["results"]:
#                                     print(f"\n■ {group.get('groupName', 'no groupName')}")
#                                     for point in group.get("data", []):
#                                         print(f"{point.get('period', '')}: {point.get('ratio', '')}")
#                             else:
#                                 print("No 'results' key in datalab_search response")
#                         else:
#                             parsed = json.loads(text)
#                             for item in parsed.get("items", [])[:5]:
#                                 print(f"[{item.get('postdate', item.get('pubDate', ''))}] {item['title']}")
#                                 print(f" > {item.get('description', '')}\n > {item['link']}\n")
#                     else:
#                         print(result)
#                 except Exception as ex:
#                     print(f"Error parsing result: {ex}")

# if __name__ == "__main__":
#     asyncio.run(main())
##########################################################################




# ## 실패!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 본문 안긁힘


# import mcp
# from mcp.client.streamable_http import streamablehttp_client
# import json, base64, asyncio
# from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, SMITHERY_API_KEY

# # MCP 공통 설정 (네이버 오픈API 인증 정보)
# config = {
#     "NAVER_CLIENT_ID": NAVER_CLIENT_ID,
#     "NAVER_CLIENT_SECRET": NAVER_CLIENT_SECRET
# }
# config_b64 = base64.b64encode(json.dumps(config).encode()).decode()

# # 1. 네이버 검색 MCP 주소 (검색 결과 요약/링크용)
# naver_search_url = (
#     f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp"
#     f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
# )

# # 2. brightdata 크롤링 MCP 주소 (본문 추출용)
# scraper_url = (
#     f"https://server.smithery.ai/@luminati-io/brightdata-mcp/mcp"
#     f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
# )

# async def main():
#     # 1단계: 네이버 블로그 링크 및 요약 추출
#     async with streamablehttp_client(naver_search_url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()
#             search_result = await session.call_tool("search_blog", {"query": "네일아트 트렌드"})
#             blog_json = json.loads(search_result.content[0].text)
#             blog_items = blog_json.get("items", [])[:5]
#             blog_links = [(item['title'], item['link']) for item in blog_items]

#             print("------ 상위 5개 네이버 블로그 (제목/요약/링크) ------")
#             for item in blog_items:
#                 print(f"[{item['postdate']}] {item['title']}")
#                 print(f" > {item['description']}\n > {item['link']}\n")

#     # 2단계: brightdata MCP로 블로그 본문 크롤링
#     async with streamablehttp_client(scraper_url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()
#             print("\n------ 각 블로그 본문 스크랩 결과 ------")
#             for idx, (title, link) in enumerate(blog_links, 1):
#                 print(f'\n[{idx}] {title}\n{link}')
#                 try:
#                     scrape_result = await session.call_tool("scrape_as_markdown", {"url": link})
#                     text = ""
#                     if hasattr(scrape_result, "content") and scrape_result.content:
#                         text = scrape_result.content[0].text.strip()
                 
#                     print(text)
#                 except Exception as ex:
#                     print(f"[본문 추출 오류] {ex}")

# if __name__ == "__main__":
#     asyncio.run(main())


# import mcp
# from mcp.client.streamable_http import streamablehttp_client
# import json, base64, asyncio
# from datetime import datetime
# from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, SMITHERY_API_KEY

# config = {
#     "NAVER_CLIENT_ID": NAVER_CLIENT_ID,
#     "NAVER_CLIENT_SECRET": NAVER_CLIENT_SECRET
# }
# config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
# url = (
#     f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp"
#     f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
# )

# async def main():
#     today = datetime.now()
#     start_date = today.replace(day=1).strftime('%Y-%m-%d')
#     end_date = today.strftime('%Y-%m-%d')

#     # 1. 네일아트 카테고리코드(대표: "50002151" = 네일케어/네일아트 소분류, 필요시 코드 재확인)
#     # 속눈썹: 50004395
    
#     category_code = "50002151"

#     async with streamablehttp_client(url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()

#             # 쇼핑분야 인기 키워드 트렌드 분석 요청
#             try:
#                 res = await session.call_tool("datalab_shopping_keywords", {
#                     "startDate": start_date,
#                     "endDate": end_date,
#                     "timeUnit": "month",
#                     "category": category_code,
#                 })
#                 print(res)
#                 # text = res.content[0].text
#                 # print(f"API 응답 원문: {text!r}")

#             #     js = json.loads(text)
#             #     print("\n[네이버쇼핑 네일아트 인기 키워드 & 트렌드 순위]")
#             #     # 응답의 구조 예: {"results": [{"title": 키워드명, "keywords": [ ... ] }]}
#             #     if "results" in js:
#             #         for r in js["results"]:
#             #             print(f"■ [{r['title']}] 인기 키워드 Top10")
#             #             for idx, kw in enumerate(r.get("keywords", [])[:10], 1):
#             #                 # 보통 "keyword","ratio" 등 필드 있음
#             #                 if isinstance(kw, dict):
#             #                     print(f"{idx}. {kw.get('keyword', kw.get('name',''))} (비중: {kw.get('ratio','')})")
#             #                 else:
#             #                     print(f"{idx}. {kw}")
#             #     else:
#             #         print("결과에 'results'가 없습니다. 응답 내용:", js)
#             except Exception as ex:
#                 print(f"분석 실패: {ex}")

# if __name__ == "__main__":
#     asyncio.run(main())


############################
#실패
# import mcp
# from mcp.client.streamable_http import streamablehttp_client
# from config import bright_data_url,naver_url
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# import asyncio
# import re
# import json

# async def get_naver_shopping_trends(
#     keyword="네일아트", 
#     category_code="50000623", 
#     time_unit="month", 
#     ages=None, 
#     gender="all"
# ):
#     """
#     네이버 쇼핑 키워드의 성별 및 연령별 트렌드 자료를 크롤링해 반환합니다.
#     """
#     today = datetime.now()
#     start_date = f"{today.year}-{str(today.month).zfill(2)}-01"
#     end_date = today.strftime("%Y-%m-%d")
#     if ages is None:
#         ages = ["10", "20", "30", "40", "50"]

#     async with streamablehttp_client(naver_url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()

#             gender_payload = {
#                 "gender": gender,  # "f"(여성), "m"(남성), "all"(전체)
#                 "startDate": start_date,
#                 "endDate": end_date,
#                 "keyword": keyword,
#                 "category": category_code,
#                 "timeUnit": time_unit,
#             }
#             gender_result = await session.call_tool("datalab_shopping_keyword_by_gender", gender_payload)

#             age_payload = {
#                 "ages": ages,
#                 "startDate": start_date,
#                 "endDate": end_date,
#                 "keyword": keyword,
#                 "category": category_code,
#                 "timeUnit": time_unit,
#             }
#             age_result = await session.call_tool("datalab_shopping_keyword_by_age", age_payload)

#             print("\n[== 쇼핑 키워드 성별 트렌드 ==]")
#             print(gender_result)
#             print("\n[== 쇼핑 키워드 연령별 트렌드 ==]")
#             print(age_result)

# if __name__ == "__main__":
#     asyncio.run(get_naver_shopping_trends())