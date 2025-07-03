"""
응답 처리 및 포맷팅 유틸리티
"""
import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """응답 포맷팅 클래스"""
    
    @staticmethod
    def format_agent_response(response: str, agent_name: str, agent_type: str) -> str:
        """에이전트 응답 포맷팅"""
        
        # 에이전트별 인사말 추가
        greetings = {
            'branding': f"안녕하세요! 브랜딩 전문가 {agent_name}입니다. 🎨",
            'content': f"안녕하세요! 콘텐츠 크리에이터 {agent_name}입니다! ✨",
            'targeting': f"안녕하세요! 타겟팅 분석가 {agent_name}입니다. 📊"
        }
        
        greeting = greetings.get(agent_type, f"안녕하세요! {agent_name}입니다.")
        
        # 응답이 이미 인사말로 시작하는지 확인
        if not response.startswith("안녕하세요"):
            response = f"{greeting}\n\n{response}"
        
        return response
    
    @staticmethod
    def add_document_references(response: str, documents: List[Dict[str, Any]]) -> str:
        """응답에 문서 참조 정보 추가"""
        if not documents:
            return response
        
        reference_section = "\n\n📚 **참고 자료:**\n"
        
        for i, doc in enumerate(documents[:3], 1):  # 최대 3개까지
            reference_section += f"{i}. [{doc['title']}]({doc.get('url', '#')}) - {doc['source']}\n"
        
        return response + reference_section
    
    @staticmethod
    def add_action_items(response: str, agent_type: str) -> str:
        """에이전트 타입별 실행 항목 추가"""
        
        action_items = {
            'branding': [
                "브랜드 키워드 3-5개 정의하기",
                "경쟁사 브랜딩 분석하기", 
                "브랜드 스토리 초안 작성하기"
            ],
            'content': [
                "콘텐츠 캘린더 1주일분 계획하기",
                "첫 번째 포스트 아이디어 스케치하기",
                "타겟 해시태그 20개 리스트 만들기"
            ],
            'targeting': [
                "현재 고객 데이터 수집하기",
                "경쟁사 타겟 고객 조사하기",
                "페르소나 초안 1개 작성하기"
            ]
        }
        
        items = action_items.get(agent_type, [])
        if not items:
            return response
        
        action_section = "\n\n✅ **다음 단계로 해볼 만한 액션:**\n"
        for item in items:
            action_section += f"• {item}\n"
        
        return response + action_section
    
    @staticmethod
    def format_markdown_response(content: str) -> str:
        """마크다운 포맷팅 개선"""
        
        # 제목 스타일링
        content = re.sub(r'^### (.+)$', r'### 🎯 \1', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'## 📋 \1', content, flags=re.MULTILINE)
        
        # 강조 표시
        content = re.sub(r'\*\*(.+?)\*\*', r'**🔥 \1**', content)
        
        # 리스트 아이템에 이모지 추가
        content = re.sub(r'^- (.+)$', r'• \1', content, flags=re.MULTILINE)
        
        return content

class ConversationManager:
    """대화 관리 클래스"""
    
    def __init__(self):
        self.conversation_history = []
        self.context_window = 10  # 최근 10개 메시지만 유지
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """메시지 추가"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(message)
        
        # 컨텍스트 윈도우 제한
        if len(self.conversation_history) > self.context_window:
            self.conversation_history = self.conversation_history[-self.context_window:]
    
    def get_recent_context(self, num_messages: int = 6) -> List[Dict[str, Any]]:
        """최근 대화 컨텍스트 반환"""
        return self.conversation_history[-num_messages:] if self.conversation_history else []
    
    def get_conversation_summary(self) -> str:
        """대화 요약 생성"""
        if not self.conversation_history:
            return "새로운 대화입니다."
        
        user_messages = [msg for msg in self.conversation_history if msg['role'] == 'user']
        
        if len(user_messages) == 1:
            return f"사용자가 '{user_messages[0]['content'][:50]}...'에 대해 문의했습니다."
        else:
            topics = []
            for msg in user_messages[-3:]:  # 최근 3개 질문
                content = msg['content'][:30]
                topics.append(content)
            
            return f"최근 대화 주제: {', '.join(topics)}"
    
    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []

class IntentDetector:
    """사용자 의도 감지 클래스"""
    
    def __init__(self):
        self.intent_keywords = {
            'branding': {
                'primary': ['브랜드', '브랜딩', '로고', '아이덴티티', '포지셔닝'],
                'secondary': ['이미지', '컨셉', '차별화', '브랜드명', '네이밍']
            },
            'content': {
                'primary': ['콘텐츠', '포스트', '글', 'SNS', '인스타그램'],
                'secondary': ['유튜브', '블로그', '카피', '해시태그', '영상']
            },
            'targeting': {
                'primary': ['타겟', '고객', '타겟팅', '고객층', '페르소나'],
                'secondary': ['시장', '분석', '세그먼트', '오디언스', '소비자']
            },
            'general': {
                'primary': ['도움', '상담', '조언', '전략', '계획'],
                'secondary': ['어떻게', '방법', '팁', '가이드', '추천']
            }
        }
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """의도 감지"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            
            # Primary 키워드 (가중치 2)
            for keyword in keywords['primary']:
                if keyword in text_lower:
                    score += 2
            
            # Secondary 키워드 (가중치 1)  
            for keyword in keywords['secondary']:
                if keyword in text_lower:
                    score += 1
            
            intent_scores[intent] = score
        
        # 최고 점수 의도 선택
        primary_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[primary_intent]
        
        # 신뢰도 계산 (0-1)
        total_words = len(text.split())
        confidence = min(max_score / total_words, 1.0) if total_words > 0 else 0
        
        # 임계값 이하면 일반 의도로 분류
        if max_score == 0 or confidence < 0.1:
            primary_intent = 'general'
            confidence = 0.5
        
        return {
            'primary_intent': primary_intent,
            'confidence': confidence,
            'scores': intent_scores,
            'detected_keywords': self._extract_matched_keywords(text_lower, primary_intent)
        }
    
    def _extract_matched_keywords(self, text: str, intent: str) -> List[str]:
        """매칭된 키워드 추출"""
        if intent not in self.intent_keywords:
            return []
        
        matched = []
        all_keywords = (self.intent_keywords[intent]['primary'] + 
                       self.intent_keywords[intent]['secondary'])
        
        for keyword in all_keywords:
            if keyword in text:
                matched.append(keyword)
        
        return matched

