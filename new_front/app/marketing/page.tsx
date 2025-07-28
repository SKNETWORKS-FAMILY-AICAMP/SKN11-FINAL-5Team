"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Progress } from "@/components/ui/progress"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { 
  Search, 
  TrendingUp, 
  FileText, 
  Calendar as CalendarIcon,
  Clock, 
  BarChart3, 
  Target, 
  Zap,
  Settings,
  Plus,
  Edit3,
  Send,
  Eye,
  Users,
  ArrowUp,
  ArrowDown,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Copy
} from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

// 타입 정의
interface KeywordData {
  keyword: string
  searchVolume: number
  competition: string
  difficulty: number
  trend: number
  relatedKeywords: string[]
}

interface ContentData {
  id: string
  keyword: string
  title: string
  content: string
  status: 'draft' | 'scheduled' | 'published'
  scheduledDate?: Date
  platform: string
  wordCount: number
  seoScore: number
}

interface ScheduleData {
  id: string
  contentId: string
  platform: string
  publishDate: Date
  status: 'pending' | 'published' | 'failed'
}

export default function MarketingAutomationPage() {
  // 상태 관리
  const [selectedTab, setSelectedTab] = useState("keywords")
  const [keywordInput, setKeywordInput] = useState("")
  const [keywords, setKeywords] = useState<KeywordData[]>([])
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([])
  const [contents, setContents] = useState<ContentData[]>([])
  const [schedules, setSchedules] = useState<ScheduleData[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date>()
  const [selectedTime, setSelectedTime] = useState("09:00")
  const [autoSchedule, setAutoSchedule] = useState(false)

  // 키워드 분석 함수
  const analyzeKeywords = async () => {
    if (!keywordInput.trim()) return
    
    setIsAnalyzing(true)
    
    // API 호출 시뮬레이션 (실제로는 keyword_api.py의 /keywords/recommend 엔드포인트 호출)
    try {
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const mockKeywords: KeywordData[] = [
        {
          keyword: keywordInput,
          searchVolume: 12500,
          competition: "medium",
          difficulty: 65,
          trend: 15,
          relatedKeywords: ["관련키워드1", "관련키워드2", "관련키워드3"]
        },
        {
          keyword: keywordInput + " 추천",
          searchVolume: 8200,
          competition: "low",
          difficulty: 45,
          trend: 8,
          relatedKeywords: ["추천키워드1", "추천키워드2"]
        },
        {
          keyword: keywordInput + " 후기",
          searchVolume: 15600,
          competition: "high",
          difficulty: 78,
          trend: -3,
          relatedKeywords: ["후기키워드1", "후기키워드2", "후기키워드3"]
        }
      ]
      
      setKeywords(mockKeywords)
    } catch (error) {
      console.error('키워드 분석 실패:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 콘텐츠 생성 함수
  const generateContent = async () => {
    if (selectedKeywords.length === 0) return
    
    setIsGenerating(true)
    
    // API 호출 시뮬레이션 (실제로는 blog_content_api.py의 /blog/content/generate 엔드포인트 호출)
    try {
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      const newContents: ContentData[] = selectedKeywords.map((keyword, index) => ({
        id: `content_${Date.now()}_${index}`,
        keyword,
        title: `${keyword}에 대한 완벽한 가이드`,
        content: `${keyword}에 대한 자세한 내용을 담은 블로그 포스트입니다. 이 포스트는 AI가 생성한 고품질 콘텐츠로, SEO 최적화가 되어 있습니다...`,
        status: 'draft',
        platform: 'naver_blog',
        wordCount: 1200 + Math.floor(Math.random() * 800),
        seoScore: 75 + Math.floor(Math.random() * 25)
      }))
      
      setContents(prev => [...prev, ...newContents])
      setSelectedKeywords([])
    } catch (error) {
      console.error('콘텐츠 생성 실패:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  // 발행 예약 함수
  const scheduleContent = async (contentId: string, publishDate: Date) => {
    try {
      const newSchedule: ScheduleData = {
        id: `schedule_${Date.now()}`,
        contentId,
        platform: 'naver_blog',
        publishDate,
        status: 'pending'
      }
      
      setSchedules(prev => [...prev, newSchedule])
      setContents(prev => prev.map(content => 
        content.id === contentId 
          ? { ...content, status: 'scheduled', scheduledDate: publishDate }
          : content
      ))
    } catch (error) {
      console.error('발행 예약 실패:', error)
    }
  }

  // 통계 데이터
  const stats = {
    totalKeywords: keywords.length,
    totalContents: contents.length,
    scheduledContents: contents.filter(c => c.status === 'scheduled').length,
    publishedContents: contents.filter(c => c.status === 'published').length,
    averageSeoScore: contents.length > 0 ? Math.round(contents.reduce((sum, c) => sum + c.seoScore, 0) / contents.length) : 0
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-yellow-50 to-emerald-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">마케팅 업무 자동화</h1>
              <p className="text-gray-600">키워드 분석부터 콘텐츠 발행까지 한 번에 관리하세요</p>
            </div>
          </div>
          
          {/* 통계 대시보드 */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <Card className="border-0 shadow-md bg-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-gray-600">키워드</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.totalKeywords}</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md bg-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span className="text-sm text-gray-600">콘텐츠</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.totalContents}</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md bg-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm text-gray-600">예약됨</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.scheduledContents}</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md bg-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span className="text-sm text-gray-600">발행됨</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.publishedContents}</p>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-md bg-white">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-600" />
                  <span className="text-sm text-gray-600">평균 SEO</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.averageSeoScore}</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 메인 탭 */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white shadow-sm">
            <TabsTrigger value="keywords" className="data-[state=active]:bg-green-100 data-[state=active]:text-green-700">
              <Search className="h-4 w-4 mr-2" />
              키워드 분석
            </TabsTrigger>
            <TabsTrigger value="content" className="data-[state=active]:bg-yellow-100 data-[state=active]:text-yellow-700">
              <FileText className="h-4 w-4 mr-2" />
              콘텐츠 생성
            </TabsTrigger>
            <TabsTrigger value="schedule" className="data-[state=active]:bg-emerald-100 data-[state=active]:text-emerald-700">
              <CalendarIcon className="h-4 w-4 mr-2" />
              발행 스케줄
            </TabsTrigger>
          </TabsList>

          {/* 키워드 분석 탭 */}
          <TabsContent value="keywords" className="space-y-6">
            <Card className="border-0 shadow-lg bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  키워드 추천 및 분석
                </CardTitle>
                <CardDescription>
                  타겟 키워드를 입력하면 관련 키워드와 트렌드 분석을 제공합니다
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="분석할 키워드를 입력하세요"
                    value={keywordInput}
                    onChange={(e) => setKeywordInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && analyzeKeywords()}
                    className="flex-1"
                  />
                  <Button onClick={analyzeKeywords} disabled={isAnalyzing} className="bg-green-600 hover:bg-green-700">
                    {isAnalyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                        분석중...
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4 mr-2" />
                        분석하기
                      </>
                    )}
                  </Button>
                </div>

                {keywords.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">분석 결과</h3>
                      <Button
                        onClick={generateContent}
                        disabled={selectedKeywords.length === 0 || isGenerating}
                        className="bg-yellow-500 hover:bg-yellow-600"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        선택한 키워드로 콘텐츠 생성 ({selectedKeywords.length})
                      </Button>
                    </div>
                    
                    <div className="grid gap-4">
                      {keywords.map((keyword, index) => (
                        <Card key={index} className="border border-gray-200 hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <input
                                  type="checkbox"
                                  checked={selectedKeywords.includes(keyword.keyword)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedKeywords(prev => [...prev, keyword.keyword])
                                    } else {
                                      setSelectedKeywords(prev => prev.filter(k => k !== keyword.keyword))
                                    }
                                  }}
                                  className="w-4 h-4 text-green-600 rounded"
                                />
                                <h4 className="font-semibold text-lg">{keyword.keyword}</h4>
                              </div>
                              <div className="flex items-center gap-2">
                                {keyword.trend > 0 && (
                                  <Badge className="bg-green-100 text-green-700">
                                    <ArrowUp className="h-3 w-3 mr-1" />
                                    +{keyword.trend}%
                                  </Badge>
                                )}
                                {keyword.trend < 0 && (
                                  <Badge className="bg-red-100 text-red-700">
                                    <ArrowDown className="h-3 w-3 mr-1" />
                                    {keyword.trend}%
                                  </Badge>
                                )}
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                              <div>
                                <Label className="text-xs text-gray-500">월간 검색량</Label>
                                <p className="font-semibold">{keyword.searchVolume.toLocaleString()}</p>
                              </div>
                              <div>
                                <Label className="text-xs text-gray-500">경쟁도</Label>
                                <Badge variant={keyword.competition === 'low' ? 'secondary' : keyword.competition === 'medium' ? 'outline' : 'destructive'}>
                                  {keyword.competition}
                                </Badge>
                              </div>
                              <div>
                                <Label className="text-xs text-gray-500">난이도</Label>
                                <div className="flex items-center gap-2">
                                  <Progress value={keyword.difficulty} className="flex-1" />
                                  <span className="text-sm">{keyword.difficulty}</span>
                                </div>
                              </div>
                              <div>
                                <Label className="text-xs text-gray-500">트렌드</Label>
                                <p className={`font-semibold ${keyword.trend > 0 ? 'text-green-600' : keyword.trend < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                                  {keyword.trend > 0 ? '+' : ''}{keyword.trend}%
                                </p>
                              </div>
                            </div>
                            
                            <div>
                              <Label className="text-xs text-gray-500 mb-2 block">관련 키워드</Label>
                              <div className="flex flex-wrap gap-2">
                                {keyword.relatedKeywords.map((related, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {related}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 콘텐츠 생성 탭 */}
          <TabsContent value="content" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">생성된 콘텐츠</h2>
                <p className="text-gray-600">AI가 생성한 콘텐츠를 확인하고 편집하세요</p>
              </div>
              {isGenerating && (
                <div className="flex items-center gap-2 text-yellow-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600" />
                  콘텐츠 생성 중...
                </div>
              )}
            </div>

            {contents.length === 0 ? (
              <Card className="border-0 shadow-lg bg-white">
                <CardContent className="p-12 text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">생성된 콘텐츠가 없습니다</h3>
                  <p className="text-gray-600 mb-4">키워드 분석 탭에서 키워드를 선택하고 콘텐츠를 생성해보세요</p>
                  <Button onClick={() => setSelectedTab("keywords")} className="bg-green-600 hover:bg-green-700">
                    키워드 분석하러 가기
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-6">
                {contents.map((content) => (
                  <Card key={content.id} className="border-0 shadow-lg bg-white">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge className="bg-blue-100 text-blue-700">{content.keyword}</Badge>
                            <Badge variant={content.status === 'draft' ? 'outline' : content.status === 'scheduled' ? 'secondary' : 'default'}>
                              {content.status === 'draft' ? '초안' : content.status === 'scheduled' ? '예약됨' : '발행됨'}
                            </Badge>
                          </div>
                          <CardTitle className="text-xl">{content.title}</CardTitle>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Edit3 className="h-4 w-4 mr-2" />
                            편집
                          </Button>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <Eye className="h-4 w-4 mr-2" />
                                미리보기
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                              <DialogHeader>
                                <DialogTitle>{content.title}</DialogTitle>
                                <DialogDescription>
                                  키워드: {content.keyword} | 플랫폼: {content.platform}
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div className="prose max-w-none">
                                  <p className="whitespace-pre-wrap">{content.content}</p>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                          {content.status === 'draft' && (
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button className="bg-emerald-600 hover:bg-emerald-700" size="sm">
                                  <Send className="h-4 w-4 mr-2" />
                                  발행 예약
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>발행 예약</DialogTitle>
                                  <DialogDescription>
                                    콘텐츠를 발행할 날짜와 시간을 선택하세요
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div className="space-y-2">
                                    <Label>발행 날짜</Label>
                                    <Popover>
                                      <PopoverTrigger asChild>
                                        <Button variant="outline" className="w-full justify-start text-left font-normal">
                                          <CalendarIcon className="mr-2 h-4 w-4" />
                                          {selectedDate ? format(selectedDate, "PPP", { locale: ko }) : "날짜를 선택하세요"}
                                        </Button>
                                      </PopoverTrigger>
                                      <PopoverContent className="w-auto p-0">
                                        <Calendar
                                          mode="single"
                                          selected={selectedDate}
                                          onSelect={setSelectedDate}
                                          initialFocus
                                        />
                                      </PopoverContent>
                                    </Popover>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>발행 시간</Label>
                                    <Select value={selectedTime} onValueChange={setSelectedTime}>
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {Array.from({ length: 24 }, (_, i) => (
                                          <SelectItem key={i} value={`${i.toString().padStart(2, '0')}:00`}>
                                            {i.toString().padStart(2, '0')}:00
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <Switch
                                      id="auto-schedule"
                                      checked={autoSchedule}
                                      onCheckedChange={setAutoSchedule}
                                    />
                                    <Label htmlFor="auto-schedule">자동 스케줄 활성화</Label>
                                  </div>
                                  <Button 
                                    onClick={() => selectedDate && scheduleContent(content.id, selectedDate)}
                                    disabled={!selectedDate}
                                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                                  >
                                    예약하기
                                  </Button>
                                </div>
                              </DialogContent>
                            </Dialog>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <Label className="text-xs text-gray-500">단어 수</Label>
                          <p className="font-semibold">{content.wordCount.toLocaleString()}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500">SEO 점수</Label>
                          <div className="flex items-center gap-2">
                            <Progress value={content.seoScore} className="flex-1" />
                            <span className="text-sm font-semibold">{content.seoScore}</span>
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500">플랫폼</Label>
                          <p className="font-semibold">{content.platform}</p>
                        </div>
                        {content.scheduledDate && (
                          <div>
                            <Label className="text-xs text-gray-500">예약 일시</Label>
                            <p className="font-semibold text-emerald-600">
                              {format(content.scheduledDate, "MM/dd HH:mm", { locale: ko })}
                            </p>
                          </div>
                        )}
                      </div>
                      
                      <Separator />
                      
                      <div>
                        <Label className="text-xs text-gray-500 mb-2 block">콘텐츠 미리보기</Label>
                        <p className="text-sm text-gray-700 line-clamp-3">
                          {content.content.slice(0, 200)}...
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* 발행 스케줄 탭 */}
          <TabsContent value="schedule" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">발행 스케줄</h2>
                <p className="text-gray-600">예약된 콘텐츠의 발행 일정을 관리하세요</p>
              </div>
              <div className="flex items-center gap-2">
                <Switch />
                <Label>자동 발행</Label>
              </div>
            </div>

            {schedules.length === 0 ? (
              <Card className="border-0 shadow-lg bg-white">
                <CardContent className="p-12 text-center">
                  <CalendarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">예약된 콘텐츠가 없습니다</h3>
                  <p className="text-gray-600 mb-4">콘텐츠 생성 탭에서 콘텐츠를 생성하고 발행을 예약해보세요</p>
                  <Button onClick={() => setSelectedTab("content")} className="bg-emerald-600 hover:bg-emerald-700">
                    콘텐츠 관리하러 가기
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {schedules.map((schedule) => {
                  const content = contents.find(c => c.id === schedule.contentId)
                  if (!content) return null
                  
                  return (
                    <Card key={schedule.id} className="border-0 shadow-md bg-white">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className={`w-3 h-3 rounded-full ${
                              schedule.status === 'pending' ? 'bg-yellow-400' :
                              schedule.status === 'published' ? 'bg-green-400' : 'bg-red-400'
                            }`} />
                            <div>
                              <h4 className="font-semibold">{content.title}</h4>
                              <p className="text-sm text-gray-600">키워드: {content.keyword}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold">
                              {format(schedule.publishDate, "yyyy년 MM월 dd일", { locale: ko })}
                            </p>
                            <p className="text-sm text-gray-600">
                              {format(schedule.publishDate, "HH:mm", { locale: ko })} | {schedule.platform}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">
                              <Edit3 className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}