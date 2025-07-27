"""
마케팅 분석 도구 API 테스트 클라이언트
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class MarketingAPIClient:
    """마케팅 API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def health_check(self) -> Dict[str, Any]:
        """헬스체크"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_blog_content(self, keyword: str, description: str = "") -> Dict[str, Any]:
        """블로그 콘텐츠 생성"""
        url = f"{self.base_url}/api/v1/content/blog"
        data = {
            "keyword": keyword,
            "description": description
        }
        
        try:
            print(f"🔄 블로그 콘텐츠 생성 중... (키워드: {keyword})")
            start_time = time.time()
            
            response = requests.post(url, json=data, timeout=120)
            result = response.json()
            
            elapsed_time = time.time() - start_time
            print(f"✅ 완료! (소요시간: {elapsed_time:.2f}초)")
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_instagram_content(self, keyword: str, description: str = "") -> Dict[str, Any]:
        """인스타그램 콘텐츠 생성"""
        url = f"{self.base_url}/api/v1/content/instagram"
        data = {
            "keyword": keyword,
            "description": description
        }
        
        try:
            print(f"🔄 인스타그램 콘텐츠 생성 중... (키워드: {keyword})")
            start_time = time.time()
            
            response = requests.post(url, json=data, timeout=120)
            result = response.json()
            
            elapsed_time = time.time() - start_time
            print(f"✅ 완료! (소요시간: {elapsed_time:.2f}초)")
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_naver_trends(self, keywords: list, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """네이버 트렌드 분석"""
        url = f"{self.base_url}/api/v1/analysis/naver-trends"
        data = {
            "keywords": keywords,
            "start_date": start_date,
            "end_date": end_date
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_instagram_hashtags(self, question: str, hashtags: list = None) -> Dict[str, Any]:
        """인스타그램 해시태그 분석"""
        url = f"{self.base_url}/api/v1/analysis/instagram-hashtags"
        data = {
            "question": question,
            "hashtags": hashtags
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_keywords(self, keyword: str, description: str = "") -> Dict[str, Any]:
        """관련 키워드 생성"""
        url = f"{self.base_url}/api/v1/keywords/generate"
        data = {
            "keyword": keyword,
            "description": description
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

def print_separator():
    """구분선 출력"""
    print("=" * 80)

def print_result(title: str, result: Dict[str, Any]):
    """결과 출력"""
    print(f"\n📊 {title}")
    print("-" * 60)
    
    if result.get("success"):
        if "blog_content" in result:
            # 블로그 콘텐츠 결과
            print(f"🎯 기본 키워드: {result.get('base_keyword')}")
            print(f"🔗 관련 키워드: {', '.join(result.get('related_keywords', [])[:5])}")
            print(f"⭐ 상위 키워드: {', '.join(result.get('top_keywords', []))}")
            
            blog_content = result.get('blog_content', {})
            if blog_content.get('full_content'):
                content = blog_content['full_content']
                print(f"\n📝 생성된 블로그 콘텐츠 (처음 500자):")
                print(content[:500] + "..." if len(content) > 500 else content)
            
            print(f"\n📈 단어 수: {blog_content.get('word_count', 0)}")
            print(f"⏱️ 처리 시간: {result.get('processing_time', 0):.2f}초")
            
        elif "instagram_content" in result:
            # 인스타그램 콘텐츠 결과
            print(f"🎯 기본 키워드: {result.get('base_keyword')}")
            print(f"🔗 관련 키워드: {', '.join(result.get('related_keywords', [])[:5])}")
            
            hashtag_analysis = result.get('hashtag_analysis', {})
            if hashtag_analysis.get('popular_hashtags'):
                print(f"📱 인기 해시태그: {' '.join(hashtag_analysis['popular_hashtags'][:10])}")
            
            instagram_content = result.get('instagram_content', {})
            if instagram_content.get('post_content'):
                print(f"\n📝 생성된 인스타그램 콘텐츠:")
                print(instagram_content['post_content'])
            
            if instagram_content.get('selected_hashtags'):
                print(f"\n#️⃣ 선택된 해시태그:")
                print(' '.join(instagram_content['selected_hashtags'][:20]))
            
            print(f"\n⏱️ 처리 시간: {result.get('processing_time', 0):.2f}초")
            
        elif "related_keywords" in result:
            # 키워드 생성 결과
            print(f"🎯 기본 키워드: {result.get('base_keyword')}")
            print(f"🔗 생성된 관련 키워드: {', '.join(result.get('related_keywords', []))}")
            
        else:
            # 기타 결과
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 오류 발생: {result.get('error', '알 수 없는 오류')}")

def run_basic_tests():
    """기본 테스트 실행"""
    client = MarketingAPIClient()
    
    print("🚀 마케팅 분석 도구 API 테스트 시작")
    print_separator()
    
    # 1. 헬스체크
    print("1️⃣ API 서버 상태 확인...")
    health = client.health_check()
    if "error" in health:
        print(f"❌ API 서버 연결 실패: {health['error']}")
        print("💡 먼저 API 서버를 실행해주세요: ./run_server.sh")
        return
    else:
        print(f"✅ API 서버 정상 작동: {health.get('status')}")
    
    print_separator()
    
    # 2. 키워드 생성 테스트
    print("2️⃣ 관련 키워드 생성 테스트...")
    keyword_result = client.generate_keywords("스킨케어", "여성 타겟 뷰티 제품")
    print_result("관련 키워드 생성", keyword_result)
    
    print_separator()
    
    # 3. 블로그 콘텐츠 생성 테스트
    print("3️⃣ 블로그 콘텐츠 생성 테스트...")
    blog_result = client.create_blog_content("홈트레이닝", "집에서 할 수 있는 운동")
    print_result("블로그 콘텐츠 생성", blog_result)
    
    print_separator()
    
    # 4. 인스타그램 콘텐츠 생성 테스트
    print("4️⃣ 인스타그램 콘텐츠 생성 테스트...")
    instagram_result = client.create_instagram_content("비건 화장품", "친환경 뷰티 제품")
    print_result("인스타그램 콘텐츠 생성", instagram_result)
    
    print_separator()
    print("✅ 모든 테스트 완료!")

def run_custom_test():
    """사용자 정의 테스트"""
    client = MarketingAPIClient()
    
    print("🎨 사용자 정의 테스트")
    print_separator()
    
    while True:
        print("\n다음 중 원하는 기능을 선택하세요:")
        print("1. 블로그 콘텐츠 생성")
        print("2. 인스타그램 콘텐츠 생성")
        print("3. 관련 키워드 생성")
        print("4. 네이버 트렌드 분석")
        print("5. 인스타그램 해시태그 분석")
        print("0. 종료")
        
        choice = input("\n선택 (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            keyword = input("키워드를 입력하세요: ").strip()
            description = input("설명을 입력하세요 (선택사항): ").strip()
            result = client.create_blog_content(keyword, description)
            print_result("블로그 콘텐츠 생성", result)
        elif choice == "2":
            keyword = input("키워드를 입력하세요: ").strip()
            description = input("설명을 입력하세요 (선택사항): ").strip()
            result = client.create_instagram_content(keyword, description)
            print_result("인스타그램 콘텐츠 생성", result)
        elif choice == "3":
            keyword = input("키워드를 입력하세요: ").strip()
            description = input("설명을 입력하세요 (선택사항): ").strip()
            result = client.generate_keywords(keyword, description)
            print_result("관련 키워드 생성", result)
        elif choice == "4":
            keywords_str = input("키워드들을 쉼표로 구분해서 입력하세요: ").strip()
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            result = client.analyze_naver_trends(keywords)
            print_result("네이버 트렌드 분석", result)
        elif choice == "5":
            question = input("질문을 입력하세요: ").strip()
            hashtags_str = input("해시태그들을 쉼표로 구분해서 입력하세요 (선택사항): ").strip()
            hashtags = [h.strip() for h in hashtags_str.split(",") if h.strip()] if hashtags_str else None
            result = client.analyze_instagram_hashtags(question, hashtags)
            print_result("인스타그램 해시태그 분석", result)
        else:
            print("❌ 잘못된 선택입니다.")
        
        print_separator()

def main():
    """메인 함수"""
    # if len(sys.argv) > 1 and sys.argv[1] == "--custom":
    #     run_custom_test()
    # else:
    #     run_basic_tests()
        
    # 사용자 정의 테스트 옵션
    user_input = input("\n🎨 사용자 정의 테스트를 실행하시겠습니까? (y/N): ").strip().lower()
    if user_input in ['y', 'yes']:
        run_custom_test()

if __name__ == "__main__":
    main()
