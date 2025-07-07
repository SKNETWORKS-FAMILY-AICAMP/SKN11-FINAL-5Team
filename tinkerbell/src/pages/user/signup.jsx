import { useState } from "react";

// Input 컴포넌트
const Input = ({ className, ...props }) => (
  <input
    className={`w-full border border-gray-300 rounded-full px-6 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
    {...props}
  />
);

// Button 컴포넌트
const Button = ({ className, children, ...props }) => (
  <button
    className={`rounded-full font-semibold transition-colors ${className}`}
    {...props}
  >
    {children}
  </button>
);

// Select 컴포넌트
const Select = ({ value, onValueChange, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="h-14 w-full rounded-full px-6 bg-white text-base border border-gray-300 text-left focus:outline-none focus:ring-2 focus:ring-blue-500 flex justify-between items-center"
      >
        <span className={value ? "text-black" : "text-gray-500"}>
          {value
            ? children.find((child) => child.props.value === value)?.props.children
            : "선택하세요"}
        </span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg">
          {children.map((child, index) => (
            <button
              key={index}
              type="button"
              onClick={() => {
                onValueChange(child.props.value);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 first:rounded-t-lg last:rounded-b-lg"
            >
              {child.props.children}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const SelectItem = ({ value, children }) => null;

// 고양이 이미지 컴포넌트
const CatImage = () => {
  return (
    <img
      src="/images/cat_face.png"
      alt="TinkerBell 고양이"
      className="absolute w-[1000px] top-[-15%] left-[0%] h-auto drop-shadow-xl"
      onError={(e) => {
        console.log("이미지 로드 실패, 대체 이미지 표시");
        e.target.style.display = 'none';
        e.target.nextSibling.style.display = 'flex';
      }}
    />
  );
};

function SignUp() {
  const [name, setName] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [entrepreneurExperience, setEntrepreneurExperience] = useState("");
  const [showSocialLogin, setShowSocialLogin] = useState(false);

  const handleSignup = () => {
    if (!name || !businessType || !entrepreneurExperience) {
      alert("모든 항목을 입력해주세요.");
      return;
    }
    setShowSocialLogin(true);
  };

  const KakaoIcon = () => (
    <img src="/images/kakao_icon.png" alt="kakao" className="w-6 h-6" />
  );

  const NaverIcon = () => (
    <img src="/images/naver_icon.png" alt="naver" className="w-6 h-6" />
  );

  const GoogleIcon = () => (
    <img src="/images/google_icon.png" alt="google" className="w-6 h-6" />
  );


  const SocialLoginButton = ({ icon, text, onClick }) => (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-6 py-3 bg-white border rounded-full hover:bg-gray-100 transition-colors"
    >
      {icon}
      <span className="text-sm font-semibold">{text}</span>
    </button>
  );

  if (showSocialLogin) {
    return (
      <div className="min-h-screen flex">
        <div className="w-[50%] bg-[#044BD9] relative flex items-end justify-start p-6">
          <CatImage />
        </div>
        <div className="w-[50%] bg-[#FFF8D2] flex flex-col justify-center items-center px-8">
          <div className="w-full max-w-md space-y-8">
            <h1 className="text-3xl font-semibold text-center mb-16">
              Sign up to TinkerBell
            </h1>
            <div className="space-y-6">
              <SocialLoginButton
                icon={<KakaoIcon />}
                text="Kakao로 계속하기"
                onClick={() => console.log("카카오 로그인:", { name, businessType, entrepreneurExperience })}
              />
              <SocialLoginButton
                icon={<NaverIcon />}
                text="Naver로 계속하기"
                onClick={() => console.log("네이버 로그인:", { name, businessType, entrepreneurExperience })}
              />
              <SocialLoginButton
                icon={<GoogleIcon />}
                text="Google로 계속하기"
                onClick={() => console.log("구글 로그인:", { name, businessType, entrepreneurExperience })}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <div className="w-[50%] bg-[#044BD9] relative flex items-end justify-start p-6">
        <CatImage />
      </div>

      <div className="w-[50%] bg-[#FFF8D2] flex justify-center items-center">
        <div className="w-full max-w-xl px-8 space-y-12">
          <h1 className="text-2xl font-semibold text-center">Sign up to TinkerBell</h1>

          <div className="space-y-8">
            <div>
              <label className="text-sm">당신의 이름을 입력하세요.</label>
              <Input type="text" value={name} onChange={(e) => setName(e.target.value)} />
            </div>

            <div>
              <label className="text-sm">당신의 비즈니스 타입을 선택하세요.</label>
              <Select value={businessType} onValueChange={setBusinessType}>
                <SelectItem value="CREATOR">크리에이터</SelectItem>
                <SelectItem value="DEVELOPER">개발자</SelectItem>
                <SelectItem value="E-COMMERCE">이커머스 셀러</SelectItem>
                <SelectItem value="BEAUTY">1인 뷰티샵</SelectItem>
                <SelectItem value="OTHER">기타</SelectItem>
              </Select>
            </div>

            <div>
              <label className="text-sm">당신의 창업 경험 여부를 알려주세요.</label>
              <Select value={entrepreneurExperience} onValueChange={setEntrepreneurExperience}>
                <SelectItem value="experienced">창업 경험 있음</SelectItem>
                <SelectItem value="beginner">창업 경험 없음</SelectItem>
              </Select>
            </div>
          </div>

          <div className="flex justify-center">
            <Button
              onClick={handleSignup}
              className="h-14 w-48 bg-[#044BD9] hover:bg-[#033caa] text-white text-lg"
            >
              NEXT
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignUp;