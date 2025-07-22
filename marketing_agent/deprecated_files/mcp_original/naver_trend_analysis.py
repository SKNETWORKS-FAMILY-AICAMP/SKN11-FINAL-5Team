"""네이버 검색어 및 쇼핑 카테고리 트렌드 분석 스크립트"""

import os
import mcp
import json
import base64
import asyncio
import re
import sys
from datetime import datetime
from mcp.client.streamable_http import streamablehttp_client

def validate_input(start_date: str, end_date: str, time_unit: str) -> bool:
    if not re.match(r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$', start_date) or \
       not re.match(r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$', end_date):
        return False
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_diff = (end - start).days
        return start <= end and 7 <= date_diff <= 365 and time_unit.lower() in ['date', 'week', 'month']
    except ValueError:
        return False
def get_config() -> dict:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / 'unified_agent_system' / '.env')
    return {
        'naver_client_id': os.getenv('NAVER_CLIENT_ID'),
        'naver_client_secret': os.getenv('NAVER_CLIENT_SECRET'),
        'smithery_api_key': os.getenv('SMITHERY_API_KEY')
    }

env_config = get_config()
config_b64 = base64.b64encode(json.dumps({
    "NAVER_CLIENT_ID": env_config['naver_client_id'],
    "NAVER_CLIENT_SECRET": env_config['naver_client_secret']
}).encode()).decode()
url = f"https://server.smithery.ai/@isnow890/naver-search-mcp/mcp?config={config_b64}&api_key={env_config['smithery_api_key']}&profile=realistic-possum-fgq4Y7"

async def analyze_search_trends(session, start_date: str, end_date: str, time_unit: str = 'month'):
    return await session.call_tool("datalab_search", {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {"groupName": "네일아트", "keywords": ["네일아트", "젤네일", "네일디자인"]},
            {"groupName": "속눈썹", "keywords": ["속눈썹연장", "속눈썹펌", "속눈썹영양제"]}
        ]
    })


async def main():
    today = datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    time_unit = 'month'

    if not validate_input(start_date, end_date, time_unit):
        print("[Error] 입력값이 올바르지 않습니다.")
        return

    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            try:
                search_result = await analyze_search_trends(session, start_date, end_date, time_unit)
                if search_result and not search_result.isError:
                    data = json.loads(search_result.content[0].text)
                    for group in data.get("results", []):
                        print(f"\n■ {group['title']} 트렌드 분석")
                        for period in group.get("data", []):
                            print(f"  - {period['period']}: {period['ratio']}%")
            except Exception as ex:
                print(f"\n[Error] 분석 실패: {str(ex)}")

if __name__ == '__main__':
    asyncio.run(main())