import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
from config import SMITHERY_API_KEY

url = (
    "https://server.smithery.ai/@JiantaoFu/appinsightmcp/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)


# 한국 App Store에서 "신규 인기 앱", "인기 무료 앱", "인기 유료 앱"
async def main():
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("🇰🇷 앱스토어 트렌드 TOP20 (신규/무료/유료)\n")

            queries = [
                {
                    "label": "신규 인기앱",
                    "params": {
                        "collection": "newapplications",
                        "country": "kr",
                    }
                },
                {
                    "label": "인기 무료 앱",
                    "params": {
                        "collection": "topfreeapplications",
                        "country": "kr",
                        "num": 20,
                    }
                },
                {
                    "label": "인기 유료 앱",
                    "params": {
                        "collection": "toppaidapplications",
                        "country": "kr",
                        "num": 20,
                    }
                },
            ]

            for query in queries:
                print(f"## {query['label']}")
                result = await session.call_tool("app-store-list", query["params"])
                apps = json.loads(result.content[0].text)
                
                if isinstance(apps, dict):
                    apps = apps.get("apps", [])
                for i, app in enumerate(apps, 1):
                    print(f"{i}. {app.get('title')} | {app.get('genre')}") #| 개발자: {app.get('developer')}")
                print("\n")

if __name__ == "__main__":
    asyncio.run(main())
