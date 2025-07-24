// import type { AutomationTask, ScheduleEvent, ContentTemplate } from "../types"

// export const initialAutomationTasks: AutomationTask[] = [
//   {
//     id: 1,
//     task_type: "instagram",
//     title: "인스타그램 신상품 포스팅",
//     status: "발행 완료",
//     created_at: "2025-07-18",
//     scheduled_at: "2025-07-20",
//     task_data: JSON.stringify({
//       content: "🌟 신상품 출시! 🌟\n\n새로운 여름 컬렉션이 드디어 출시되었습니다!\n\n#신상품 #여름컬렉션 #패션",
//       hashtags: ["신상품", "여름컬렉션", "패션"],
//       image_url: "/placeholder.svg",
//     }),
//   },
//   {
//     id: 2,
//     task_type: "email",
//     title: "주간 뉴스레터 발송",
//     status: "발행 완료",
//     created_at: "2025-07-19",
//     scheduled_at: "2025-07-22",
//     task_data: JSON.stringify({
//       subject: "이번 주 특가 상품 안내",
//       content: "안녕하세요! 이번 주 특가 상품을 안내드립니다.",
//       recipients: "all_customers",
//     }),
//   },
//   {
//     id: 5,
//     task_type: "instagram",
//     title: "고객 후기 공유",
//     status: "발행 완료",
//     created_at: "2025-07-20",
//     scheduled_at: "2025-07-23",
//     task_data: JSON.stringify({
//       content: "💝 고객님들의 따뜻한 후기 💝\n\n'정말 만족스러운 쇼핑이었어요!'\n\n감사합니다 ❤️\n\n#고객후기 #감사인사",
//       hashtags: ["고객후기", "감사인사"],
//       image_url: "/placeholder.svg",
//     }),
//   },
//   {
//     id: 6,
//     task_type: "email",
//     title: "신규 회원 환영 메일",
//     status: "발행 완료",
//     created_at: "2025-07-23",
//     scheduled_at: "2025-07-24",
//     task_data: JSON.stringify({
//       subject: "TinkerBell에 오신 것을 환영합니다!",
//       content: "회원가입을 축하드립니다! 첫 구매 시 10% 할인 쿠폰을 드려요.",
//       recipients: "new_members",
//     }),
//   },
//   {
//     id: 3,
//     task_type: "instagram",
//     title: "할인 이벤트 홍보",
//     status: "발행 전",
//     created_at: "2025-07-21",
//     scheduled_at: "2025-07-25",
//     task_data: JSON.stringify({
//       content: "🔥 특별 할인 이벤트 🔥\n\n오직 이번 주만! 30% 할인\n\n기간: 7/25 ~ 7/31\n\n#할인 #이벤트 #특가",
//       hashtags: ["할인", "이벤트", "특가"],
//       image_url: "/placeholder.svg",
//     }),
//   },
//   {
//     id: 4,
//     task_type: "email",
//     title: "고객 만족도 조사",
//     status: "발행 전",
//     created_at: "2025-07-22",
//     scheduled_at: "2025-07-26",
//     task_data: JSON.stringify({
//       subject: "고객님의 소중한 의견을 들려주세요",
//       content: "안녕하세요! 더 나은 서비스 제공을 위해 고객 만족도 조사를 진행합니다.",
//       recipients: "recent_customers",
//     }),
//   },
//   {
//     id: 7,
//     task_type: "instagram",
//     title: "브랜드 스토리 소개",
//     status: "발행 전",
//     created_at: "2025-07-24",
//     scheduled_at: "2025-07-28",
//     task_data: JSON.stringify({
//       content:
//         "✨ TinkerBell의 이야기 ✨\n\n우리는 모든 여성이 아름다워질 권리가 있다고 믿습니다.\n\n#브랜드스토리 #TinkerBell",
//       hashtags: ["브랜드스토리", "TinkerBell"],
//       image_url: "/placeholder.svg",
//     }),
//   },
//   {
//     id: 8,
//     task_type: "email",
//     title: "재입고 알림",
//     status: "발행 전",
//     created_at: "2025-07-25",
//     scheduled_at: "2025-07-27",
//     task_data: JSON.stringify({
//       subject: "인기 상품이 재입고되었습니다!",
//       content: "품절되었던 인기 상품들이 다시 입고되었습니다. 서둘러 주문하세요!",
//       recipients: "waitlist_customers",
//     }),
//   },
// ]

