"use client"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Star, X } from "lucide-react"

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
  onSubmit,
}: FeedbackModalProps) {
  const categories = ["general", "planning", "marketing", "customer", "task", "mental"]

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] p-6">
        <DialogHeader>
          <DialogTitle className="flex justify-between items-center">
            피드백 남기기
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
          <DialogDescription>에이전트와의 대화에 대한 피드백을 남겨주세요.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="rating" className="text-left">
              별점
            </Label>
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`cursor-pointer ${star <= rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}`}
                  onClick={() => setRating(star)}
                />
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="comment" className="text-left">
              의견
            </Label>
            <Textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="자유롭게 의견을 남겨주세요."
              rows={4}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="category" className="text-left">
              카테고리
            </Label>
            <select
              id="category"
              className="w-full border border-gray-300 rounded-md p-2 text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === "general" && "일반"}
                  {cat === "planning" && "사업기획"}
                  {cat === "marketing" && "마케팅"}
                  {cat === "customer" && "고객관리"}
                  {cat === "task" && "업무지원"}
                  {cat === "mental" && "멘탈코칭"}
                </option>
              ))}
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            취소
          </Button>
          <Button onClick={onSubmit} disabled={rating === 0}>
            피드백 제출
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
