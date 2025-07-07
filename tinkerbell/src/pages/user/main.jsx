import { Link } from "react-router-dom";

function Main() {
  return (
    <div className="min-h-screen bg-[#044BD9] text-white relative">
      {/* 상단 헤더 영역 */}
      <div className="absolute top-6 right-6 flex items-center space-x-6 text-black font-medium z-10">
        <Link to="/signup" className="hover:underline">가입하기</Link>
        <Link to="/signin" className="hover:underline">로그인</Link>
        <Link to="#" className="hover:underline">FAQ</Link>
        <img src="/images/cat_face.png" alt="프로필" className="w-8 h-8 rounded-full" />
      </div>

      {/* 좌측 상단 로고 */}
      <div className="absolute top-6 left-6 text-2xl font-extrabold text-black z-10">
        TinkerBell
      </div>

      {/* 메인 컨텐츠 영역 */}
      <div className="flex flex-col justify-center h-full px-16">
        <div className="flex items-center justify-between">
          {/* 중앙 좌측 텍스트 */}
          <div className="absolute left-[7%] top-[30%] text-white text-7xl font-bold drop-shadow-lg leading-tight">
            <h1 className="text-7xl font-extrabold text-white drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-snug">
              혼자서도<br />충분해요!
            </h1>
          </div>

          {/* 오른쪽 텍스트 (당신의 든든한 AI 비즈니스 팀) */}
          <div className="absolute top-[9%] right-[3%] text-right">
            <p className="text-7xl font-extrabold text-white drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-snug">
              당신의 든든한
            </p>
            <p className="text-7xl font-extrabold text-white drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-snug">
              AI 비즈니스 팀
            </p>
          </div>


          {/* 중앙 고양이 일러스트 */}
          <div className="absolute inset-0 flex justify-center items-center pointer-events-none">
            <img
              src="/images/cat_group.png"
              alt="고양이 일러스트"
              className="w-[900px] h-auto drop-shadow-2xl"
            />
          </div>
        </div>
      </div>

      {/* 좌측 하단 내비게이션 */}
      <div className="absolute bottom-[10%] left-[5%] text-3xl text-black font-medium space-y-4">
        <Link to="#" className="block hover:underline">서비스 소개</Link>
        <Link to="#" className="block hover:underline">상담하기</Link>
        <Link to="#" className="block font-bold underline">FAQ</Link>
      </div>


      {/* 우측 하단 로고 */}
      <div className="absolute bottom-[3%] right-[2%] text-8xl font-extrabold text-white">
        TinkerBell
      </div>
    </div>
  );
}

export default Main;
