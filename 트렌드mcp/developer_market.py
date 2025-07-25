import mcp
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json
from config import SMITHERY_API_KEY

url = f"https://server.smithery.ai/@AudienseCo/mcp-audiense-di-linkedin/mcp?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"

# 오디언스/기준군 정의 (실제 facet 값은 Typeahead로 보완 가능)
audience_def = {
    "include": {
        "and": [
            {"or": {"urn:li:adTargetingFacet:titles": ["Software Engineer", "Developer"]}},
            {"or": {"urn:li:adTargetingFacet:locations": ["South Korea", "대한민국"]}}
        ]
    }
}
baseline_def = {
    "include": {
        "and": [
            {"or": {"urn:li:adTargetingFacet:titles": ["Software Engineer", "Developer"]}}
        ]
    }
}
report_title = "Korean Solo Developer Market"

async def main():
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            # 리포트 생성
            req = {
                "title": report_title,
                "audienceDefinition": audience_def,
                "baselineDefinition": baseline_def
            }
            result = await session.call_tool("create-linkedin-report", req)
            print(result)
           

if __name__ == "__main__":
    asyncio.run(main())
