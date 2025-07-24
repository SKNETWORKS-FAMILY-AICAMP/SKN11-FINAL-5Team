"use client"

import { Button } from "@/components/ui/button"
import { Zap, Share2, Mail } from "lucide-react"

interface TabMenuProps {
  activeTab: string
  setActiveTab: (tab: string) => void
  onTabChange: () => void
}

export function TabMenu({ activeTab, setActiveTab, onTabChange }: TabMenuProps) {
  const handleTabClick = (tab: string) => {
    setActiveTab(tab)
    onTabChange()
  }

  return (
    <div className="mb-6">
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl w-fit">
        <Button
          variant={activeTab === "automation" ? "default" : "ghost"}
          className={`flex items-center space-x-2 rounded-lg text-sm px-4 py-2 h-9 ${
            activeTab === "automation" ? "bg-green-500 hover:bg-green-600 text-white shadow-sm" : "hover:bg-gray-200"
          }`}
          onClick={() => handleTabClick("automation")}
        >
          <Zap className="h-4 w-4" />
          <span>자동화 업무</span>
        </Button>
        <Button
          variant={activeTab === "sns" ? "default" : "ghost"}
          className={`flex items-center space-x-2 rounded-lg text-sm px-4 py-2 h-9 ${
            activeTab === "sns" ? "bg-green-500 hover:bg-green-600 text-white shadow-sm" : "hover:bg-gray-200"
          }`}
          onClick={() => handleTabClick("sns")}
        >
          <Share2 className="h-4 w-4" />
          <span>SNS 컨텐츠</span>
        </Button>
        <Button
          variant={activeTab === "email" ? "default" : "ghost"}
          className={`flex items-center space-x-2 rounded-lg text-sm px-4 py-2 h-9 ${
            activeTab === "email" ? "bg-green-500 hover:bg-green-600 text-white shadow-sm" : "hover:bg-gray-200"
          }`}
          onClick={() => handleTabClick("email")}
        >
          <Mail className="h-4 w-4" />
          <span>이메일</span>
        </Button>
      </div>
    </div>
  )
}
