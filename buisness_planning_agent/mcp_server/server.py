#!/usr/bin/env python3
"""
Business Planning Agent MCP Server
사업기획 에이전트를 위한 MCP 서버 구현 (워크플로우 통합)
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import aiohttp

# 상위 디렉토리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field

# 기존 비즈니스 플래닝 서비스 import
try:
    from business_planning import BusinessPlanningService
except ImportError:
    BusinessPlanningService = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 외부 MCP 서버 URL 설정
EXTERNAL_MCP_URLS = {
    "search": "https://smithery.ai/server/@smithery-ai/search-mcp",
    "lean_canvas": "https://smithery.ai/server/@canDplugin/plugin-mcp-server", 
    "notion": "https://smithery.ai/server/mcp-notion"
}

class TrendSearchInput(BaseModel):
    """트렌드 검색 입력 모델"""
    query: str = Field(..., description="검색할 트렌드 키워드")
    year: Optional[int] = Field(default=2025, description="검색 연도")
    category: Optional[str] = Field(default="startup", description="검색 카테고리")

class MarketAnalysisInput(BaseModel):
    """시장 분석 입력 모델"""
    business_idea: str = Field(..., description="분석할 사업 아이디어")
    target_market: Optional[str] = Field(default=None, description="목표 시장")
    analysis_type: Optional[str] = Field(default="comprehensive", description="분석 유형")

class LeanCanvasInput(BaseModel):
    """린캔버스 생성 입력 모델"""
    business_idea: str = Field(..., description="사업 아이디어")
    idea_summary: Optional[str] = Field(default=None, description="아이디어 요약")
    market_summary: Optional[str] = Field(default=None, description="시장 분석 요약")

class NotionDocumentInput(BaseModel):
    """Notion 문서 생성 입력 모델"""
    title: str = Field(..., description="문서 제목")
    content: str = Field(..., description="문서 내용")
    tags: Optional[List[str]] = Field(default=None, description="태그")

class BusinessPlanningMCPServer:
    """사업기획 에이전트 MCP 서버"""
    
    def __init__(self):
        self.server = Server("business-planning-agent")
        if BusinessPlanningService:
            self.business_service = BusinessPlanningService()
        else:
            self.business_service = None
        self.setup_tools()
    
    def setup_tools(self):
        """MCP 도구 설정"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="trend_search_with_mcp",
                    description="외부 검색 MCP를 활용한 트렌드 검색",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "검색할 트렌드 키워드"},
                            "year": {"type": "integer", "description": "검색 연도", "default": 2025},
                            "category": {"type": "string", "description": "검색 카테고리", "default": "startup"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="market_analysis",
                    description="시장 분석 및 경쟁사 분석",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "분석할 사업 아이디어"},
                            "target_market": {"type": "string", "description": "목표 시장"},
                            "analysis_type": {"type": "string", "description": "분석 유형", "default": "comprehensive"}
                        },
                        "required": ["business_idea"]
                    }
                ),
                Tool(
                    name="generate_lean_canvas_with_mcp",
                    description="외부 MCP를 활용한 린캔버스 생성",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "사업 아이디어"},
                            "idea_summary": {"type": "string", "description": "아이디어 요약"},
                            "market_summary": {"type": "string", "description": "시장 분석 요약"}
                        },
                        "required": ["business_idea"]
                    }
                ),
                Tool(
                    name="save_to_notion",
                    description="Notion에 사업계획서 저장",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "문서 제목"},
                            "content": {"type": "string", "description": "문서 내용"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "태그"}
                        },
                        "required": ["title", "content"]
                    }
                ),
                Tool(
                    name="comprehensive_business_workflow",
                    description="사업기획 전체 워크플로우 실행 (트렌드→분석→린캔버스→저장)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "initial_query": {"type": "string", "description": "초기 사업 아이디어 또는 관심 분야"},
                            "user_preferences": {"type": "string", "description": "사용자 선호도 및 관심사"},
                            "auto_save": {"type": "boolean", "description": "자동으로 Notion에 저장할지 여부", "default": true}
                        },
                        "required": ["initial_query"]
                    }
                ),
                Tool(
                    name="validate_business_idea",
                    description="사업 아이디어 검증 및 피드백",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "검증할 사업 아이디어"},
                            "target_customer": {"type": "string", "description": "목표 고객"},
                            "market_size": {"type": "string", "description": "예상 시장 규모"}
                        },
                        "required": ["business_idea"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "trend_search_with_mcp":
                    return await self.handle_trend_search_mcp(arguments)
                elif name == "market_analysis":
                    return await self.handle_market_analysis(arguments)
                elif name == "generate_lean_canvas_with_mcp":
                    return await self.handle_lean_canvas_mcp(arguments)
                elif name == "save_to_notion":
                    return await self.handle_notion_save(arguments)
                elif name == "comprehensive_business_workflow":
                    return await self.handle_comprehensive_workflow(arguments)
                elif name == "validate_business_idea":
                    return await self.handle_idea_validation(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=f"도구 실행 중 오류가 발생했습니다: {str(e)}"
                )]
    
    async def handle_trend_search_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """외부 검색 MCP를 활용한 트렌드 검색"""
        try:
            query = arguments.get("query", "")
            year = arguments.get("year", 2025)
            category = arguments.get("category", "startup")
            
            # 외부 검색 MCP 호출
            search_query = f"{year}년 {category} 트렌드 {query}"
            external_response = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": search_query}
            )
            
            # 내부 AI로 결과 분석 및 구조화
            if self.business_service:
                analysis_prompt = f"""
                다음 검색 결과를 바탕으로 유망한 창업 아이템 3개를 제안해주세요:
                
                검색 결과: {external_response}
                
                각 후보는 특징, 시장성, 고객군, 수익모델을 포함해서 정리해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=analysis_prompt,
                    use_retriever=True
                )
                analysis_content = result['answer']
            else:
                analysis_content = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📊 {year}년 {category} 트렌드 분석 결과

## 🔍 검색 키워드: {query}

### 외부 검색 결과
{external_response}

### 🎯 AI 분석 및 추천
{analysis_content}

## 📈 다음 단계
1. 관심 있는 아이템 선택
2. 시장 분석 수행 (`market_analysis` 도구 사용)
3. 린캔버스 생성 (`generate_lean_canvas_with_mcp` 도구 사용)
4. Notion에 사업계획서 저장 (`save_to_notion` 도구 사용)

## 🚀 전체 워크플로우 실행
`comprehensive_business_workflow` 도구를 사용하면 위 과정을 자동으로 실행할 수 있습니다.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Trend search MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"트렌드 검색 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_market_analysis(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """시장 분석 처리 (외부 검색 MCP 활용)"""
        try:
            business_idea = arguments.get("business_idea", "")
            target_market = arguments.get("target_market", "")
            analysis_type = arguments.get("analysis_type", "comprehensive")
            
            # 외부 검색 MCP로 시장 데이터 수집
            market_search_query = f"{business_idea} 시장 규모 경쟁사 분석"
            external_market_data = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": market_search_query}
            )
            
            # 내부 AI로 분석
            if self.business_service:
                analysis_prompt = f"""
                사업 아이디어: {business_idea}
                목표 시장: {target_market}
                
                다음 시장 데이터를 바탕으로 종합적인 시장 분석을 수행해주세요:
                {external_market_data}
                
                분석 항목:
                1. 시장 규모 및 성장성
                2. 목표 고객 세그먼트 분석
                3. 경쟁사 분석 및 차별화 포인트
                4. 시장 진입 전략
                5. 예상 수익 구조
                6. 위험 요소 및 대응 방안
                
                표와 구체적인 데이터를 포함해서 분석해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=analysis_prompt,
                    use_retriever=True
                )
                analysis_content = result['answer']
            else:
                analysis_content = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📊 시장 분석 보고서

