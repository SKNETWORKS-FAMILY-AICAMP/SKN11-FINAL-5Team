# Available tools: find_products_to_buy, shop_for_items, get_product_details, get_search_options, get_cache_stats, clear_cache
# 


import mcp
from mcp.client.streamable_http import streamablehttp_client
from collections import defaultdict
import json
import re
from config import SMITHERY_API_KEY

url = (
    f"https://server.smithery.ai/@SiliconValleyInsight/amazon-product-search/mcp"
    f"?api_key={SMITHERY_API_KEY}&profile=blank-tahr-7BPYtb"
)

def parse_amazon_plain_text_products(raw_text, max_results=5):
    """
    아마존 MCP 서버에서 받은 plain text(1. 상품명 ... Price: ... 등) 파싱 함수
    """
    lines = raw_text.splitlines()
    products = []
    curr = {}
    for line in lines:
        line = line.strip()
        m = re.match(r"^(\d+)\.\s+(.*)", line)
        if m:
            if curr:  # 이전 상품 저장
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
            # 기타 줄 (설명 등)
            # 필요시 short_desc로 구성
            if 'short_desc' not in curr:
                curr['short_desc'] = line
    # 마지막 상품 추가
    if curr and len(products) < max_results:
        products.append(curr)
    return products[:max_results]

async def main():
    max_results = 20

    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            search_input = {
                "query": "아마존 top 20 트렌딩 상품이 뭐야?",   
                "maxResults": max_results
            }
            result = await session.call_tool("find_products_to_buy", search_input)
            
            # MCP 서버는 text/plain으로 결과를 반환(대부분 JSON이 아님)
            result_text = result.content[0].text

            # 먼저 JSON 여부 체크
            try:
                product_list = json.loads(result_text)
            except Exception:
                product_list = None

            output_lines = ["🔥 아마존 top 20 트렌딩 상품", ""]
            if product_list and isinstance(product_list, list):
                # JSON 리스트로 온 경우 (거의 없음)
                for idx, item in enumerate(product_list, 1):
                    title = item.get("title", "제목없음")
                    price = item.get("price", "(가격정보없음)")
                    product_url = item.get("url", "(링크없음)")
                    short_desc = item.get("shortDescription", "")
                    output_lines.append(
                        f"{idx}. {title}\n"
                        f"   - 가격: {price}\n"
                        f"   - 상품설명: {short_desc}\n"
                        f"   - 상품링크: {product_url}\n"
                    )
            else:
                # plain text 파서 활용 (이 케이스가 대부분!)
                products = parse_amazon_plain_text_products(result_text, max_results=max_results)
                for idx, item in enumerate(products, 1):
                    title = item.get("title", "제목없음")
                    price = item.get("price", "(가격정보없음)")
                    product_url = item.get("product_url", "(링크없음)")
                    image_url = item.get("image", "")
                    short_desc = item.get("short_desc", "")
                    output_lines.append(
                        f"{idx}. {title}\n"
                        f"   - 가격: {price}\n"
                        f"   - 상품설명: {short_desc}\n"
                        f"   - 상품링크: {product_url}\n"
                        f"   - 이미지: {image_url}\n"
                    )
            print("\n".join(output_lines))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
