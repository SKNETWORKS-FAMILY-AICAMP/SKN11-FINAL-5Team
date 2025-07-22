"""
템플릿 추천 서비스
사용자 요청에 맞는 마케팅 템플릿을 추천하는 서비스
"""

from typing import List, Dict, Any
import sys
import os

# 상위 디렉토리의 shared_modules 접근을 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from shared_modules import get_templates_by_type


class TemplateRecommender:
    """템플릿 추천기"""
    
    TEMPLATE_KEYWORDS = {
        "생일": "생일/기념일", "기념일": "생일/기념일", "축하": "생일/기념일",
        "리뷰": "리뷰 요청", "후기": "리뷰 요청", "평가": "리뷰 요청",
        "예약": "예약", "설문": "설문 요청",
        "감사": "구매 후 안내", "출고": "구매 후 안내", "배송": "구매 후 안내",
        "재구매": "재구매 유도", "재방문": "재방문", "다시": "재구매 유도",
        "VIP": "고객 맞춤 메시지", "맞춤": "고객 맞춤 메시지", "특별": "고객 맞춤 메시지",
        "이벤트": "이벤트 안내", "할인": "이벤트 안내", "세일": "이벤트 안내"
    }
    
    TEMPLATE_QUERY_KEYWORDS = [
        "템플릿", "문자", "메시지", "문구", "추천", "예시", 
        "샘플", "양식", "포맷", "멘트", "말", "텍스트"
    ]
    
    @classmethod
    def is_template_query(cls, text: str) -> bool:
        """템플릿 쿼리 감지"""
        text_lower = text.lower()
        is_template = any(keyword in text_lower for keyword in cls.TEMPLATE_QUERY_KEYWORDS)
        
        print(f"📝 템플릿 쿼리 감지: {is_template} (입력: '{text}')")
        return is_template
    
    @classmethod
    def extract_template_keyword(cls, text: str) -> str:
        """템플릿 키워드 추출"""
        text_lower = text.lower()
        
        for keyword, template_type in cls.TEMPLATE_KEYWORDS.items():
            if keyword in text_lower:
                print(f"🎯 키워드 '{keyword}' → 템플릿 타입 '{template_type}'")
                return template_type
        
        print("🔍 특정 키워드 없음 → '전체' 템플릿")
        return "전체"
    
    @classmethod
    def recommend_templates(cls, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """템플릿 추천"""
        try:
            keyword = cls.extract_template_keyword(query)
            print(f"📌 추출된 템플릿 키워드: {keyword}")
            
            # DB에서 템플릿 조회
            templates = get_templates_by_type(keyword)
            print(f"📋 조회된 템플릿 수: {len(templates)}")
            
            # 템플릿이 없으면 전체 템플릿에서 검색
            if not templates and keyword != "전체":
                print("⚠️ 특정 타입 템플릿 없음, 전체에서 검색...")
                templates = get_templates_by_type("전체")
            
            # 디버깅을 위한 템플릿 정보 출력
            for i, template in enumerate(templates[:3]):  # 처음 3개만
                print(f"템플릿 {i+1}: {template.get('title', 'No Title')}")
            
            return templates[:limit]
            
        except Exception as e:
            print(f"❌ 템플릿 추천 오류: {e}")
            return []
    
    @classmethod
    def get_template_categories(cls) -> List[str]:
        """사용 가능한 템플릿 카테고리 반환"""
        return list(set(cls.TEMPLATE_KEYWORDS.values()))
    
    @classmethod
    def get_template_by_id(cls, template_id: int) -> Dict[str, Any]:
        """ID로 특정 템플릿 조회"""
        try:
            # 실제 구현에서는 데이터베이스에서 조회
            # 여기서는 예시로 빈 딕셔너리 반환
            return {}
        except Exception as e:
            print(f"❌ 템플릿 조회 오류: {e}")
            return {}