## 분석 대상: {business_idea}

### 🔍 외부 시장 데이터
{external_market_data}

### 📈 AI 분석 결과
{analysis_content}

## 📋 분석 요약
- **시장 유형**: {analysis_type}
- **목표 시장**: {target_market or "전체 시장"}
- **분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 다음 단계
이 시장 분석 결과를 바탕으로 린캔버스를 생성하시겠습니까?
`generate_lean_canvas_with_mcp` 도구를 사용해보세요.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return [TextContent(
                type="text",
                text=f"시장 분석 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_lean_canvas_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """외부 MCP를 활용한 린캔버스 생성"""
        try:
            business_idea = arguments.get("business_idea", "")
            idea_summary = arguments.get("idea_summary", "")
            market_summary = arguments.get("market_summary", "")
            
            # 외부 린캔버스 MCP 호출
            external_canvas = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["lean_canvas"],
                tool="build-lean-canvas",
                arguments={
                    "canvas_type": "lean_canvas",
                    "idea_summary": idea_summary or business_idea,
                    "market_summary": market_summary or "시장 분석 필요"
                }
            )
            
            # 내부 AI로 추가 분석
            if self.business_service:
                canvas_prompt = f"""
                사업 아이디어: {business_idea}
                
                외부 툴에서 생성된 린캔버스:
                {external_canvas}
                
                이 린캔버스를 검토하고 개선점을 제안해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=canvas_prompt,
                    use_retriever=True
                )
                ai_review = result['answer']
            else:
                ai_review = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📋 린캔버스 비즈니스 모델

## 사업 아이디어: {business_idea}

### 🎯 기본 정보
- **아이디어 요약**: {idea_summary or business_idea}
- **시장 분석 요약**: {market_summary or "추가 분석 필요"}

### 📊 생성된 린캔버스
{external_canvas}

### 💡 AI 검토 및 개선점
{ai_review}

### 📈 다음 단계
1. 린캔버스의 각 항목을 구체적으로 작성
2. 고객 검증 및 피드백 수집
3. MVP 개발 계획 수립
4. 사업 계획서 작성 및 저장

## 🎯 자동 저장
이 린캔버스를 Notion에 저장하시겠습니까? `save_to_notion` 도구를 사용해보세요.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Lean canvas MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"린캔버스 생성 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_notion_save(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Notion에 문서 저장"""
        try:
            title = arguments.get("title", "")
            content = arguments.get("content", "")
            tags = arguments.get("tags", ["사업기획", "자동화", "AI"])
            
            # Notion MCP 호출
            notion_response = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["notion"],
                tool="create_page",
                arguments={
                    "title": title,
                    "content": content,
                    "metadata": {
                        "tags": tags,
                        "created_at": datetime.now().isoformat(),
                        "source": "business_planning_agent"
                    }
                }
            )
            
            response_text = f"""
# 📝 Notion 저장 완료

## 문서 정보
- **제목**: {title}
- **태그**: {', '.join(tags)}
- **저장 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 저장 결과
{notion_response}

## 🎯 저장된 내용 미리보기
{content[:300]}{"..." if len(content) > 300 else ""}

## 📚 문서 관리
- Notion에서 문서 편집 및 공유 가능
- 팀 협업을 위한 권한 설정
- 버전 관리 및 변경 이력 추적
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Notion save error: {e}")
            return [TextContent(
                type="text",
                text=f"Notion 저장 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_comprehensive_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """사업기획 전체 워크플로우 실행"""
        try:
            initial_query = arguments.get("initial_query", "")
            user_preferences = arguments.get("user_preferences", "")
            auto_save = arguments.get("auto_save", True)
            
            workflow_results = []
            
            # 1. 트렌드 검색
            trend_result = await self.handle_trend_search_mcp({
                "query": initial_query,
                "year": 2025,
                "category": "startup"
            })
            workflow_results.append("✅ 트렌드 검색 완료")
            
            # 2. 시장 분석 (가상의 선택된 아이디어로)
            selected_idea = f"{initial_query} 관련 AI 솔루션"  # 실제로는 사용자 선택 필요
            market_result = await self.handle_market_analysis({
                "business_idea": selected_idea,
                "target_market": "한국 시장",
                "analysis_type": "comprehensive"
            })
            workflow_results.append("✅ 시장 분석 완료")
            
            # 3. 린캔버스 생성
            canvas_result = await self.handle_lean_canvas_mcp({
                "business_idea": selected_idea,
                "idea_summary": f"{initial_query}를 위한 혁신적인 솔루션",
                "market_summary": "시장 분석 결과 반영"
            })
            workflow_results.append("✅ 린캔버스 생성 완료")
            
            # 4. Notion 저장 (auto_save가 True인 경우)
            if auto_save:
                comprehensive_content = f"""
# {selected_idea} 사업계획서

## 1. 창업 아이디어 요약
{initial_query}

## 2. 시장 조사 요약
시장 분석 결과가 여기에 포함됩니다.

## 3. 비즈니스 모델 (Lean Canvas)
린캔버스 결과가 여기에 포함됩니다.

## 4. 사용자 선호도
{user_preferences}

생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                notion_result = await self.handle_notion_save({
                    "title": f"{selected_idea} 사업계획서",
                    "content": comprehensive_content,
                    "tags": ["사업기획", "자동화", "워크플로우"]
                })
                workflow_results.append("✅ Notion 저장 완료")
            
            response_text = f"""
# 🚀 사업기획 워크플로우 실행 완료

## 초기 쿼리: {initial_query}

## 📋 실행 결과
{chr(10).join(workflow_results)}

## 🎯 선정된 사업 아이디어
**{selected_idea}**

## 👤 사용자 선호도 반영
{user_preferences or "기본 설정 적용"}

## 📈 워크플로우 단계별 결과

### 1️⃣ 트렌드 검색
최신 트렌드 데이터를 수집하고 유망 아이템을 식별했습니다.

### 2️⃣ 시장 분석
목표 시장의 규모와 경쟁 상황을 분석했습니다.

### 3️⃣ 린캔버스 생성
비즈니스 모델의 핵심 요소들을 구조화했습니다.

### 4️⃣ 문서화
{f"모든 결과를 Notion에 저장했습니다." if auto_save else "수동 저장을 선택하셨습니다."}

## 🎯 다음 단계 권장사항
1. 고객 인터뷰 및 검증
2. MVP 개발 계획 수립
3. 투자 유치 전략 수립
4. 팀 구성 및 역할 분담

## 📅 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Comprehensive workflow error: {e}")
            return [TextContent(
                type="text",
                text=f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_idea_validation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """사업 아이디어 검증 처리"""
        try:
            business_idea = arguments.get("business_idea", "")
            target_customer = arguments.get("target_customer", "")
            market_size = arguments.get("market_size", "")
            
            # 외부 검색으로 검증 데이터 수집
            validation_query = f"{business_idea} 시장 검증 사례 성공 실패"
            external_validation_data = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": validation_query}
            )
            
            if self.business_service:
                validation_prompt = f"""
                다음 사업 아이디어를 검증해주세요:
                
                사업 아이디어: {business_idea}
                목표 고객: {target_customer}
                예상 시장 규모: {market_size}
                
                외부 검증 데이터: {external_validation_data}
                
                검증 항목:
                1. 시장 필요성 및 문제 해결 정도
                2. 목표 고객의 명확성
                3. 경쟁 우위 요소
                4. 수익성 및 확장 가능성
                5. 실현 가능성
                6. 위험 요소
                
                각 항목에 대해 점수(1-10)와 개선 방안을 제시해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=validation_prompt,
                    use_retriever=True
                )
                validation_content = result['answer']
            else:
                validation_content = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 🔍 사업 아이디어 검증 보고서

