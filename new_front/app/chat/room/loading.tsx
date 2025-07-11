export default function Loading() {
  return (
    <div className="min-h-screen bg-green-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">채팅룸 로딩 중...</p>
      </div>
    </div>
  )
}
