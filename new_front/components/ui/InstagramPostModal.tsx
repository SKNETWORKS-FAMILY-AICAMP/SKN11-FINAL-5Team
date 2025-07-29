"use client"

import { useState, useRef, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { 
  Instagram, 
  Image as ImageIcon, 
  X, 
  Send, 
  Copy,
  Eye,
  Hash,
  Calendar,
  Clock,
  User
} from "lucide-react"
import { toast } from "@/hooks/use-toast"

interface InstagramPostModalProps {
  isOpen: boolean
  onClose: () => void
  generatedContent: string
  onPost: (content: string, images: File[]) => Promise<void>
  onSchedule?: (content: string, images: File[], scheduledTime: Date) => Promise<void>
}

export function InstagramPostModal({ 
  isOpen, 
  onClose, 
  generatedContent, 
  onPost,
  onSchedule 
}: InstagramPostModalProps) {
  const [content, setContent] = useState('')
  const [images, setImages] = useState<File[]>([])
  const [imagePreviewUrls, setImagePreviewUrls] = useState<string[]>([])
  const [isPosting, setIsPosting] = useState(false)
  const [isScheduling, setIsScheduling] = useState(false)
  const [showScheduleOptions, setShowScheduleOptions] = useState(false)
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // generatedContent가 변경될 때마다 content 업데이트
  useEffect(() => {
    if (generatedContent) {
      console.log('[DEBUG] Modal에서 생성된 콘텐츠 받음:', generatedContent)
      setContent(generatedContent)
    }
  }, [generatedContent])

  // 해시태그 추출
  const hashtags = content.match(/#\w+/g) || []
  const contentWithoutHashtags = content.replace(/#\w+/g, '').trim()
  
  // 글자 수 계산 (Instagram 제한: 2200자)
  const characterCount = content.length
  const isOverLimit = characterCount > 2200

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    if (files.length + images.length > 10) {
      toast({
        title: "이미지 제한",
        description: "최대 10개의 이미지만 업로드할 수 있습니다.",
        variant: "destructive"
      })
      return
    }

    const newImages = [...images, ...files]
    setImages(newImages)

    // 미리보기 URL 생성
    const newPreviewUrls = files.map(file => URL.createObjectURL(file))
    setImagePreviewUrls(prev => [...prev, ...newPreviewUrls])
  }

  const removeImage = (index: number) => {
    const newImages = images.filter((_, i) => i !== index)
    const newPreviewUrls = imagePreviewUrls.filter((_, i) => i !== index)
    
    // 메모리 정리
    URL.revokeObjectURL(imagePreviewUrls[index])
    
    setImages(newImages)
    setImagePreviewUrls(newPreviewUrls)
  }

  const handlePost = async () => {
    if (isOverLimit) {
      toast({
        title: "글자 수 초과",
        description: "Instagram 게시글은 2200자를 초과할 수 없습니다.",
        variant: "destructive"
      })
      return
    }

    setIsPosting(true)
    try {
      let imageUrl = '';
      if (images.length > 0) {
        // S3에 이미지 업로드
        const formData = new FormData();
        formData.append('file', images[0]); // instagram.py에서는 'file' 키를 사용함

        const uploadRes = await fetch('https://localhost:8005/s3/upload', {
          method: 'POST',
          body: formData,
        });

        if (!uploadRes.ok) {
          let uploadError: any = {};
          try {
            uploadError = await uploadRes.json();
          } catch {
            uploadError = { error: "S3 업로드 중 서버 에러" };
          }
          throw new Error(uploadError?.error || '이미지 업로드 실패');
        }

        const uploadData = await uploadRes.json();
        imageUrl = uploadData.file_url;
      }
      
      const userId = localStorage.getItem('user_id'); 

      // Instagram 포스팅 API 호출
      const response = await fetch('https://localhost:8005/instagram/post', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({
          user_id: userId, // 반드시 user_id를 포함해야 함
          caption: content,
          image_url: imageUrl,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '포스팅 실패');
      }

      toast({
        title: '포스팅 완료',
        description: 'Instagram에 성공적으로 게시되었습니다.',
      });
      onClose();
    } catch (error) {
      console.error('Instagram 포스팅 오류:', error);
      toast({
        title: '포스팅 실패',
        description:
          error instanceof Error
            ? error.message
            : '게시 중 오류가 발생했습니다. 다시 시도해주세요.',
        variant: 'destructive',
      });
    } finally {
      setIsPosting(false);
    }

  }

  const handleSchedule = async () => {
    if (!scheduledDate || !scheduledTime) {
      toast({
        title: "예약 정보 필요",
        description: "예약 날짜와 시간을 선택해주세요.",
        variant: "destructive"
      })
      return
    }

    const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`)
    if (scheduledDateTime <= new Date()) {
      toast({
        title: "잘못된 예약 시간",
        description: "미래 시간으로 예약해주세요.",
        variant: "destructive"
      })
      return
    }

    setIsScheduling(true)
    try {
      await onSchedule?.(content, images, scheduledDateTime)
      toast({
        title: "예약 완료",
        description: `${scheduledDateTime.toLocaleString()}에 게시 예약되었습니다.`,
      })
      onClose()
    } catch (error) {
      toast({
        title: "예약 실패",
        description: "예약 중 오류가 발생했습니다. 다시 시도해주세요.",
        variant: "destructive"
      })
    } finally {
      setIsScheduling(false)
    }
  }

  const copyContent = () => {
    navigator.clipboard.writeText(content)
    toast({
      title: "복사 완료",
      description: "콘텐츠가 클립보드에 복사되었습니다.",
    })
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Instagram className="h-5 w-5 text-pink-500" />
            Instagram 포스팅
          </DialogTitle>
          <DialogDescription>
            생성된 콘텐츠를 확인하고 Instagram에 게시하거나 예약하세요.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 왼쪽: 콘텐츠 편집 */}
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="content">게시글 내용</Label>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyContent}
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    복사
                  </Button>
                  <span className={`text-sm ${
                    isOverLimit ? 'text-red-500' : 
                    characterCount > 1800 ? 'text-yellow-500' : 'text-gray-500'
                  }`}>
                    {characterCount}/2200
                  </span>
                </div>
              </div>
              <Textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Instagram 게시글 내용을 입력하세요..."
                className="min-h-[200px] resize-none"
              />
            </div>

            {/* 해시태그 표시 */}
            {hashtags.length > 0 && (
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Hash className="h-4 w-4" />
                  해시태그 ({hashtags.length}개)
                </Label>
                <div className="flex flex-wrap gap-1">
                  {hashtags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-blue-600">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* 이미지 업로드 */}
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                <ImageIcon className="h-4 w-4" />
                이미지 ({images.length}/10)
              </Label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full"
                  disabled={images.length >= 10}
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  이미지 추가
                </Button>
              </div>

              {/* 이미지 미리보기 */}
              {imagePreviewUrls.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {imagePreviewUrls.map((url, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={url}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-20 object-cover rounded-lg"
                      />
                      <Button
                        variant="destructive"
                        size="sm"
                        className="absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => removeImage(index)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 오른쪽: 미리보기 및 액션 */}
          <div className="space-y-4">
            {/* Instagram 스타일 미리보기 */}
            <Card>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
                      <Instagram className="h-4 w-4 text-white" />
                    </div>
                    <span className="font-semibold text-sm">your_account</span>
                  </div>
                  
                  {/* 이미지 미리보기 (첫 번째 이미지만) */}
                  {imagePreviewUrls.length > 0 && (
                    <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                      <img
                        src={imagePreviewUrls[0]}
                        alt="Post preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <p className="text-sm whitespace-pre-wrap">
                      {contentWithoutHashtags}
                    </p>
                    {hashtags.length > 0 && (
                      <p className="text-sm text-blue-600">
                        {hashtags.join(' ')}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Separator />

            {/* 예약 옵션 */}
            {!showScheduleOptions ? (
              <Button
                variant="outline"
                onClick={() => setShowScheduleOptions(true)}
                className="w-full"
              >
                <Calendar className="h-4 w-4 mr-2" />
                예약 게시
              </Button>
            ) : (
              <div className="space-y-3 p-3 border rounded-lg">
                <Label className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  예약 설정
                </Label>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="date" className="text-xs">날짜</Label>
                    <Input
                      id="date"
                      type="date"
                      value={scheduledDate}
                      onChange={(e) => setScheduledDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  <div>
                    <Label htmlFor="time" className="text-xs">시간</Label>
                    <Input
                      id="time"
                      type="time"
                      value={scheduledTime}
                      onChange={(e) => setScheduledTime(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowScheduleOptions(false)}
                    className="flex-1"
                  >
                    취소
                  </Button>
                  <Button
                    onClick={handleSchedule}
                    disabled={isScheduling || !scheduledDate || !scheduledTime}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    {isScheduling ? '예약 중...' : '예약하기'}
                  </Button>
                </div>
              </div>
            )}

            {/* 액션 버튼들 */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                취소
              </Button>
              <Button
                onClick={handlePost}
                disabled={isPosting || isOverLimit}
                className="flex-1 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600"
              >
                {isPosting ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    게시 중...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Send className="h-4 w-4" />
                    지금 게시
                  </div>
                )}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}