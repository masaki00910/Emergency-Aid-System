'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/alerts',    label: 'Alerts'    },
  { href: '/faq',       label: 'FAQ'       },
]

interface SidebarProps {
  className?: string
}

export default function Sidebar({ className = '' }: SidebarProps) {
  const pathname = usePathname()
  return (
    <aside className={`hidden md:block sticky top-0 h-dvh w-64 shrink-0 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-zinc-50 animate-slide-up ${className}`}>
      <div className="p-6 border-b border-slate-700/50">
        <div className="flex items-center gap-3 animate-fade-in">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 via-cyan-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-slate-900 animate-pulse"></div>
          </div>
          <div>
            <div className="text-xl font-bold bg-gradient-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">
              WIND
            </div>
            <div className="text-xs text-slate-400 font-medium">
              Emergency Response
            </div>
          </div>
        </div>
      </div>
      <nav className="p-4 space-y-2">
        {items.map((it, index) => {
          const active = pathname?.startsWith(it.href)
          const icons = {
            '/dashboard': '📊',
            '/alerts': '🚨',
            '/faq': '❓'
          }
          return (
            <Link
              key={it.href}
              href={it.href}
              className={`group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300 animate-fade-in ${
                index === 0 ? 'animate-stagger-1' : index === 1 ? 'animate-stagger-2' : 'animate-stagger-3'
              } ${
                active
                  ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-cyan-300 shadow-lg border border-blue-500/30 pulse-glow'
                  : 'text-slate-300 hover:bg-slate-700/50 hover:text-white hover:shadow-md'
              }`}
            >
              <span className="text-lg animate-scale-in">{icons[it.href] || '📋'}</span>
              <span className="font-semibold">{it.label}</span>
              {active && (
                <div className="ml-auto w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
              )}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
