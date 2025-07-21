import { useState,useEffect } from "react";
import { useSearchParams,useNavigate } from "react-router-dom";

import ReactMarkdown from "react-markdown";

import useChat from "../../hooks/useChat";
import Sidebar from "../../components/Sidebar";
import FeedbackModal from "../../components/Feedback";

import styles from './ChatPage.module.css';
import React from "react";

const exampleQuestions = [
  { category: "사업기획", question: "온라인 쇼핑몰을 운영하려는데 초기 사업계획을 어떻게 세우면 좋을까요?", agent: "planner"},
  { category: "마케팅", question: "인스타그램에서 제품을 효과적으로 홍보하려면 어떤 팁이 있을까요?", agent: "marketing" },
  { category: "고객관리", question: "리뷰에 불만 글이 달렸을 때 어떻게 대응해야 좋을까요?", agent: "crm" },
  { category: "업무지원", question: "매번 반복되는 예약 문자 전송을 자동화할 수 있을까요?", agent: "task"  },
];



function ChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams()
  const agent = searchParams.get("agent") || "unified_agent"
  const initialQuestion = searchParams.get("question") || ""
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [category, setCategory] = useState(agent?.replace("_agent", "") || "general");


  const {
    conversationId,
    messages,
    userInput,
    setUserInput, 
    handleInputChange,
    handleSend,
    handleExampleClick,
    startNewConversation,
    textareaRef, 
    scrollRef 
  } = useChat();

  // useEffect(() => {
  //   startNewConversation();
  // }, [startNewConversation]);

  useEffect(() => {
    startNewConversation(agent)
    if (initialQuestion) {
      setUserInput(initialQuestion)
      setTimeout(() => {
        document.querySelector("form").dispatchEvent(
          new Event("submit", { bubbles: true })
        )
      }, 100)
    }
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar
        onSelectAgent={(type) => {
          if (type === "home") {
            navigate("/"); // 또는 navigate("/main");
          } else {
            navigate(`/chat?agent=${type}`);
            startNewConversation(type);
          }
        }}
      />



      <div className="flex-1 flex flex-col px-8 py-6 relative">
        {/* ✅ 예시 카드 및 타이틀: 메시지 없을 때만 */}
        {messages.length === 0 && (
          <>
            <h2 className="font-semibold mb-3">팅커벨 활용하기 &gt;</h2>
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
          </>
        )}

        {/* ✅ 채팅 메시지 영역 */}
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
                  <div className="w-10 h-10 rounded-full bg-[#046BBF] flex items-center justify-center shadow shrink-0">
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
          <div ref={scrollRef} /> 
        </div>

        {/* ✅ 입력창 */}
        <form
          className="absolute bottom-4 left-8 right-8 bg-white shadow-md rounded-2xl px-4 py-3 flex flex-col space-y-2"
          onSubmit={handleSend}
        >
          <textarea
            ref={textareaRef}
            placeholder="추가 질문하기 ..."
            value={userInput}
            onChange={handleInputChange}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault(); // 줄바꿈 막기
                handleSend(e); // form submit 동작 호출
              }
            }}
            rows={1}
            className="w-full max-h-[200px] bg-white text-sm px-2 py-2 rounded-md border-none outline-none resize-none overflow-y-auto"
          />

          <div className="flex justify-end">
            <button
              type="submit"
              className="w-8 h-8 bg-gray-200 hover:bg-gray-300 rounded-md flex items-center justify-center"
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
            onSubmit={async () => {
              try {
                const response = await fetch("/api/feedback", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    user_id: 2, // 일단 하드 코딩
                    conversation_id: 30,//conversationId,
                    rating,
                    comment,
                    category,
                  }),
                });

                const result = await response.json();
                console.log("피드백 응답:", result);

                if (result.status === "success") {
                  alert("피드백이 등록되었습니다!");
                } else {
                  alert("피드백 전송에 실패했습니다.");
                }
              } catch (error) {
                console.error("피드백 전송 오류:", error);
                alert("서버 오류로 피드백을 전송하지 못했어요.");
              }

              setShowFeedbackModal(false);
              setRating(0);
              setComment("");
            }}
          />
        )}
      </div>
    </div>
  );
}

export default ChatPage;
