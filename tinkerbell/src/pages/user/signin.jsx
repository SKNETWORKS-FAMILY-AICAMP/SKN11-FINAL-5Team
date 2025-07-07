"use client";

export default function SignIn() {
  const handleSocialLogin = async (provider) => {
    const access_token = "임시토큰";

    const res = await fetch("/auth/social-login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ provider, access_token }),
    });

    const result = await res.json();
    if (result.success) {
      alert("로그인 성공!");
    } else {
      alert("로그인 실패");
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFAD1] flex flex-col items-center">
      {/* 상단 고양이 일러스트 - 파란색 영역 확대 */}
      <div className="w-full relative bg-[#044BD9] h-80 flex justify-center items-end">
        <img
          src="/images/cat.png"
          alt="cat"
          className="w-[500px] absolute bottom-[-150px]"
        />
      </div>

      {/* 로그인 영역 - 노란색 영역 안에서 가운데 정렬 */}
      <div className="mt-32 w-full max-w-md px-6 flex flex-col items-center">
        <h1 className="text-2xl font-semibold text-center mb-8">
          Sign in to TinkerBell
        </h1>

        <div className="w-full space-y-6">
          {/* Kakao 로그인 */}
          <button
            onClick={() => handleSocialLogin("kakao")}
            className="flex items-center gap-4 w-full h-16 bg-white border border-gray-300 rounded-full px-8 hover:bg-gray-100 shadow-sm"
          >
            <img src="/images/kakao_icon.png" alt="kakao" className="w-8 h-8" />
            <span className="text-lg font-medium">Kakao 로 계속하기</span>
          </button>

          {/* Naver 로그인 */}
          <button
            onClick={() => handleSocialLogin("naver")}
            className="flex items-center gap-4 w-full h-16 bg-white border border-gray-300 rounded-full px-8 hover:bg-gray-100 shadow-sm"
          >
            <img src="/images/naver_icon.png" alt="naver" className="w-8 h-8" />
            <span className="text-lg font-medium">Naver 로 계속하기</span>
          </button>

          {/* Google 로그인 */}
          <button
            onClick={() => handleSocialLogin("google")}
            className="flex items-center gap-4 w-full h-16 bg-white border border-gray-300 rounded-full px-8 hover:bg-gray-100 shadow-sm"
          >
            <img src="/images/google_icon.png" alt="google" className="w-8 h-8" />
            <span className="text-lg font-medium">Google 로 계속하기</span>
          </button>
        </div>
      </div>
    </div>
  );
}