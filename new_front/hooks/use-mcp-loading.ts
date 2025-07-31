"use client"

import { useState, useCallback } from "react"
import type { MCPSourceType } from "@/components/ui/mcp-loading-indicator"

interface MCPLoadingState {
  isLoading: boolean
  sourceType: MCPSourceType | null
  sources: MCPSourceType[]
}

export function useMCPLoading() {
  const [loadingState, setLoadingState] = useState<MCPLoadingState>({
    isLoading: false,
    sourceType: null,
    sources: [],
  })

  const startLoading = useCallback((sourceType: MCPSourceType) => {
    setLoadingState({
      isLoading: true,
      sourceType,
      sources: [sourceType],
    })
  }, [])

  const startMultiLoading = useCallback((sources: MCPSourceType[]) => {
    setLoadingState({
      isLoading: true,
      sourceType: sources[0] || null,
      sources,
    })
  }, [])

  const stopLoading = useCallback(() => {
    setLoadingState({
      isLoading: false,
      sourceType: null,
      sources: [],
    })
  }, [])

  const updateLoadingSource = useCallback((sourceType: MCPSourceType) => {
    setLoadingState((prev) => ({
      ...prev,
      sourceType,
      sources: prev.sources.includes(sourceType) ? prev.sources : [...prev.sources, sourceType],
    }))
  }, [])

  return {
    ...loadingState,
    startLoading,
    startMultiLoading,
    stopLoading,
    updateLoadingSource,
  }
}
