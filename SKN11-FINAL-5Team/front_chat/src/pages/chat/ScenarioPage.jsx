import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import FeedbackModal from '../../components/Feedback';
import styles from './ChatPage.module.css';

// 시나리오 데이터
const marketingScenario = {
  messages: [
    {
      sender: 'user',
      text: '새로 들어온 소이캔들 홍보용 인스타 포스팅 만들어줘!\n감성적이고 따뜻한 느낌으로 부탁해',
      delay: 1000
    },
    {
      sender: 'agent',
      text: `**이런 내용으로 작성할까요?**

"집에 돌아오는 순간, 따뜻한 향기가 나를 맞아줘
새로 들어온 프리미엄 소이캔들로 당신만의 힐링 공간을 만들어보세요!
100% 천연 소이왁스로 안전하고 은은한 라벤더향으로 마음까지 편안하게"

해시태그: #소이캔들 #홈데코 #집꾸미기 #힐링템 #라벤더향 #천연캔들

추천 업로드 시간: 저녁 7-8시 (퇴근 후 집에서 편안한 시간대)`,
      delay: 3000
    },
    {
      sender: 'user',
      text: '감성적인 느낌 너무 좋다! 추천 시간으로 업로드 해줘',
      delay: 2000
    },
    {
      sender: 'agent',
      text: `✅ **업로드 완료!**

저녁 7시에 맞춰 인스타그램에 포스팅이 업로드되었습니다.

📊 **예상 성과**
- 도달률: 약 1,200명
- 추정 참여율: 8-12%
- 예상 좋아요: 80-120개

포스팅 성과는 24시간 후 상세 리포트로 확인하실 수 있습니다! 🎯`,
      delay: 2000
    }
  ]
};

const exampleQuestions = [
  { category: "사업기획", question: "온라인 쇼핑몰을 운영하려는데 초기 사업계획을 어떻게 세우면 좋을까요?", agent: "planner"},
  { category: "마케팅", question: "인스타그램에서 제품을 효과적으로 홍보하려면 어떤 팁이 있을까요?", agent: "marketing" },
  { category: "고객관리", question: "리뷰에 불만 글이 달렸을 때 어떻게 대응해야 좋을까요?", agent: "crm" },
  { category: "업무지원", question: "매번 반복되는 예약 문자 전송을 자동화할 수 있을까요?", agent: "task"  },
];


function ScenarioPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [category, setCategory] = useState("marketing");
  
  const textareaRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const startScenario = () => {
    setMessages([]);
    setIsPlaying(true);
    setIsComplete(false);
    setUserInput('');

    let messageIndex = 0;
    
    const addNextMessage = () => {
      if (messageIndex >= marketingScenario.messages.length) {
        setIsPlaying(false);
        setIsComplete(true);
        return;
      }
      
      const currentMessage = marketingScenario.messages[messageIndex];
      
      setTimeout(() => {
        setMessages(prev => [...prev, currentMessage]);
        messageIndex++;
        addNextMessage();
      }, currentMessage.delay);
    };
    
    addNextMessage();
  };

  const resetScenario = () => {
    setMessages([]);
    setIsPlaying(false);
    setIsComplete(false);
    setUserInput('');
  };

  const handleExampleClick = (text) => {
    setUserInput(text);
  };

  const handleInputChange = (e) => {
    setUserInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    // 사용자 메시지 추가
    const userMessage = {
      sender: 'user',
      text: userInput
    };
    setMessages(prev => [...prev, userMessage]);
    
    // 시나리오 자동 진행 중단
    setIsPlaying(false);
    
    // 사용자 입력 초기화
    setUserInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // AI 응답 생성
    setTimeout(() => {
      const aiResponse = generateScenarioResponse(userInput);
      setMessages(prev => [...prev, {
        sender: 'agent',
        text: aiResponse
      }]);
    }, 1000);
  };

  const generateScenarioResponse = (userInput) => {
    const input = userInput.toLowerCase();
    
    // 마케팅 관련 키워드 기반 응답
    if (input.includes('인스타') || input.includes('인스타그램') || input.includes('sns')) {
      return `📱 **인스타그램 마케팅 전략**

인스타그램에서 효과적인 마케팅을 위해서는:

• **콘텐츠 전략**: 감성적이고 고품질의 비주얼 이미지
• **해시태그**: 타겟 고객이 검색할 만한 키워드 활용
• **업로드 시간**: 7-9시 저녁 시간대 추천
• **인플루언서 협업**: 마이크로 인플루언서 활용

어떤 대부분을 더 자세히 알고 싶으신가요?`;
    }
    
    if (input.includes('소이캔들') || input.includes('캔들') || input.includes('제품')) {
      return `🕯️ **소이캔들 마케팅 인사이트**

소이캔들은 환경친화적이고 건강한 대안으로 인기가 높아지고 있어요!

**타겟 고객층:**
• 25-40세 여성 (홈리빙/인테리어에 관심 많은)
• 환경의식이 높은 소비자
• 집에서의 휴식/힐링을 중요시하는 사람들

**마케팅 포인트:**
• 자연 성분 100% 강조
• 장시간 연소 가능
• 은은한 향기로 힐링 효과

추가 전략이 더 필요하신가요?`;
    }
    
    if (input.includes('홍보') || input.includes('광고') || input.includes('포스팅')) {
      return `🎯 **효과적인 홍보 전략**

**1. 콘텐츠 기획**
• 스토리텔링 방식 사용 (일상 속 캔들 사용법)
• 비포어&애프터 비교 이미지
• 사용자 후기/리뷰 활용

**2. 채널 다변화**
• 인스타그램 피드 + 스토리
• 네이버 블로그 상세 리뷰
• 유튜브 만들기 영상

**3. 성과 측정**
• 도달률, 참여률 추적
• 전환율 분석
• ROI 계산

어떤 부분을 우선적으로 실행하고 싶으신가요?`;
    }
    
    if (input.includes('분석') || input.includes('성과') || input.includes('결과') || input.includes('리포트')) {
      return `📈 **마케팅 성과 분석 방법**

**핵심 지표 (KPI):**
• **도달률**: 예상 1,200명 (현재 진행 중)
• **참여률**: 목표 8-12%
• **클릭률**: 링크 클릭 수 측정
• **전환율**: 실제 구매로 이어진 비율

**분석 도구:**
• 인스타그램 인사이트
• 구글 애널리틱스 연동
• 네이버 서치어드바이저

현재 포스팅 후 24시간이 지나면 상세 성과 리포트를 제공드릴 예정입니다!

어떤 지표를 가장 우선적으로 보고 싶으신가요?`;
    }
    
    if (input.includes('안녕') || input.includes('하이') || input.includes('반가') || input.includes('고마워')) {
      return `안녕하세요! 😊 마케팅 전담 AI 어시스턴트입니다.

현재 소이캔들 마케팅 캠페인을 진행 중이에요!

**오늘 도와드릴 수 있는 일:**
• 마케팅 전략 수립
• 콘텐츠 기획 및 제작
• 성과 분석 및 리포트
• 경쟁사 분석

무엇을 도와드릴까요?`;
    }
    
    if (input.includes('고객') || input.includes('타겟') || input.includes('대상')) {
      return `🎯 **타겟 고객 분석**

**주요 고객층:**
• **연령대**: 25-40세
• **성별**: 여성 70%, 남성 30%
• **관심사**: 홈데코, 인테리어, 힐링, 우아한 라이프스타일
• **소비패턴**: 친환경적이고 프리미엄 제품 선호

**고객 니즈:**
• 집에서의 휴식과 힐링
• 안전하고 자연스러운 제품
• 인스타그램 감성 콘텐츠

**마케팅 메시지:**
"집에서의 소중한 힐링 시간"을 강조하여 감성적 어필

어떤 고객층에 대해 더 자세히 알고 싶으신가요?`;
    }
    
    // 기본 응답
    return `🤔 흥미로운 질문이네요!

마케팅 캠페인과 관련해서 도와드릴 수 있는 분야:

• **소이캔들 마케팅 전략**
• **인스타그램 콘텐츠 기획**
• **성과 분석 및 리포트**
• **고객 분석 및 타겟팅**
• **경쟁사 리서치**

어떤 부분에 대해 더 자세히 알고 싶으신가요?`;
  };

  return (
    <div className="flex h-screen">
      <Sidebar
        onSelectAgent={(type) => {
          if (type === "home") {
            navigate("/");
          } else {
            navigate(`/chat?agent=${type}`);
          }
        }}
      />

      <div className={`flex-1 flex ${isComplete ? 'space-x-6' : ''}`}>
        {/* 메인 채팅 영역 */}
        <div className={`${isComplete ? 'w-2/3' : 'w-full'} flex flex-col px-8 py-6 relative transition-all duration-300`}>
          {/* 타이틀과 예시 카드: 항상 표시 */}
          <h2 className="font-semibold mb-3">자주 묻는 질문 &gt;</h2>
          
          {/* 시나리오 시작 버튼: 메시지 없을 때만 */}
          {messages.length === 0 && !isPlaying && (
            <div className="mb-6">
              <button
                onClick={startScenario}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors duration-200 flex items-center gap-2"
              >
                <span>🎬</span>
                마케팅 시나리오 체험하기
              </button>
            </div>
          )}
          
          {/* 예시 질문 카드: 항상 표시 */}
          <div className="flex space-x-3 mb-6">
            {exampleQuestions.map((item, idx) => (
              <div
                key={idx}
                className="bg-white rounded-lg shadow px-4 py-3 cursor-pointer hover:shadow-md"
                onClick={() => handleExampleClick(item.question)}
              >
                <div className="font-bold mb-2">{item.category}</div>
                <div className="text-sm text-gray-700">{item.question}</div>
              </div>
            ))}
          </div>

          {/* 채팅 메시지 영역 */}
          <div className="flex-1 space-y-4 overflow-y-auto pb-24">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex items-start ${
                  idx === 0 && msg.sender === "user" ? "mt-6" : ""
                }`}
              >
                {msg.sender === "user" ? (
                  <div className="flex flex-row-reverse items-end ml-auto space-x-reverse space-x-2">
                    {/* 고양이 아이콘 */}
                    <div className="w-10 h-10 rounded-full flex items-center justify-center shadow shrink-0">
                      <img src="/images/cat.png" className="w-8 h-8" alt="사용자" />
                    </div>

                    {/* 유저 말풍선 */}
                    <div className={styles["user-bubble-wrapper"]}>
                      <div className={styles["user-bubble"]}>
                        {msg.text}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-start w-full">
                    <div className="flex flex-col space-y-2 max-w-[70%] mr-auto">
                      <div className="bg-gray-100 text-gray-800 px-4 py-3 rounded-none shadow-md border border-gray-200 whitespace-pre-line">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                      <div className="mt-3 text-sm text-gray-500 flex items-center space-x-4">
                        <span>이 답변이 도움이 되었나요?</span>
                        <button className="flex items-center space-x-1 hover:opacity-80">
                          <img src="/images/good.png" className="w-4 h-4" alt="좋아요" />
                          <span>좋아요</span>
                        </button>
                        <button className="flex items-center space-x-1 hover:opacity-80">
                          <img src="/images/bad.png" className="w-4 h-4" alt="별로예요" />
                          <span>별로예요</span>
                        </button>
                        <button className="flex items-center space-x-1 hover:opacity-80" onClick={() => setShowFeedbackModal(true)}>
                          <img src="/images/comment.png" className="w-4 h-4" alt="상세 피드백" />
                          <span>상세 피드백</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* 로딩 인디케이터 */}
            {isPlaying && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 px-4 py-3 rounded-none shadow-md border border-gray-200">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>

          {/* 입력창 */}
          <form
            className="absolute bottom-4 left-8 right-8 bg-white shadow-md rounded-2xl px-4 py-3 flex flex-col space-y-2"
            onSubmit={handleSend}
          >
            <textarea
              ref={textareaRef}
              placeholder={isPlaying ? "실행 중입니다..." : "추가 질문하기 ..."}
              value={userInput}
              onChange={handleInputChange}
              disabled={isPlaying}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              rows={1}
              className={`w-full max-h-[200px] bg-white text-sm px-2 py-2 rounded-md border-none outline-none resize-none overflow-y-auto ${
                isPlaying ? 'opacity-50 cursor-not-allowed text-gray-400' : 'text-gray-900'
              }`}
            />

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isPlaying}
                className={`w-8 h-8 flex items-center justify-center rounded-md ${
                  isPlaying 
                    ? 'bg-gray-200 cursor-not-allowed' 
                    : 'bg-gray-200 hover:bg-gray-300'
                }`}
              >
                <img src="/images/up_arrow.png" className="w-4 h-4" alt="전송" />
              </button>
            </div>
          </form>

          {showFeedbackModal && (
            <FeedbackModal
              rating={rating}
              setRating={setRating}
              comment={comment}
              setComment={setComment}
              category={category}
              setCategory={setCategory}
              onClose={() => setShowFeedbackModal(false)}
              onSubmit={() => {
                alert("시나리오 데모에서는 피드백이 저장되지 않습니다.");
                setShowFeedbackModal(false);
                setRating(0);
                setComment("");
              }}
            />
          )}
        </div>

        {/* 업무 테이블 영역 - 시나리오 완료 후에만 표시 */}
        {isComplete && (
          <div className="w-1/3 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-bold mb-4 text-gray-800">📊 마케팅 업무 현황</h3>
              
              {/* 완료된 작업 */}
              <div className="mb-6">
                <h4 className="font-semibold text-green-600 mb-3 flex items-center">
                  <span className="mr-2">✅</span>
                  완료된 작업
                </h4>
                <div className="space-y-2">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="font-medium text-green-800">소이캔들 인스타 포스팅</div>
                    <div className="text-sm text-green-600">저녁 7시 업로드 완료</div>
                    <div className="text-xs text-gray-500 mt-1">예상 도달률: 1,200명</div>
                  </div>
                </div>
              </div>

              {/* 진행 중인 작업 */}
              <div className="mb-6">
                <h4 className="font-semibold text-yellow-600 mb-3 flex items-center">
                  <span className="mr-2">🔄</span>
                  진행 중인 작업
                </h4>
                <div className="space-y-2">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="font-medium text-yellow-800">성과 분석 대기</div>
                    <div className="text-sm text-yellow-600">24시간 후 리포트 생성 예정</div>
                  </div>
                </div>
              </div>

              {/* 예정된 작업 */}
              <div>
                <h4 className="font-semibold text-blue-600 mb-3 flex items-center">
                  <span className="mr-2">📅</span>
                  예정된 작업
                </h4>
                <div className="space-y-2">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="font-medium text-blue-800">후속 마케팅 기획</div>
                    <div className="text-sm text-blue-600">성과 분석 후 진행</div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="font-medium text-blue-800">고객 반응 모니터링</div>
                    <div className="text-sm text-blue-600">주간 리포트 작성</div>
                  </div>
                </div>
              </div>

              {/* 통계 요약 */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <h4 className="font-semibold text-gray-700 mb-3">📈 이번 주 요약</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 bg-gray-100 rounded">
                    <div className="text-lg font-bold text-gray-800">1</div>
                    <div className="text-xs text-gray-600">완료된 캠페인</div>
                  </div>
                  <div className="text-center p-2 bg-gray-100 rounded">
                    <div className="text-lg font-bold text-gray-800">3</div>
                    <div className="text-xs text-gray-600">예정된 작업</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScenarioPage;
