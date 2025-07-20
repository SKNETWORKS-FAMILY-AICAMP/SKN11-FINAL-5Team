import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json

SMITHERY_API_KEY = "056f88d0-aa2e-4ea9-8f2d-382ba74dcb07"
PROFILE = "realistic-possum-fgq4Y7"

# LinkedIn MCP Server
LINKEDIN_MCP_URL = (
    f"https://server.smithery.ai/@horizondatawave/hdw-mcp-server/mcp?"
    f"api_key={SMITHERY_API_KEY}&profile={PROFILE}"
)

# -------------------------------
# 1. LinkedIn 사용자 검색
# -------------------------------
async def search_linkedin_users(keywords: str = None, count: int = 5, title: str = None, 
                            industry: str = None, name: str = None, location: str = None):
    # 검색 파라미터 구성
    search_params = {
        "count": count
    }
    
    # 선택적 파라미터 추가
    if keywords:
        search_params["keywords"] = keywords
    if title:
        search_params["title"] = title
    if industry:
        search_params["industry"] = industry
    if name:
        search_params["name"] = name
    if location:
        search_params["location"] = location

    async with streamablehttp_client(LINKEDIN_MCP_URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_linkedin_users",
                search_params
            )
            return result

# -------------------------------
# 2. 특정 사용자의 포스트 조회
# -------------------------------
async def get_linkedin_user_posts(urn: str, count: int = 5):
    async with streamablehttp_client(LINKEDIN_MCP_URL) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_linkedin_user_posts",
                {"urn": urn, "count": count}
            )
            return result

# -------------------------------
# 3. 전체 플로우 실행
# -------------------------------
async def marketing_flow(keywords: str = None, title: str = None, industry: str = None, 
                      name: str = None, location: str = None, count: int = 5):
    # 검색 조건 출력
    print("\n🔍 [Step 1] LinkedIn 사용자 검색:")
    if keywords: print(f"  키워드: '{keywords}'")
    if title: print(f"  직함: '{title}'")
    if industry: print(f"  산업: '{industry}'")
    if name: print(f"  이름: '{name}'")
    if location: print(f"  위치: '{location}'")
    
    users_result = await search_linkedin_users(
        keywords=keywords,
        title=title,
        industry=industry,
        name=name,
        location=location,
        count=count
    )

    # 사용자 목록 파싱
    if not hasattr(users_result, 'content') or not users_result.content:
        print("❌ 사용자 검색 결과가 없습니다.")
        return

    users = json.loads(users_result.content[0].text)
    if not users:  # 검색 결과가 비어있는 경우
        print("❌ 키워드와 일치하는 사용자를 찾을 수 없습니다.")
        return

    for idx, user in enumerate(users, start=1):
        print(f"\n[{idx}] {user['name']} - {user.get('headline', '')}")
        print(f"URL: {user['url']}")
        print(f"URN: {user['urn']['type']}:{user['urn']['value']}")

    # 모든 사용자의 포스트 가져오기
    print("\n📝 [Step 2] 사용자들의 최신 포스트 조회")
    for user in users:
        user_urn = f"{user['urn']['type']}:{user['urn']['value']}"
        print(f"\n👤 {user['name']}의 포스트:")
        
        posts_result = await get_linkedin_user_posts(user_urn, count=5)
        
        if not hasattr(posts_result, 'content') or not posts_result.content:
            print("  ❌ 포스트 결과가 없습니다.")
            continue

        posts = json.loads(posts_result.content[0].text)
        for i, post in enumerate(posts, start=1):
            text = post.get("text", "내용 없음")
            url = post.get("url", "URL 없음")
            print(f"\n  ▶ 포스트 {i}: {text}")
            print(f"     URL: {url}")

# -------------------------------
# 실행
# -------------------------------
if __name__ == "__main__":
    # 예시: 게임 산업의 모바일 게임 관련 직함을 가진 사용자 검색
    asyncio.run(marketing_flow(
        keywords="mobile gaming",
        title="game developer",
        industry="Gaming",
        location="United States",
        count=5
    ))