## 검증 대상: {business_idea}

### 🔍 외부 검증 데이터
{external_validation_data}

### 💡 AI 검증 결과
{validation_content}

## 📋 검증 요약
- **목표 고객**: {target_customer or "미정"}
- **시장 규모**: {market_size or "미정"}
- **검증 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 권장 사항
검증 결과를 바탕으로 사업 아이디어를 개선하고, 다음 단계로 시장 분석과 린캔버스 작성을 진행하시기 바랍니다.

전체 워크플로우를 실행하려면 `comprehensive_business_workflow` 도구를 사용해보세요.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Idea validation error: {e}")
            return [TextContent(
                type="text",
                text=f"아이디어 검증 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def run(self):
        """MCP 서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

def main():
    """메인 함수"""
    server = BusinessPlanningMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()

// ...
    async def call_external_mcp(self, server_url: str, tool: str, arguments: dict) -> str:
        """외부 MCP 서버로 요청 전송"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "call_tool",
                "params": {
                    "name": tool,
                    "arguments": arguments
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(server_url, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("result", [{}])[0].get("text", "외부 MCP 응답 없음")
                    else:
                        return f"외부 MCP 서버 오류: {resp.status}"
        except Exception as e:
            logger.error(f"External MCP call error: {e}")
            return f"외부 MCP 호출 실패: {str(e)}"

class BusinessPlanningMCPServer:
    """사업기획 에이전트 MCP 서버"""
    
    def __init__(self):
        self.server = Server("business-planning-agent")
        if BusinessPlanningService:
            self.business_service = BusinessPlanningService()
        else:
            self.business_service = None
        self.setup_tools()
    
    def setup_tools(self):
        """MCP 도구 설정"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="trend_search_with_mcp",
                    description="외부 검색 MCP를 활용한 트렌드 검색",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "검색할 트렌드 키워드"},
                            "year": {"type": "integer", "description": "검색 연도", "default": 2025},
                            "category": {"type": "string", "description": "검색 카테고리", "default": "startup"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="market_analysis",
                    description="시장 분석 및 경쟁사 분석",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "분석할 사업 아이디어"},
                            "target_market": {"type": "string", "description": "목표 시장"},
                            "analysis_type": {"type": "string", "description": "분석 유형", "default": "comprehensive"}
                        },
                        "required": ["business_idea"]
                    }
                ),
                Tool(
                    name="generate_lean_canvas_with_mcp",
                    description="외부 MCP를 활용한 린캔버스 생성",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "사업 아이디어"},
                            "idea_summary": {"type": "string", "description": "아이디어 요약"},
                            "market_summary": {"type": "string", "description": "시장 분석 요약"}
                        },
                        "required": ["business_idea"]
                    }
                ),
                Tool(
                    name="save_to_notion",
                    description="Notion에 사업계획서 저장",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "문서 제목"},
                            "content": {"type": "string", "description": "문서 내용"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "태그"}
                        },
                        "required": ["title", "content"]
                    }
                ),
                Tool(
                    name="comprehensive_business_workflow",
                    description="사업기획 전체 워크플로우 실행 (트렌드→분석→린캔버스→저장)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "initial_query": {"type": "string", "description": "초기 사업 아이디어 또는 관심 분야"},
                            "user_preferences": {"type": "string", "description": "사용자 선호도 및 관심사"},
                            "auto_save": {"type": "boolean", "description": "자동으로 Notion에 저장할지 여부", "default": true}
                        },
                        "required": ["initial_query"]
                    }
                ),
                Tool(
                    name="validate_business_idea",
                    description="사업 아이디어 검증 및 피드백",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_idea": {"type": "string", "description": "검증할 사업 아이디어"},
                            "target_customer": {"type": "string", "description": "목표 고객"},
                            "market_size": {"type": "string", "description": "예상 시장 규모"}
                        },
                        "required": ["business_idea"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "trend_search_with_mcp":
                    return await self.handle_trend_search_mcp(arguments)
                elif name == "market_analysis":
                    return await self.handle_market_analysis(arguments)
                elif name == "generate_lean_canvas_with_mcp":
                    return await self.handle_lean_canvas_mcp(arguments)
                elif name == "save_to_notion":
                    return await self.handle_notion_save(arguments)
                elif name == "comprehensive_business_workflow":
                    return await self.handle_comprehensive_workflow(arguments)
                elif name == "validate_business_idea":
                    return await self.handle_idea_validation(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=f"도구 실행 중 오류가 발생했습니다: {str(e)}"
                )]
    
    async def handle_trend_search_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """외부 검색 MCP를 활용한 트렌드 검색"""
        try:
            query = arguments.get("query", "")
            year = arguments.get("year", 2025)
            category = arguments.get("category", "startup")
            
            # 외부 검색 MCP 호출
            search_query = f"{year}년 {category} 트렌드 {query}"
            external_response = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": search_query}
            )
            
            # 내부 AI로 결과 분석 및 구조화
            if self.business_service:
                analysis_prompt = f"""
                다음 검색 결과를 바탕으로 유망한 창업 아이템 3개를 제안해주세요:
                
                검색 결과: {external_response}
                
                각 후보는 특징, 시장성, 고객군, 수익모델을 포함해서 정리해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=analysis_prompt,
                    use_retriever=True
                )
                analysis_content = result['answer']
            else:
                analysis_content = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📊 {year}년 {category} 트렌드 분석 결과

## 🔍 검색 키워드: {query}

### 외부 검색 결과
{external_response}

### 🎯 AI 분석 및 추천
{analysis_content}

## 📈 다음 단계
1. 관심 있는 아이템 선택
2. 시장 분석 수행 (`market_analysis` 도구 사용)
3. 린캔버스 생성 (`generate_lean_canvas_with_mcp` 도구 사용)
4. Notion에 사업계획서 저장 (`save_to_notion` 도구 사용)

## 🚀 전체 워크플로우 실행
`comprehensive_business_workflow` 도구를 사용하면 위 과정을 자동으로 실행할 수 있습니다.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Trend search MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"트렌드 검색 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_market_analysis(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """시장 분석 처리 (외부 검색 MCP 활용)"""
        try:
            business_idea = arguments.get("business_idea", "")
            target_market = arguments.get("target_market", "")
            analysis_type = arguments.get("analysis_type", "comprehensive")
            
            # 외부 검색 MCP로 시장 데이터 수집
            market_search_query = f"{business_idea} 시장 규모 경쟁사 분석"
            external_market_data = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": market_search_query}
            )
            
            # 내부 AI로 분석
            if self.business_service:
                analysis_prompt = f"""
                사업 아이디어: {business_idea}
                목표 시장: {target_market}
                
                다음 시장 데이터를 바탕으로 종합적인 시장 분석을 수행해주세요:
                {external_market_data}
                
                분석 항목:
                1. 시장 규모 및 성장성
                2. 목표 고객 세그먼트 분석
                3. 경쟁사 분석 및 차별화 포인트
                4. 시장 진입 전략
                5. 예상 수익 구조
                6. 위험 요소 및 대응 방안
                
                표와 구체적인 데이터를 포함해서 분석해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=analysis_prompt,
                    use_retriever=True
                )
                analysis_content = result['answer']
            else:
                analysis_content = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📊 시장 분석 보고서

## 분석 대상: {business_idea}

### 🔍 외부 시장 데이터
{external_market_data}

### 📈 AI 분석 결과
{analysis_content}

## 📋 분석 요약
- **시장 유형**: {analysis_type}
- **목표 시장**: {target_market or "전체 시장"}
- **분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 다음 단계
이 시장 분석 결과를 바탕으로 린캔버스를 생성하시겠습니까?
`generate_lean_canvas_with_mcp` 도구를 사용해보세요.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return [TextContent(
                type="text",
                text=f"시장 분석 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_lean_canvas_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """외부 MCP를 활용한 린캔버스 생성"""
        try:
            business_idea = arguments.get("business_idea", "")
            idea_summary = arguments.get("idea_summary", "")
            market_summary = arguments.get("market_summary", "")
            
            # 외부 린캔버스 MCP 호출
            external_canvas = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["lean_canvas"],
                tool="build-lean-canvas",
                arguments={
                    "canvas_type": "lean_canvas",
                    "idea_summary": idea_summary or business_idea,
                    "market_summary": market_summary or "시장 분석 필요"
                }
            )
            
            # 내부 AI로 추가 분석
            if self.business_service:
                canvas_prompt = f"""
                사업 아이디어: {business_idea}
                
                외부 툴에서 생성된 린캔버스:
                {external_canvas}
                
                이 린캔버스를 검토하고 개선점을 제안해주세요.
                """
                
                result = await self.business_service.run_rag_query(
                    conversation_id=1,
                    user_input=canvas_prompt,
                    use_retriever=True
                )
                ai_review = result['answer']
            else:
                ai_review = "내부 분석 서비스를 사용할 수 없습니다."
            
            response_text = f"""
# 📋 린캔버스 비즈니스 모델

## 사업 아이디어: {business_idea}

### 🎯 기본 정보
- **아이디어 요약**: {idea_summary or business_idea}
- **시장 분석 요약**: {market_summary or "추가 분석 필요"}

### 📊 생성된 린캔버스
{external_canvas}

### 💡 AI 검토 및 개선점
{ai_review}

### 📈 다음 단계
1. 린캔버스의 각 항목을 구체적으로 작성
2. 고객 검증 및 피드백 수집
3. MVP 개발 계획 수립
4. 사업 계획서 작성 및 저장

## 🎯 자동 저장
이 린캔버스를 Notion에 저장하시겠습니까? `save_to_notion` 도구를 사용해보세요.
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Lean canvas MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"린캔버스 생성 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_notion_save(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Notion에 문서 저장"""
        try:
            title = arguments.get("title", "")
            content = arguments.get("content", "")
            tags = arguments.get("tags", ["사업기획", "자동화", "AI"])
            
            # Notion MCP 호출
            notion_response = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["notion"],
                tool="create_page",
                arguments={
                    "title": title,
                    "content": content,
                    "metadata": {
                        "tags": tags,
                        "created_at": datetime.now().isoformat(),
                        "source": "business_planning_agent"
                    }
                }
            )
            
            response_text = f"""
# 📝 Notion 저장 완료

## 문서 정보
- **제목**: {title}
- **태그**: {', '.join(tags)}
- **저장 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 저장 결과
{notion_response}

## 🎯 저장된 내용 미리보기
{content[:300]}{"..." if len(content) > 300 else ""}

## 📚 문서 관리
- Notion에서 문서 편집 및 공유 가능
- 팀 협업을 위한 권한 설정
- 버전 관리 및 변경 이력 추적
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Notion save error: {e}")
            return [TextContent(
                type="text",
                text=f"Notion 저장 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_comprehensive_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """사업기획 전체 워크플로우 실행"""
        try:
            initial_query = arguments.get("initial_query", "")
            user_preferences = arguments.get("user_preferences", "")
            auto_save = arguments.get("auto_save", True)
            
            workflow_results = []
            
            # 1. 트렌드 검색
            trend_result = await self.handle_trend_search_mcp({
                "query": initial_query,
                "year": 2025,
                "category": "startup"
            })
            workflow_results.append("✅ 트렌드 검색 완료")
            
            # 2. 시장 분석 (가상의 선택된 아이디어로)
            selected_idea = f"{initial_query} 관련 AI 솔루션"  # 실제로는 사용자 선택 필요
            market_result = await self.handle_market_analysis({
                "business_idea": selected_idea,
                "target_market": "한국 시장",
                "analysis_type": "comprehensive"
            })
            workflow_results.append("✅ 시장 분석 완료")
            
            # 3. 린캔버스 생성
            canvas_result = await self.handle_lean_canvas_mcp({
                "business_idea": selected_idea,
                "idea_summary": f"{initial_query}를 위한 혁신적인 솔루션",
                "market_summary": "시장 분석 결과 반영"
            })
            workflow_results.append("✅ 린캔버스 생성 완료")
            
            # 4. Notion 저장 (auto_save가 True인 경우)
            if auto_save:
                comprehensive_content = f"""
# {selected_idea} 사업계획서

## 1. 창업 아이디어 요약
{initial_query}

## 2. 시장 조사 요약
시장 분석 결과가 여기에 포함됩니다.

## 3. 비즈니스 모델 (Lean Canvas)
린캔버스 결과가 여기에 포함됩니다.

## 4. 사용자 선호도
{user_preferences}

생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                notion_result = await self.handle_notion_save({
                    "title": f"{selected_idea} 사업계획서",
                    "content": comprehensive_content,
                    "tags": ["사업기획", "자동화", "워크플로우"]
                })
                workflow_results.append("✅ Notion 저장 완료")
            
            response_text = f"""
# 🚀 사업기획 워크플로우 실행 완료

## 초기 쿼리: {initial_query}

## 📋 실행 결과
{chr(10).join(workflow_results)}

## 🎯 선정된 사업 아이디어
**{selected_idea}**

## 👤 사용자 선호도 반영
{user_preferences or "기본 설정 적용"}

## 📈 워크플로우 단계별 결과

### 1️⃣ 트렌드 검색
최신 트렌드 데이터를 수집하고 유망 아이템을 식별했습니다.

### 2️⃣ 시장 분석
목표 시장의 규모와 경쟁 상황을 분석했습니다.

### 3️⃣ 린캔버스 생성
비즈니스 모델의 핵심 요소들을 구조화했습니다.

### 4️⃣ 문서화
{f"모든 결과를 Notion에 저장했습니다." if auto_save else "수동 저장을 선택하셨습니다."}

## 🎯 다음 단계 권장사항
1. 고객 인터뷰 및 검증
2. MVP 개발 계획 수립
3. 투자 유치 전략 수립
4. 팀 구성 및 역할 분담

## 📅 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Comprehensive workflow error: {e}")
            return [TextContent(
                type="text",
                text=f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_idea_validation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """사업 아이디어 검증 처리"""
        try:
            business_idea = arguments.get("business_idea", "")
            target_customer = arguments.get("target_customer", "")
            market_size = arguments.get("market_size", "")
            
            # 외부 검색으로 검증 데이터 수집
            validation_query = f"{business_idea} 시장 검증 사례 성공 실패"
            external_validation_data = await call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["search"],
                tool="search",
                arguments={"query": validation_
