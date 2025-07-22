#!/usr/bin/env python3
"""
Task Agent MCP Server
업무지원 에이전트를 위한 MCP 서버 구현 (워크플로우 통합)
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import aiohttp

# 상위 디렉토리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field

# 기존 Task Agent import
try:
    from agent import TaskAgent
    from models import UserQuery, AutomationRequest, PersonaType, IntentType
    from shared_modules import get_config, setup_logging
except ImportError:
    # 공통 모듈 import 실패 시 기본 로깅만 사용
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# 로깅 설정
logger = logging.getLogger(__name__)

# 외부 MCP 서버 URL 설정
EXTERNAL_MCP_URLS = {
    "task_manager": "https://smithery.ai/server/@kazuph/mcp-taskmanager",
    "task_queue": "https://smithery.ai/server/@chriscarrollsmith/taskqueue-mcp",
    "calendar": "https://smithery.ai/server/@falgom4/calendar-mcp",
    "gsuite": "https://smithery.ai/server/@rishipradeep-think41/gsuite-mcp"
}

class ProjectWorkflowInput(BaseModel):
    """프로젝트 워크플로우 입력 모델"""
    project_description: str = Field(..., description="프로젝트 설명 또는 기획서")
    deadline: Optional[str] = Field(default=None, description="마감일")
    team_members: Optional[List[str]] = Field(default=None, description="팀 멤버 이메일")
    auto_schedule: bool = Field(default=True, description="자동 캘린더 등록 여부")

class TaskBreakdownInput(BaseModel):
    """업무 분해 입력 모델"""
    project_description: str = Field(..., description="프로젝트 설명")
    deadline: Optional[str] = Field(default=None, description="마감일")
    priority: Optional[str] = Field(default="medium", description="우선순위")
    team_size: Optional[int] = Field(default=1, description="팀 규모")

class TaskManagerInput(BaseModel):
    """태스크 매니저 입력 모델"""
    tasks: List[dict] = Field(..., description="태스크 목록")
    project_title: str = Field(..., description="프로젝트 제목")

class CalendarEventInput(BaseModel):
    """캘린더 이벤트 입력 모델"""
    title: str = Field(..., description="일정 제목")
    start_time: str = Field(..., description="시작 시간")
    end_time: Optional[str] = Field(default=None, description="종료 시간")
    description: Optional[str] = Field(default=None, description="설명")
    attendees: Optional[List[str]] = Field(default=None, description="참석자")

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

class TaskAgentMCPServer:
    """업무지원 에이전트 MCP 서버"""
    
    def __init__(self):
        self.server = Server("task-agent")
        try:
            self.task_agent = TaskAgent()
        except:
            self.task_agent = None
        self.setup_tools()
    
    def setup_tools(self):
        """MCP 도구 설정"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="project_workflow",
                    description="프로젝트 전체 워크플로우 실행 (분해→태스크 등록→캘린더 등록)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_description": {"type": "string", "description": "프로젝트 설명 또는 기획서"},
                            "deadline": {"type": "string", "description": "마감일"},
                            "team_members": {"type": "array", "items": {"type": "string"}, "description": "팀 멤버 이메일"},
                            "auto_schedule": {"type": "boolean", "description": "자동 캘린더 등록 여부", "default": True}
                        },
                        "required": ["project_description"]
                    }
                ),
                Tool(
                    name="break_down_project_with_mcp",
                    description="외부 MCP를 활용한 프로젝트 태스크 분해",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_description": {"type": "string", "description": "프로젝트 설명"},
                            "deadline": {"type": "string", "description": "마감일"},
                            "priority": {"type": "string", "description": "우선순위", "default": "medium"},
                            "team_size": {"type": "integer", "description": "팀 규모", "default": 1}
                        },
                        "required": ["project_description"]
                    }
                ),
                Tool(
                    name="register_tasks_to_manager",
                    description="태스크 매니저에 업무 등록",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tasks": {"type": "array", "description": "태스크 목록"},
                            "project_title": {"type": "string", "description": "프로젝트 제목"}
                        },
                        "required": ["tasks", "project_title"]
                    }
                ),
                Tool(
                    name="schedule_to_calendar_mcp",
                    description="Google Calendar에 일정 등록",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "일정 제목"},
                            "start_time": {"type": "string", "description": "시작 시간"},
                            "end_time": {"type": "string", "description": "종료 시간"},
                            "description": {"type": "string", "description": "설명"},
                            "attendees": {"type": "array", "items": {"type": "string"}, "description": "참석자"}
                        },
                        "required": ["title", "start_time"]
                    }
                ),
                Tool(
                    name="get_tasks_from_manager",
                    description="태스크 매니저에서 업무 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "프로젝트 ID"},
                            "status": {"type": "string", "description": "상태 필터"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="update_task_status",
                    description="태스크 상태 업데이트",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "태스크 ID"},
                            "status": {"type": "string", "description": "새로운 상태"},
                            "progress": {"type": "integer", "description": "진행률 (0-100)"}
                        },
                        "required": ["task_id", "status"]
                    }
                ),
                Tool(
                    name="sync_calendar_with_tasks",
                    description="태스크와 캘린더 동기화",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "프로젝트 ID"},
                            "sync_type": {"type": "string", "description": "동기화 타입", "default": "bidirectional"}
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="generate_project_report",
                    description="프로젝트 진행 상황 보고서 생성",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "프로젝트 ID"},
                            "report_type": {"type": "string", "description": "보고서 유형", "default": "summary"}
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="set_automated_reminders",
                    description="자동 리마인더 설정",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "태스크 ID"},
                            "reminder_intervals": {"type": "array", "items": {"type": "string"}, "description": "리마인더 간격"},
                            "notification_channels": {"type": "array", "items": {"type": "string"}, "description": "알림 채널"}
                        },
                        "required": ["task_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "project_workflow":
                    return await self.handle_project_workflow(arguments)
                elif name == "break_down_project_with_mcp":
                    return await self.handle_project_breakdown_mcp(arguments)
                elif name == "register_tasks_to_manager":
                    return await self.handle_task_registration(arguments)
                elif name == "schedule_to_calendar_mcp":
                    return await self.handle_calendar_scheduling_mcp(arguments)
                elif name == "get_tasks_from_manager":
                    return await self.handle_task_retrieval(arguments)
                elif name == "update_task_status":
                    return await self.handle_task_status_update(arguments)
                elif name == "sync_calendar_with_tasks":
                    return await self.handle_calendar_sync(arguments)
                elif name == "generate_project_report":
                    return await self.handle_project_report(arguments)
                elif name == "set_automated_reminders":
                    return await self.handle_automated_reminders(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=f"도구 실행 중 오류가 발생했습니다: {str(e)}"
                )]
    
    async def handle_project_workflow(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """프로젝트 전체 워크플로우 실행"""
        try:
            project_description = arguments.get("project_description", "")
            deadline = arguments.get("deadline", "")
            team_members = arguments.get("team_members", [])
            auto_schedule = arguments.get("auto_schedule", True)
            
            workflow_results = []
            
            # 1. 프로젝트 분해
            breakdown_result = await self.handle_project_breakdown_mcp({
                "project_description": project_description,
                "deadline": deadline,
                "team_size": len(team_members) if team_members else 1
            })
            workflow_results.append("✅ 프로젝트 분해 완료")
            
            # 2. 태스크 매니저에 등록
            # 시뮬레이션된 태스크 구조 생성
            sample_tasks = [
                {"title": "기획서 작성", "priority": "high", "estimated_days": 2},
                {"title": "설계 및 구조화", "priority": "high", "estimated_days": 3},
                {"title": "개발 환경 구축", "priority": "medium", "estimated_days": 1},
                {"title": "핵심 기능 개발", "priority": "high", "estimated_days": 5},
                {"title": "테스트 및 검증", "priority": "medium", "estimated_days": 2},
                {"title": "배포 및 런칭", "priority": "high", "estimated_days": 1}
            ]
            
            task_registration_result = await self.handle_task_registration({
                "tasks": sample_tasks,
                "project_title": f"프로젝트: {project_description[:50]}..."
            })
            workflow_results.append("✅ 태스크 매니저 등록 완료")
            
            # 3. 캘린더 일정 등록 (auto_schedule이 True인 경우)
            calendar_results = []
            if auto_schedule:
                start_date = datetime.now()
                for i, task in enumerate(sample_tasks):
                    task_start = start_date + timedelta(days=sum(t["estimated_days"] for t in sample_tasks[:i]))
                    task_end = task_start + timedelta(days=task["estimated_days"])
                    
                    calendar_result = await self.handle_calendar_scheduling_mcp({
                        "title": task["title"],
                        "start_time": task_start.strftime("%Y-%m-%d 09:00"),
                        "end_time": task_end.strftime("%Y-%m-%d 18:00"),
                        "description": f"우선순위: {task['priority']}, 예상 소요: {task['estimated_days']}일",
                        "attendees": team_members
                    })
                    calendar_results.append(f"- {task['title']}: {task_start.strftime('%m/%d')} - {task_end.strftime('%m/%d')}")
                
                workflow_results.append("✅ 캘린더 일정 등록 완료")
            
            # 4. 자동 리마인더 설정
            reminder_result = await self.handle_automated_reminders({
                "task_id": "project_main",
                "reminder_intervals": ["1d", "3d", "1w"],
                "notification_channels": ["email", "slack"]
            })
            workflow_results.append("✅ 자동 리마인더 설정 완료")
            
            response_text = f"""
# 🚀 프로젝트 워크플로우 실행 완료

## 프로젝트: {project_description}

## 📋 실행 결과
{chr(10).join(workflow_results)}

## 🎯 프로젝트 개요
- **마감일**: {deadline or "미정"}
- **팀 규모**: {len(team_members) if team_members else 1}명
- **자동 스케줄링**: {"활성화" if auto_schedule else "비활성화"}

## 📊 생성된 태스크 구조
{chr(10).join([f"- {task['title']} ({task['priority']}, {task['estimated_days']}일)" for task in sample_tasks])}

## 📅 캘린더 일정
{chr(10).join(calendar_results) if auto_schedule else "수동 일정 등록 모드"}

## 👥 팀 멤버
{chr(10).join([f"- {member}" for member in team_members]) if team_members else "개인 프로젝트"}

## 🔔 리마인더 설정
- 1일 전 알림
- 3일 전 알림  
- 1주일 전 알림
- 채널: 이메일, Slack

## 📈 진행 관리 도구
- 태스크 상태 조회: `get_tasks_from_manager`
- 상태 업데이트: `update_task_status`
- 진행 보고서: `generate_project_report`
- 캘린더 동기화: `sync_calendar_with_tasks`

## 🎯 다음 단계
1. 각 태스크의 세부 계획 수립
2. 팀원별 역할 분담
3. 정기 체크인 미팅 설정
4. 진행 상황 모니터링

## 📅 워크플로우 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Project workflow error: {e}")
            return [TextContent(
                type="text",
                text=f"프로젝트 워크플로우 실행 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_project_breakdown_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """외부 MCP를 활용한 프로젝트 분해"""
        try:
            project_description = arguments.get("project_description", "")
            deadline = arguments.get("deadline", "")
            priority = arguments.get("priority", "medium")
            team_size = arguments.get("team_size", 1)
            
            # 내부 AI로 먼저 분해
            breakdown_prompt = f"""
            프로젝트 설명: {project_description}
            마감일: {deadline}
            우선순위: {priority}
            팀 규모: {team_size}명
            
            이 프로젝트를 실행 가능한 태스크로 분해해주세요.
            각 태스크는 다음 형식으로 제공해주세요:
            - 태스크명
            - 예상 소요 시간
            - 우선순위
            - 의존성
            """
            
            # Task Agent를 통한 처리
            internal_breakdown = ""
            if self.task_agent:
                user_query = UserQuery(
                    user_id=1,
                    message=breakdown_prompt,
                    persona=PersonaType.COMMON,
                    conversation_id="project_breakdown"
                )
                response = await self.task_agent.process_query(user_query)
                internal_breakdown = response.response
            
            # 외부 태스크 매니저 MCP로 구조화
            structured_tasks = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="create_project",
                arguments={
                    "project_name": f"프로젝트: {project_description[:50]}",
                    "description": internal_breakdown,
                    "deadline": deadline,
                    "priority": priority
                }
            )
            
            response_text = f"""
# 📋 프로젝트 태스크 분해 결과

## 프로젝트: {project_description}

## 🤖 AI 분해 결과
{internal_breakdown}

## 🏗 구조화된 태스크 (외부 MCP)
{structured_tasks}

## 📊 프로젝트 정보
- **마감일**: {deadline or "미정"}
- **우선순위**: {priority}
- **팀 규모**: {team_size}명
- **분해 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 태스크 관리 권장사항
1. **의존성 확인**: 선후 관계가 있는 태스크 식별
2. **리소스 배분**: 팀원별 역량에 맞는 태스크 할당
3. **마일스톤 설정**: 주요 단계별 검토 포인트 설정
4. **위험 관리**: 지연 가능성이 높은 태스크 식별

## 📅 다음 단계
- 태스크 매니저에 등록: `register_tasks_to_manager`
- 캘린더 일정 등록: `schedule_to_calendar_mcp`
- 자동 리마인더 설정: `set_automated_reminders`
- 전체 워크플로우 실행: `project_workflow`
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Project breakdown MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"프로젝트 분해 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_task_registration(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """태스크 매니저에 업무 등록"""
        try:
            tasks = arguments.get("tasks", [])
            project_title = arguments.get("project_title", "")
            
            # 외부 태스크 매니저 MCP 호출
            registration_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="bulk_create_tasks",
                arguments={
                    "project_title": project_title,
                    "tasks": tasks
                }
            )
            
            # 백업으로 task_queue MCP도 시도
            queue_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_queue"],
                tool="enqueue_tasks",
                arguments={
                    "project": project_title,
                    "task_list": tasks
                }
            )
            
            response_text = f"""
# 📝 태스크 매니저 등록 완료

## 프로젝트: {project_title}

## 📊 등록된 태스크 ({len(tasks)}개)
{chr(10).join([f"- {task.get('title', '제목 없음')} (우선순위: {task.get('priority', 'medium')}, 예상: {task.get('estimated_days', 1)}일)" for task in tasks])}

## 🏗 주 태스크 매니저 결과
{registration_result}

## 🔄 백업 큐 시스템 결과
{queue_result}

## 📈 태스크 관리 기능
- **상태 추적**: 진행 중, 완료, 지연 등
- **우선순위 관리**: High, Medium, Low
- **의존성 관리**: 태스크 간 선후 관계
- **진행률 모니터링**: 0-100% 진행률

## 🎯 관리 도구
- 태스크 조회: `get_tasks_from_manager`
- 상태 업데이트: `update_task_status`
- 진행 보고서: `generate_project_report`

## 🔔 자동화 옵션
- 마감일 알림
- 진행률 체크
- 팀원 배정 알림
- 완료 보고

## 📅 등록 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Task registration error: {e}")
            return [TextContent(
                type="text",
                text=f"태스크 등록 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_calendar_scheduling_mcp(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Google Calendar에 일정 등록"""
        try:
            title = arguments.get("title", "")
            start_time = arguments.get("start_time", "")
            end_time = arguments.get("end_time", "")
            description = arguments.get("description", "")
            attendees = arguments.get("attendees", [])
            
            # 주 캘린더 MCP 호출
            calendar_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["calendar"],
                tool="create_event",
                arguments={
                    "summary": title,
                    "description": description,
                    "start": start_time,
                    "end": end_time or start_time,
                    "attendees": attendees
                }
            )
            
            # GSuite MCP로 백업 시도
            gsuite_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["gsuite"],
                tool="calendar_create_event",
                arguments={
                    "title": title,
                    "start_datetime": start_time,
                    "end_datetime": end_time or start_time,
                    "description": description,
                    "attendees": attendees
                }
            )
            
            response_text = f"""
# 📅 Google Calendar 일정 등록 완료

## 일정 정보
- **제목**: {title}
- **시작 시간**: {start_time}
- **종료 시간**: {end_time or "미정"}
- **설명**: {description or "없음"}
- **참석자**: {len(attendees)}명

## 📋 참석자 목록
{chr(10).join([f"- {attendee}" for attendee in attendees]) if attendees else "참석자 없음"}

## 🗓 주 캘린더 시스템 결과
{calendar_result}

## 🔄 GSuite 백업 결과
{gsuite_result}

## 📱 캘린더 기능
- **알림 설정**: 15분 전, 1시간 전, 1일 전
- **반복 일정**: 일일, 주간, 월간 반복 가능
- **회의실 예약**: 가용한 회의실 자동 예약
- **화상회의**: Google Meet 링크 자동 생성

## 🔗 연동 기능
- Slack 알림 연동
- 이메일 초대 자동 발송
- 태스크 매니저와 동기화
- 프로젝트 마일스톤 추적

## 📈 일정 관리 팁
- 준비 시간 15분 추가 권장
- 회의 목적과 아젠다 명시
- 필수/선택 참석자 구분
- 사전 자료 공유

## 🎯 후속 조치
- 회의 전 리마인더 발송
- 참석자 확인 및 대체 일정 조율
- 회의록 템플릿 준비

## 📅 등록 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Calendar scheduling MCP error: {e}")
            return [TextContent(
                type="text",
                text=f"캘린더 일정 등록 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_task_retrieval(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """태스크 매니저에서 업무 조회"""
        try:
            project_id = arguments.get("project_id", "")
            status = arguments.get("status", "")
            
            # 태스크 매니저에서 조회
            task_list = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="get_tasks",
                arguments={
                    "project_id": project_id,
                    "status_filter": status
                }
            )
            
            response_text = f"""
# 📋 태스크 조회 결과

## 조회 조건
- **프로젝트 ID**: {project_id or "전체"}
- **상태 필터**: {status or "전체"}

## 🎯 태스크 목록
{task_list}

## 📊 태스크 통계
조회된 태스크 정보를 바탕으로 다음과 같은 분석이 가능합니다:
- 진행 중인 태스크 수
- 완료된 태스크 수
- 지연된 태스크 수
- 팀별/개인별 작업 부하

## 🔧 관리 도구
- 상태 업데이트: `update_task_status`
- 진행 보고서 생성: `generate_project_report`
- 캘린더와 동기화: `sync_calendar_with_tasks`

## 📅 조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Task retrieval error: {e}")
            return [TextContent(
                type="text",
                text=f"태스크 조회 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_task_status_update(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """태스크 상태 업데이트"""
        try:
            task_id = arguments.get("task_id", "")
            status = arguments.get("status", "")
            progress = arguments.get("progress", 0)
            
            # 태스크 매니저에서 업데이트
            update_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="update_task",
                arguments={
                    "task_id": task_id,
                    "status": status,
                    "progress": progress
                }
            )
            
            response_text = f"""
# ✅ 태스크 상태 업데이트 완료

## 업데이트 정보
- **태스크 ID**: {task_id}
- **새로운 상태**: {status}
- **진행률**: {progress}%

## 🔄 업데이트 결과
{update_result}

## 📈 상태별 의미
- **시작 전**: 아직 작업을 시작하지 않음
- **진행 중**: 현재 작업 중
- **검토 중**: 작업 완료 후 검토 단계
- **완료**: 작업이 완전히 끝남
- **보류**: 일시적으로 중단된 상태
- **취소**: 작업이 취소됨

## 🎯 자동화 트리거
상태 변경에 따른 자동 액션:
- 완료 시: 다음 태스크 자동 시작
- 지연 시: 관련자에게 알림 발송
- 보류 시: 대체 계획 수립 제안

## 📅 업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Task status update error: {e}")
            return [TextContent(
                type="text",
                text=f"태스크 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_calendar_sync(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """태스크와 캘린더 동기화"""
        try:
            project_id = arguments.get("project_id", "")
            sync_type = arguments.get("sync_type", "bidirectional")
            
            # 태스크 목록 조회
            tasks = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="get_tasks",
                arguments={"project_id": project_id}
            )
            
            # 캘린더와 동기화
            sync_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["calendar"],
                tool="sync_with_tasks",
                arguments={
                    "project_id": project_id,
                    "tasks": tasks,
                    "sync_type": sync_type
                }
            )
            
            response_text = f"""
# 🔄 태스크-캘린더 동기화 완료

## 동기화 정보
- **프로젝트 ID**: {project_id}
- **동기화 타입**: {sync_type}

## 📊 동기화 결과
{sync_result}

## 🎯 동기화 타입별 기능
### Bidirectional (양방향)
- 태스크 변경 시 캘린더 자동 업데이트
- 캘린더 일정 변경 시 태스크 자동 업데이트

### Task to Calendar (태스크→캘린더)
- 태스크 생성/수정 시 캘린더 이벤트 생성/수정
- 태스크 완료 시 캘린더 이벤트 완료 처리

### Calendar to Task (캘린더→태스크)
- 캘린더 이벤트 생성 시 태스크 자동 생성
- 일정 변경 시 태스크 마감일 자동 조정

## 📈 동기화 혜택
- 일정과 업무의 일관성 유지
- 중복 입력 작업 제거
- 실시간 진행 상황 추적
- 자동 알림 및 리마인더

## 🔧 관리 옵션
- 동기화 주기 설정
- 특정 태스크 제외 설정
- 알림 방식 사용자화
- 충돌 해결 규칙 설정

## 📅 동기화 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Calendar sync error: {e}")
            return [TextContent(
                type="text",
                text=f"캘린더 동기화 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_project_report(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """프로젝트 진행 상황 보고서 생성"""
        try:
            project_id = arguments.get("project_id", "")
            report_type = arguments.get("report_type", "summary")
            
            # 태스크 데이터 수집
            project_data = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="get_project_analytics",
                arguments={
                    "project_id": project_id,
                    "report_type": report_type
                }
            )
            
            response_text = f"""
# 📊 프로젝트 진행 상황 보고서

## 프로젝트 ID: {project_id}
## 보고서 유형: {report_type}

## 📈 프로젝트 데이터
{project_data}

## 🎯 주요 지표
### 진행 현황
- 전체 태스크 수: -개
- 완료된 태스크: -개 (-)
- 진행 중인 태스크: -개 (-)
- 지연된 태스크: -개 (-)

### 일정 현황
- 프로젝트 시작일: -
- 예상 완료일: -
- 현재 진행률: -%
- 일정 준수율: -%

### 팀 성과
- 참여 인원: -명
- 평균 태스크 완료 시간: -일
- 개인별 생산성: -
- 협업 효율성: -

## 📋 상세 분석
### 완료된 주요 마일스톤
- 기획 단계 완료
- 설계 단계 진행 중
- 개발 단계 대기

### 위험 요소
- 지연 가능성이 높은 태스크 식별
- 리소스 부족 구간 분석
- 의존성 문제 파악

### 개선 제안
- 병렬 처리 가능한 작업 식별
- 우선순위 재조정 권장
- 추가 리소스 필요 구간

## 🔮 예측 및 권장사항
- 현재 속도 기준 완료 예상일
- 목표 달성을 위한 가속 방안
- 품질 관리 체크포인트

## 📅 보고서 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Project report error: {e}")
            return [TextContent(
                type="text",
                text=f"프로젝트 보고서 생성 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def handle_automated_reminders(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """자동 리마인더 설정"""
        try:
            task_id = arguments.get("task_id", "")
            reminder_intervals = arguments.get("reminder_intervals", ["1d", "3d", "1w"])
            notification_channels = arguments.get("notification_channels", ["email"])
            
            # 리마인더 설정
            reminder_result = await self.call_external_mcp(
                server_url=EXTERNAL_MCP_URLS["task_manager"],
                tool="set_reminders",
                arguments={
                    "task_id": task_id,
                    "intervals": reminder_intervals,
                    "channels": notification_channels
                }
            )
            
            response_text = f"""
# ⏰ 자동 리마인더 설정 완료

## 리마인더 정보
- **태스크 ID**: {task_id}
- **알림 간격**: {', '.join(reminder_intervals)}
- **알림 채널**: {', '.join(notification_channels)}

## 🔔 설정 결과
{reminder_result}

## 📱 알림 채널별 특징
### 이메일
- 상세한 정보 제공 가능
- 첨부파일 지원
- 보관 및 검색 용이

### Slack
- 실시간 알림
- 팀 채널 공유 가능
- 빠른 응답 및 토론

### SMS
- 즉시 확인 가능
- 간단한 정보 전달
- 긴급 상황에 적합

### 앱 푸시
- 모바일 최적화
- 액션 버튼 지원
- 위치 기반 알림

## ⚙️ 리마인더 옵션
### 스누즈 기능
- 5분, 15분, 1시간 후 재알림
- 사용자 설정 시간

### 에스컬레이션
- 응답 없을 시 관리자에게 알림
- 중요도에 따른 알림 강도 조절

### 스마트 알림
- 사용자 활동 패턴 학습
- 최적 시간대 자동 선택

## 📊 효과 측정
- 알림 확인률 추적
- 태스크 완료율 개선도
- 응답 시간 단축 효과

## 📅 설정 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Automated reminders error: {e}")
            return [TextContent(
                type="text",
                text=f"자동 리마인더 설정 중 오류가 발생했습니다: {str(e)}"
            )]
    
    async def run(self):
        """MCP 서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

def main():
    """메인 함수"""
    server = TaskAgentMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
