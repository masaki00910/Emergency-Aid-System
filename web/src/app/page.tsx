'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    router.push('/dashboard')
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-4xl mb-4">🚨</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">守り雲</h1>
        <p className="text-gray-600">災害情報ダッシュボードに移動中...</p>
      </div>
    </div>
  )
}