// export const initialScheduleEvents: ScheduleEvent[] = [
//   {
//     id: 1,
//     title: "가을신상 촬영하기",
//     date: "2025-07-20",
//     time: "14:00",
//     type: "manual",
//     description: "가을 신상품 촬영 일정",
//   },
//   {
//     id: 2,
//     title: "재고 점검하기",
//     date: "2025-07-22",
//     time: "10:30",
//     type: "manual",
//     description: "월말 재고 점검 및 정리",
//   },
//   {
//     id: 3,
//     title: "마케팅 미팅",
//     date: "2025-07-25",
//     time: "15:00",
//     type: "manual",
//     description: "SNS 마케팅 전략 회의",
//   },
//   {
//     id: 4,
//     title: "고객 상담",
//     date: "2025-07-26",
//     time: "16:00",
//     type: "manual",
//     description: "VIP 고객 개별 상담",
//   },
//   {
//     id: 5,
//     title: "상품 기획 회의",
//     date: "2025-07-23",
//     time: "11:00",
//     type: "manual",
//     description: "신상품 기획 및 디자인 논의",
//   },
// ]

// export const contentTemplates: ContentTemplate[] = [
//   {
//     id: 1,
//     type: "sns",
//     title: "인스타그램 상품 소개 템플릿",
//     content:
//       "🌟 신상품 출시! 🌟\n\n{상품명}이 드디어 출시되었습니다!\n\n✨ 특징:\n- {특징1}\n- {특징2}\n- {특징3}\n\n💰 가격: {가격}\n🚚 무료배송\n\n#신상품 #온라인쇼핑 #{카테고리}",
//     tags: ["상품소개", "신상품", "마케팅"],
//   },
//   {
//     id: 2,
//     type: "email",
//     title: "고객 감사 이메일 템플릿",
//     content:
//       "안녕하세요, {고객명}님!\n\n저희 쇼핑몰을 이용해주셔서 진심으로 감사드립니다.\n\n이번 주 특별 할인 혜택을 준비했습니다:\n- 전 상품 20% 할인\n- 무료배송 (5만원 이상)\n- 적립금 2배 적립\n\n감사합니다.",
//     tags: ["고객관리", "할인", "감사인사"],
//   },
//   {
//     id: 3,
//     type: "sns",
//     title: "블로그 상품 리뷰 템플릿",
//     content:
//       "# {상품명} 솔직 후기\n\n안녕하세요! 오늘은 {상품명}에 대한 솔직한 후기를 공유하려고 합니다.\n\n## 장점\n- {장점1}\n- {장점2}\n\n## 단점\n- {단점1}\n\n## 총평\n{총평 내용}\n\n⭐⭐⭐⭐⭐ (5/5점)",
//     tags: ["상품리뷰", "후기", "블로그"],
//   },
//   {
//     id: 4,
//     type: "email",
//     title: "신상품 안내 이메일 템플릿",
//     content:
//       "안녕하세요, {고객명}님!\n\n저희 쇼핑몰에 새로운 상품이 입고되었습니다.\n\n{상품명} - {가격}원\n\n지금 바로 확인해보세요!\n\n감사합니다.",
//     tags: ["신상품", "안내", "이메일마케팅"],
//   },
//   {
//     id: 5,
//     type: "sns",
//     title: "인스타그램 할인 이벤트 템플릿",
//     content:
//       "🔥 특별 할인 이벤트 🔥\n\n오직 이번 주만! {할인율}% 할인\n\n기간: {시작일} ~ {종료일}\n\n놓치지 마세요! 👉 프로필 링크\n\n#할인 #이벤트 #특가",
//     tags: ["할인", "이벤트", "프로모션"],
//   },
//   {
//     id: 6,
//     type: "email",
//     title: "고객 문의 응답 템플릿",
//     content:
//       "안녕하세요! 문의해주셔서 감사합니다.\n\n{고객명}님의 문의사항에 대해 답변드리겠습니다.\n\n{답변내용}\n\n추가 궁금한 사항이 있으시면 언제든 연락주세요.\n\n감사합니다.",
//     tags: ["고객응답", "문의", "상담"],
//   },
//   {
//     id: 7,
//     type: "email",
//     title: "배송 안내 이메일 템플릿",
//     content:
//       "[TinkerBell] 배송 안내\n\n{고객명}님, 주문하신 상품이 발송되었습니다.\n\n운송장번호: {운송장번호}\n택배사: {택배사}\n\n배송조회: {조회링크}\n\n감사합니다.",
//     tags: ["배송안내", "주문", "알림"],
//   },
//   {
//     id: 8,
//     type: "sns",
//     title: "이벤트 참여 감사 포스트",
//     content:
//       "🎉 이벤트 참여 감사합니다!\n\n{고객명}님의 참여가 확인되었습니다.\n\n당첨자 발표: {발표일}\n경품: {경품내용}\n\n많은 관심 감사드립니다!",
//     tags: ["이벤트", "참여", "감사"],
//   },
// ]
