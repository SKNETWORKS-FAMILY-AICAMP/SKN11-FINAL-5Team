import { useState } from "react";

function Sidebar({ onSelectAgent }) {
  const [expanded, setExpanded] = useState(false);

  const menuItems = [
    { icon: "/images/plus.png", label: "새 채팅 시작하기", type: "unified_agent" },
    { icon: "/images/home.png", label: "상담 메인화면", type: "home" },
    { icon: "/images/pencil.png", label: "사업기획 에이전트", type: "planner" },
    { icon: "/images/megaphone.png", label: "마케팅 에이전트", type: "marketing" },
    { icon: "/images/paw.png", label: "업무 지원 에이전트", type: "task" },
    { icon: "/images/tele.png", label: "고객 관리 에이전트", type: "crm" },
    { icon: "/images/heart.png", label: "멘탈 케어 에이전트", type: "mentalcare" },
  ];

  return (
    <div
      className={`${
        expanded ? "w-56" : "w-16"
      } bg-blue-200 min-h-screen flex flex-col py-4 px-2 transition-all duration-300`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div className="flex flex-col space-y-2 mb-10">
        {menuItems.map((item, idx) => (
          <div
            key={idx}
            onClick={() => onSelectAgent(item.type)}
            className={`flex items-center gap-3 transition-all duration-200 ${
              idx === 0
                ? "text-blue-700 font-semibold hover:bg-blue-50 cursor-pointer"
                : "text-gray-800 hover:bg-blue-100 cursor-pointer"
            } ${expanded ? "px-3 py-2 rounded-full" : "justify-center"}`}
          >
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow">
              <img src={item.icon} alt={item.label} className="w-5 h-5" />
            </div>
            {expanded && (
              <span className="whitespace-nowrap text-sm">{item.label}</span>
            )}
          </div>
        ))}
      </div>

      {/* ✅ 채팅 목록 예시 */}
      {expanded && (
        <div className="px-2">
          <div className="text-xs text-gray-500 font-bold px-2 mb-2 mt-6">채팅</div>
          <div className="text-sm px-2 py-1 rounded cursor-pointer hover:bg-blue-100 text-blue-800">
            현재 채팅
          </div>
          <div className="space-y-1">
            {["이전 채팅 1", "이전 채팅 2", "이전 채팅 3", "이전 채팅 4", "이전 채팅 5"].map(
              (chat, i) => (
                <div
                  key={i}
                  className="text-sm px-2 py-1 rounded hover:bg-blue-100 cursor-pointer"
                >
                  {chat}
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Sidebar;
