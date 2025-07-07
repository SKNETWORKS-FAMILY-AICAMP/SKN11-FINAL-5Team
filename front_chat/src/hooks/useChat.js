import { useState, useRef, useEffect } from "react";
import { getAgentPort } from "../config/agentConfig"; // ✅ 포트 매핑 유틸

function useChat() {
  const [conversationId, setConversationId] = useState(3);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [agentConfig, setAgentConfig] = useState({
    type: "unified_agent",
    port: getAgentPort("unified_agent"),
  });

  const textareaRef = useRef(null);
  const scrollRef = useRef(null);

  const initializeConversation = (newId, agent) => {
    setConversationId(newId);
    setMessages([]);
    setUserInput("");
    setAgentConfig({
      type: agent,
      port: getAgentPort(agent),
    });
  };
  
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // const startNewConversation = (agent = "unified_agent") => {
  //   //const newId = Date.now();
  //   setConversationId(newId);
  //   setMessages([]);
  //   setUserInput("");
  //   setAgentConfig({
  //     type: agent,
  //     port: getAgentPort(agent),
  //   });
  // };
  const startNewConversation = async (agent = "unified_agent") => {
    try {
      const response = await fetch("/api/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 3,
          conversation_type: agent.replace("_agent", "") || "general",
        }),
      });

      if (!response.ok) throw new Error("서버 응답 실패");

      const result = await response.json();
      if (result.status === "success") {
        const newId = result.data.conversation_id;
        initializeConversation(newId, agent);
        return;
      }

      // 서버가 실패 응답 준 경우
      console.warn("대화 세션 생성 실패:", result);
    } catch (error) {
      console.warn("대화 세션 서버 요청 실패, 로컬 ID로 대체:", error.message);
    }

    // 서버 없거나 실패 → 임시 ID 생성
    const fallbackId = Date.now();
    initializeConversation(fallbackId, agent);
  };


  const handleSend = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const currentInput = userInput;

    setUserInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMessage = { sender: "user", text: currentInput };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    const payload =
    agentConfig.type === "unified_agent"
      ? {
          user_id: "3", //하드코딩
          message: currentInput,
          conversation_id: conversationId,
        }
      : {
          customer_id: "3", //하드코딩
          question: currentInput,
          conversation_id: conversationId,
        };

  const endpoint =
    agentConfig.type === "unified_agent"
      ? `http://localhost:${agentConfig.port}/query`
      : `http://localhost:${agentConfig.port}/agent/query`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });


    // const endpoint =
    // agentConfig.type === "unified_agent"
    // ? `http://localhost:${agentConfig.port}/query`
    // : `http://localhost:${agentConfig.port}/agent/query`;

    // const response = await fetch(endpoint, {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({
    //     customer_id: "3", // 일단 하드 코딩
    //     conversation_id: conversationId,
    //     question: currentInput,
    //     //agent_type: agentConfig.type,
    //   }),
    // });

    const res = await response.json();
    const agentMessage = { sender: "agent", text: res.answer };
    setMessages((prev) => [...prev, agentMessage]);
  };

  const handleInputChange = (e) => {
    setUserInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  };

  const handleExampleClick = (text) => {
    setUserInput(text);
    setTimeout(() => {
      document.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true }));
    }, 0);
  };

  return {
    conversationId,
    messages,
    userInput,
    setUserInput, 
    agentConfig,
    handleInputChange,
    handleSend,
    handleExampleClick,
    startNewConversation,
    textareaRef,
    scrollRef,
  };
}

export default useChat;

