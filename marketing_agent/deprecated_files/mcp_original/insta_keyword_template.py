import mcp
from mcp.client.streamable_http import streamablehttp_client
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from shared_modules.llm_utils import get_llm
import json
import base64

async def extract_hashtags_from_question(question: str):
    # LLM을 사용하여 키워드 추출
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 사용자의 질문에서 해시태그를 추출하는 전문가야. 콤마(,)로 구분된 키워드만 출력하고, 설명은 하지마. 비슷한 키워드로 5개 생성해줘."),
        ("human", f"다음 질문에서 해시태그를 추출해줘: {question}")
    ])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({})
    
    # 추출된 키워드를 해시태그 형식으로 변환
    keywords = [kw.strip() for kw in result.split(',')]
    hashtags = [t for t in keywords if len(t) > 1 and t.replace(' ', '').isalnum()]
    return hashtags

async def extract_similar_hashtags(hashtag: str):
    # LLM을 사용하여 유사 키워드 추출
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 해시태그와 유사한 키워드를 추출하는 전문가야. 콤마(,)로 구분된 키워드만 출력하고, 설명은 하지마. 비슷한 키워드로 5개 생성해줘."),
        ("human", f"다음 해시태그와 유사한 키워드를 추출해줘: {hashtag}")
    ])
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({})
    
    # 추출된 키워드를 해시태그 형식으로 변환
    keywords = [kw.strip() for kw in result.split(',')]
    hashtags = [t for t in keywords if len(t) > 1 and t.replace(' ', '').isalnum()]
    return hashtags

smithery_api_key = "056f88d0-aa2e-4ea9-8f2d-382ba74dcb07"
profile = "realistic-possum-fgq4Y7"

async def get_trend_hashtags(user_question: str, user_hashtags: list = None):
    try:
        # 사용자 입력 해시태그와 추출된 키워드 결합
        hashtags_arg = []
        if user_hashtags:
            # 사용자 입력 해시태그 처리
            base_hashtags = [tag.lstrip('#') for tag in user_hashtags]
            hashtags_arg.extend(base_hashtags)
            print(f"사용자 입력 해시태그: {base_hashtags}")
            
            # 각 해시태그에 대해 유사 키워드 추출
            for tag in base_hashtags:
                similar_tags = await extract_similar_hashtags(tag)
                if similar_tags:
                    hashtags_arg.extend(similar_tags)
                    print(f"'{tag}'의 유사 해시태그: {similar_tags}")
        else :
            # 질문에서 추가 키워드 추출
            extracted_tags = await extract_hashtags_from_question(user_question)
            if extracted_tags:
                hashtags_arg.extend(extracted_tags)
                print(f"질문에서 추출된 해시태그: {extracted_tags}")
            
        if not hashtags_arg:
            print("⚠️ 분석할 해시태그가 없습니다.")
            return []
        
        # 중복 제거
        hashtags_arg = list(dict.fromkeys(hashtags_arg))
        print(f"최종 분석할 해시태그: {hashtags_arg}")
        
        # MCP 설정
        config = {
            "APIFY_API_TOKEN": "apify_api_LAUmyixlrAn8cvwanbU9moalojDpaF2e0deQ"
        }
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        url = f"https://server.smithery.ai/@HeurisTech/product-trends-mcp/mcp?config={config_b64}&api_key={smithery_api_key}&profile={profile}"
        
        # MCP 세션 생성 및 도구 호출
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with mcp.ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()

                available_tools = [t.name for t in tools_result.tools]
                print(f"사용 가능한 도구들: {available_tools}")
                
                tool_name = "insta_hashtag_scraper"
                if tool_name not in available_tools:
                    print(f"⚠️ 해시태그 스크래퍼를 찾을 수 없습니다: {tool_name}")
                    return []

                arguments = {
                    "hashtags": hashtags_arg,
                    "results_limit": 3000
                }

                result = await session.call_tool(tool_name, arguments)
                
                # 응답 데이터 추출 및 검증
                try:
                    data = None
                    if hasattr(result, 'content') and result.content:
                        data = json.loads(result.content[0].text)
                    elif hasattr(result, 'data'):
                        data = result.data
                    elif hasattr(result, 'result'):
                        data = result.result
                    
                    if not data or not isinstance(data, dict):
                        print("⚠️ 유효하지 않은 응답 데이터 형식")
                        return []
                    
                    # 게시글 데이터 처리
                    posts = data.get('results', [])
                    if not posts:
                        print("⚠️ 분석할 게시글이 없습니다.")
                        return []

                    # 해시태그 추출 및 필터링
                    tag_list = []
                    for post in posts:
                        likes = post.get("likesCount", 0)
                        hashtags = post.get("hashtags", [])
                        if likes >= 10 and hashtags:  # 좋아요 10개 이상
                            tag_list.extend(hashtags)

                    # 중복 제거 및 정제
                    unique_tags = list({tag for tag in tag_list if tag and len(tag) > 1})
                    
                    if not unique_tags:
                        print("⚠️ 추출된 해시태그가 없습니다.")
                        return []
                    return unique_tags
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 파싱 오류: {str(e)}")
                    return []
                except Exception as e:
                    print(f"⚠️ 데이터 처리 오류: {str(e)}")
                    return []
    except Exception as e:
        print(f"⚠️ 해시태그 분석 실패: {str(e)}")
        return []

