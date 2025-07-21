// import { useNavigate } from "react-router-dom"

// const agents = [
//   { id: "business", name: "사업기획", icon: "/images/cat.png" },
//   { id: "marketing", name: "마케팅", icon: "/images/fish.png" },
//   { id: "customer", name: "고객관리", icon: "/images/foot.png" },
//   { id: "support", name: "업무지원", icon: "/images/star.png" },
//   { id: "mental", name: "멘탈케어", icon: "/images/cat_mental_care.png" }
// ]

// function MainPage() {
//   const navigate = useNavigate()
//   const [input, setInput] = useState("")

//   const handleSearch = (e) => {
//     e.preventDefault()
//     const encoded = encodeURIComponent(input.trim())
//     if (encoded) {
//       navigate(`/chat?agent=unified_agent&question=${encoded}`)
//     }
//   }

//   return (
//     <div className="min-h-screen bg-gradient-to-b from-blue-100 to-blue-200 flex flex-col items-center px-4 py-12">
//       {/* 헤더 */}
//       <header className="w-full flex justify-between items-center mb-12 px-4">
//         <h1 className="text-2xl font-bold text-gray-800">TinkerBell</h1>
//         <button className="p-2 hover:bg-white hover:bg-opacity-20 rounded">
//           <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
//           </svg>
//         </button>
//       </header>

//       {/* 중앙 질문 */}
//       <h2 className="text-xl font-semibold text-gray-800 mt-20 mb-10">무엇을 도와드릴까요?</h2>

//       {/* 검색창 */}
//         <form onSubmit={handleSearch} className="flex w-full max-w-md mb-4">
//             <input
//                 type="text"
//                 placeholder="질문을 입력해주세요..."
//                 className="flex-1 h-12 px-4 rounded-l-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
//             />
//             <button
//                 type="submit"
//                 className="h-12 w-12 bg-blue-500 text-white flex items-center justify-center rounded-r-full hover:bg-blue-600"
//             >
//                 <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
//                 </svg>
//             </button>
//         </form>

//       {/* 바로 시작하기 버튼 */}
//       <button
//         onClick={() => navigate("/chat")}
//         className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2 rounded-full mb-16"
//       >
//         바로 시작하기
//       </button>

//       {/* 에이전트 섹션 */}
//       <div className="w-full max-w-4xl text-left  mt-20 mb-4 text-gray-700 font-medium">
//         에이전트 바로가기 &gt;
//       </div>

//       <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 w-full max-w-4xl">
//         {agents.map((agent) => (
//           <div
//             key={agent.id}
//             className="bg-white rounded-lg shadow hover:shadow-lg p-4 flex flex-col items-center cursor-pointer"
//             onClick={() => navigate(`/chat?agent=${agent.id}`)}
//           >
//             <img src={agent.icon} alt={agent.name} className="w-12 h-12 mb-2" />
//             <p className="text-sm font-semibold text-gray-800">{agent.name}</p>
//           </div>
//         ))}
//       </div>
//     </div>
//   )
// }

// export default MainPage

import { useNavigate } from "react-router-dom"
import { useState } from "react"

const agents = [
  { id: "planner", name: "사업기획", icon: "/images/cat.png" },
  { id: "marketing", name: "마케팅", icon: "/images/fish.png" },
  { id: "crm", name: "고객관리", icon: "/images/foot.png" },
  { id: "task", name: "업무지원", icon: "/images/star.png" },
  { id: "mentalcare", name: "멘탈케어", icon: "/images/cat_mental_care.png" }
];

function MainPage() {
  const navigate = useNavigate()
  const [input, setInput] = useState("")

  const handleSearch = (e) => {
    e.preventDefault()
    const encoded = encodeURIComponent(input.trim())
    if (encoded) {
      navigate(`/chat?agent=unified_agent&question=${encoded}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-blue-200 flex flex-col items-center px-4 py-12">
      {/* 헤더 */}
      <header className="w-full flex justify-between items-center mb-12 px-4">
        <h1 className="text-2xl font-bold text-gray-800">TinkerBell</h1>
        <button className="p-2 hover:bg-white hover:bg-opacity-20 rounded">
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </header>

      {/* 중앙 질문 */}
      <h2 className="text-xl font-semibold text-gray-800 mt-20 mb-10">무엇을 도와드릴까요?</h2>

      {/* 검색창 */}
      <form onSubmit={handleSearch} className="flex w-full max-w-md mb-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="질문을 입력해주세요..."
          className="flex-1 h-12 px-4 rounded-l-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          className="h-12 w-12 bg-blue-500 text-white flex items-center justify-center rounded-r-full hover:bg-blue-600"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </form>

      {/* 바로 시작하기 버튼 */}
      <button
        onClick={() => navigate("/chat?agent=unified_agent")}
        className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2 rounded-full mb-16"
      >
        바로 시작하기
      </button>

      {/* 에이전트 섹션 */}
      <div className="w-full max-w-4xl text-left mt-20 mb-4 text-gray-700 font-medium">
        에이전트 바로가기 &gt;
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 w-full max-w-4xl">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white rounded-lg shadow hover:shadow-lg p-4 flex flex-col items-center cursor-pointer"
            onClick={() => navigate(`/chat?agent=${agent.id}`)}
          >
            <img src={agent.icon} alt={agent.name} className="w-12 h-12 mb-2" />
            <p className="text-sm font-semibold text-gray-800">{agent.name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MainPage
