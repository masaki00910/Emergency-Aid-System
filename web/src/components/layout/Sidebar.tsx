'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/alerts',    label: 'Alerts'    },
  { href: '/feeds',     label: 'Feeds'     },
  { href: '/faq',       label: 'FAQ'       },
]

interface SidebarProps {
  className?: string
}

export default function Sidebar({ className = '' }: SidebarProps) {
  const pathname = usePathname()
  return (
    <aside className={`hidden md:block sticky top-0 h-dvh w-56 shrink-0 bg-zinc-900 text-zinc-50 ${className}`}>
      <div className="p-4 border-b border-zinc-800">
        <div className="text-xl font-semibold tracking-tight">守り雲</div>
      </div>
      <nav className="p-2 space-y-1">
        {items.map(it => {
          const active = pathname?.startsWith(it.href)
          return (
            <Link
              key={it.href}
              href={it.href}
              className={`block rounded-lg px-3 py-2 text-sm ${active ? 'bg-zinc-800' : 'hover:bg-zinc-800/60'}`}
            >
              {it.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
