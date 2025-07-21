// src/workspace/components/TemplatePreview.tsx
"use client"
import Image from "next/image"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Heart, MessageCircle, Send, Bookmark, MessageSquare } from "lucide-react"

interface Props {
  type: "sns" | "email" | "message"
  title?: string
  content: string
}

export default function TemplatePreview({ type, title, content }: Props) {
  if (!type || !content) {
    return <div className="text-sm text-gray-500 text-center py-8">미리보기할 콘텐츠가 없습니다</div>
  }

  switch (type) {
    case "sns":
      return (
        <div className="max-w-sm mx-auto bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between p-3 border-b">
            <div className="flex items-center space-x-3">
              <Avatar className="w-8 h-8">
                <AvatarImage src="/placeholder.svg" />
                <AvatarFallback>TB</AvatarFallback>
              </Avatar>
              <div>
                <p className="font-semibold text-sm">tinkerbell_shop</p>
                <p className="text-xs text-gray-500">Seoul, South Korea</p>
              </div>
            </div>
          </div>

          <div className="aspect-square bg-gray-100 flex items-center justify-center">
            <Image src="/placeholder.svg" alt="Post" width={300} height={300} className="object-cover" />
          </div>

          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-4">
                <Heart className="w-5 h-5" />
                <MessageCircle className="w-5 h-5" />
                <Send className="w-5 h-5" />
              </div>
              <Bookmark className="w-5 h-5" />
            </div>
            <p className="font-semibold text-sm mb-1">1,234개의 좋아요</p>
            <div className="text-sm whitespace-pre-wrap">
              <span className="font-semibold">tinkerbell_shop</span> {content}
            </div>
            <p className="text-xs text-gray-500 mt-2">1시간 전</p>
          </div>
        </div>
      )

    case "email":
      return (
        <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50 p-4 border-b text-sm text-gray-700 space-y-1">
            <div>
              <strong>From:</strong> TinkerBell &lt;noreply@tinkerbell.com&gt;
            </div>
            <div>
              <strong>To:</strong> 고객님 &lt;customer@example.com&gt;
            </div>
            <div>
              <strong>Subject:</strong> {title || "제목 없음"}
            </div>
          </div>
          <div className="p-4">
            <Image
              src="/placeholder.svg"
              alt="logo"
              width={120}
              height={40}
              className="mb-4"
            />
            <div className="whitespace-pre-wrap text-sm text-gray-800">{content}</div>
            <div className="mt-6 pt-4 border-t text-xs text-gray-500 space-y-1">
              <p>TinkerBell Shop</p>
              <p>서울시 강남구 테헤란로 123</p>
              <p>고객센터: 1588-1234</p>
            </div>
          </div>
        </div>
      )

    case "message":
      return (
        <div className="max-w-xs mx-auto bg-white border rounded-xl overflow-hidden shadow-sm">
          <div className="bg-green-500 text-white p-3 flex items-center space-x-2">
            <MessageSquare className="w-4 h-4" />
            <span className="font-semibold text-sm">TinkerBell Shop</span>
          </div>
          <div className="p-3">
            <div className="bg-gray-100 rounded-lg p-3 mb-2 text-sm text-gray-800 whitespace-pre-wrap">
              {content}
            </div>
            <div className="text-xs text-gray-500 text-right">
              {new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        </div>
      )

    default:
      return <div className="text-sm text-center text-gray-500 py-8">지원하지 않는 템플릿입니다</div>
  }
}