class ContextBuilder:
    """컨텍스트 구성 클래스"""
    
    @staticmethod
    def build_llm_context(
        user_input: str,
        intent_result: Dict[str, Any],
        relevant_docs: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        agent_type: str
    ) -> List[Dict[str, str]]:
        """LLM용 컨텍스트 메시지 구성"""
        
        messages = []
        
        # 1. 시스템 프롬프트
        from config.prompts_config import get_system_prompt
        system_prompt = get_system_prompt(agent_type)
        messages.append({"role": "system", "content": system_prompt})
        
        # 2. 관련 문서 컨텍스트
        if relevant_docs:
            doc_context = "다음은 관련 참고 자료입니다:\n\n"
            for i, doc in enumerate(relevant_docs[:3], 1):
                doc_context += f"[참고자료 {i}] {doc['title']}\n"
                doc_context += f"출처: {doc['source']}\n"
                doc_context += f"내용: {doc['content'][:500]}...\n\n"
            
            messages.append({"role": "system", "content": doc_context})
        
        # 3. 대화 기록 (최근 3쌍)
        recent_history = conversation_history[-6:] if conversation_history else []
        for msg in recent_history:
            if msg['role'] in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # 4. 현재 사용자 입력
        messages.append({"role": "user", "content": user_input})
        
        return messages

# 전역 인스턴스들
conversation_manager = ConversationManager()
intent_detector = IntentDetector()
response_formatter = ResponseFormatter()

def process_user_input(
    user_input: str,
    rag_system,
    llm_client,
    agents: Dict[str, Any]
) -> Dict[str, Any]:
    """사용자 입력 전체 처리 파이프라인"""
    
    try:
        # 1. 의도 감지
        intent_result = intent_detector.detect_intent(user_input)
        primary_intent = intent_result['primary_intent']
        
        # 2. 문서 검색
        relevant_docs = rag_system.search_documents(user_input, top_k=3)
        
        # 3. 에이전트 선택
        if primary_intent in agents:
            selected_agent = agents[primary_intent]
        else:
            selected_agent = agents['branding']  # 기본 에이전트
        
        # 4. 컨텍스트 구성
        conversation_history = conversation_manager.get_recent_context()
        llm_messages = ContextBuilder.build_llm_context(
            user_input, intent_result, relevant_docs, conversation_history, primary_intent
        )
        
        # 5. LLM 응답 생성
        llm_response = llm_client.generate_response(llm_messages)
        
        # 6. 응답 포맷팅
        agent_name = selected_agent.config.get('name', 'AI 상담사')
        formatted_response = response_formatter.format_agent_response(
            llm_response, agent_name, primary_intent
        )
        formatted_response = response_formatter.add_action_items(
            formatted_response, primary_intent
        )
        
        # 7. 대화 기록 업데이트
        conversation_manager.add_message('user', user_input)
        conversation_manager.add_message('assistant', formatted_response, {
            'agent_type': primary_intent,
            'agent_name': agent_name,
            'intent_confidence': intent_result['confidence']
        })
        
        return {
            'response': formatted_response,
            'agent_name': agent_name,
            'agent_type': primary_intent,
            'confidence': intent_result['confidence'],
            'relevant_documents': relevant_docs,
            'context_used': len(relevant_docs) > 0,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"사용자 입력 처리 실패: {e}")
        return {
            'response': "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
            'agent_name': "시스템",
            'agent_type': "error",
            'confidence': 0,
            'relevant_documents': [],
            'context_used': False,
            'success': False,
            'error': str(e)
        }