"use client"

import * as React from "react"
import { Toaster } from "@/components/ui/sonner"
import { toast } from "sonner"

// Toast 유틸리티 함수들
export const showSuccessToast = (message: string) => {
  toast.success(message)
}

export const showErrorToast = (message: string) => {
  toast.error(message)
}

export const showInfoToast = (message: string) => {
  toast.info(message)
}

export const showLoadingToast = (message: string) => {
  return toast.loading(message)
}

// Toast Provider 컴포넌트
export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
    />
  )
}