async def extract_tool_response(result, error_message):
    """도구 응답에서 텍스트 추출을 위한 헬퍼 함수"""
    if hasattr(result, 'content') and result.content:
        return result.content[0].text
    elif hasattr(result, 'result'):
        return result.result
    else:
        raise ValueError(error_message)

async def make_instagram_content():
    try:
        # MCP 설정
        config = {
            "debug": False,
            "hyperFeedApiKey": "bee-7dc552d8-7dee-46f4-9869-4123dd34f7dd"
        }
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        url = (
            f"https://server.smithery.ai/@synthetic-ci/vibe-marketing/mcp"
            f"?config={config_b64}"
            f"&api_key={smithery_api_key}"
            f"&profile=realistic-possum-fgq4Y7"
        )
        
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with mcp.ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # 1. Instagram 훅 가져오기
                try:
                    hooks_result = await session.call_tool("find-hooks", {
                        "network": "instagram",
                        "category": "promotional",
                        "limit": 5
                    })
                    hooks_text = await extract_tool_response(hooks_result, "유효하지 않은 hooks 응답 형식")
                    print("\n✅ Instagram Hooks 생성 완료")
                except Exception as e:
                    print(f"⚠️ Hooks 생성 실패: {str(e)}")
                    hooks_text = ""  # 기본값 설정
                
                # 2. 프레임워크 목록 가져오기
                try:
                    await session.call_tool("list-copywriting-frameworks", {"network": "instagram"})
                except Exception as e:
                    print(f"⚠️ 프레임워크 목록 조회 실패: {str(e)}")
                
                # 3. AIDA 템플릿 가져오기
                try:
                    aida_result = await session.call_tool("get-copywriting-framework", {
                        "network": "instagram",
                        "framework": "aida"
                    })
                    aida_template = await extract_tool_response(aida_result, "유효하지 않은 AIDA 응답 형식")
                    print("\n✅ AIDA 템플릿 생성 완료")
                except Exception as e:
                    print(f"⚠️ AIDA 템플릿 생성 실패: {str(e)}")
                    aida_template = """
                    1. Attention: 주목을 끄는 제목이나 이미지
                    2. Interest: 흥미를 유발하는 내용
                    3. Desire: 구매 욕구를 자극하는 혜택
                    4. Action: 명확한 행동 유도
                    """  # 기본 템플릿
                
                # 결과 반환
                if not hooks_text and not aida_template:
                    raise ValueError("콘텐츠 생성에 실패했습니다.")
                
                return hooks_text, aida_template
                
    except Exception as e:
        print(f"\n⚠️ Instagram 콘텐츠 생성 실패: {str(e)}")
        # 기본 템플릿 반환
        return (
            "\n1. 제품/서비스의 핵심 가치 강조\n2. 고객 문제 해결 방법 제시\n3. 실제 사용 사례 공유\n4. 행동 유도 문구 사용",
            """
            1. Attention: 주목을 끄는 제목이나 이미지
            2. Interest: 흥미를 유발하는 내용
            3. Desire: 구매 욕구를 자극하는 혜택
            4. Action: 명확한 행동 유도
            """
                    )


if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            print("\n=== Instagram 마케팅 콘텐츠 생성기 ===\n")
            
            # 사용자 입력 받기
            keyword = input("검색할 키워드를 입력하세요 (예: 선크림): ").strip()
            
            # 트렌드 해시태그 분석
            print(f"\n'{keyword}'에 대한 트렌드 해시태그를 분석 중입니다...")
            hashtags = await get_trend_hashtags(keyword)
            print("\n=== 트렌드 해시태그 분석 결과 ===\n")
            print(hashtags)
            
            # 마케팅 콘텐츠 생성
            print("\n마케팅 콘텐츠를 생성 중입니다...")
            hooks_text, aida_template = await make_instagram_content()
            
            print("\n=== 생성된 마케팅 콘텐츠 ===\n")
            print("1. 추천 훅(Hook):\n")
            for i, hook in enumerate(hooks_text.split('\n'), 1):
                if hook.strip():
                    print(f"{i}. {hook.strip()}")
            
            print("\n2. AIDA 프레임워크 템플릿:\n")
            print(aida_template)
            
        except Exception as e:
            print(f"\n오류가 발생했습니다: {str(e)}")
            print("\n기본 템플릿을 사용합니다:")
            print("\n1. Attention: 주목을 끄는 제목이나 이미지")
            print("2. Interest: 흥미를 유발하는 내용")
            print("3. Desire: 구매 욕구를 자극하는 혜택")
            print("4. Action: 명확한 행동 유도")
    
    asyncio.run(main())