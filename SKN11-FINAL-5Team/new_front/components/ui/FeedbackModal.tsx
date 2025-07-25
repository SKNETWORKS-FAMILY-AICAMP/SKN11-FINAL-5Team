import React from 'react'
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { X, Star } from "lucide-react"

interface FeedbackModalProps {
  rating: number
  setRating: (rating: number) => void
  comment: string
  setComment: (comment: string) => void
  category: string
  setCategory: (category: string) => void
  onClose: () => void
  onSubmit: () => void
}

export function FeedbackModal({
  rating,
  setRating,
  comment,
  setComment,
  category,
  setCategory,
  onClose,
  onSubmit
}: FeedbackModalProps) {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg relative">
        {/* 헤더 - X 버튼 하나만 */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">피드백 남기기</h3>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onClose}
            className="h-6 w-6 p-0 hover:bg-gray-100 rounded-full"
          >
            <X className="h-4 w-4 text-gray-500" />
          </Button>
        </div>

        <p className="text-sm text-gray-600 mb-6">
          에이전트의 대화에 대한 피드백을 남겨주세요.
        </p>

        {/* 별점 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            별점
          </label>
          <div className="flex space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                className="p-1 hover:scale-110 transition-transform"
              >
                <Star
                  className={`w-6 h-6 ${
                    star <= rating 
                      ? 'fill-yellow-400 text-yellow-400' 
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* 의견 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            의견
          </label>
          <Textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="구체적인 피드백을 남겨주세요..."
            rows={4}
            className="w-full resize-none border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>

        {/* 카테고리 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            카테고리
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
          >
            <option value="general">일반</option>
            <option value="planner">사업기획</option>
            <option value="marketing">마케팅</option>
            <option value="crm">고객관리</option>
            <option value="task">업무지원</option>
            <option value="mentalcare">멘탈케어</option>
          </select>
        </div>

        {/* 버튼들 */}
        <div className="flex justify-end space-x-3">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100"
          >
            취소
          </Button>
          <Button
            type="button"
            onClick={onSubmit}
            className="px-4 py-2 bg-gray-900 text-white hover:bg-gray-800 rounded-md"
          >
            피드백 제출
          </Button>
        </div>
      </div>
    </div>
  )
}