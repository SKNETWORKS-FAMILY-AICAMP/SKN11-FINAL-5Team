import type { Metadata } from 'next'
import './globals.css'
import { ToastProvider } from '@/lib/toast'

export const metadata: Metadata = {
  title: 'TinkerBell Business - 마케팅 자동화',
  description: '1인 창업자를 위한 AI 마케팅 자동화 플랫폼',
  generator: 'TinkerBell Business',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body>
        {children}
        <ToastProvider />
      </body>
    </html>
  )
}
