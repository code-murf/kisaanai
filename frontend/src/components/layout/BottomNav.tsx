"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Map, BarChart3, Mic, Settings } from "lucide-react"

import { cn } from "@/lib/utils"
// import { Button } from "@/components/ui/button" // might use for the mic button

export function BottomNav() {
  const pathname = usePathname()

  const navItems = [
    {
      label: "Home",
      href: "/",
      icon: Home,
    },
    {
      label: "Mandi",
      href: "/mandi",
      icon: Map,
    },
    {
      label: "Voice",
      href: "/voice",
      icon: Mic,
      isFloating: true,
    },
    {
      label: "Charts",
      href: "/charts",
      icon: BarChart3,
    },
    {
      label: "Settings",
      href: "/settings",
      icon: Settings,
    },
  ]

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full border-t bg-background/80 backdrop-blur-lg supports-[backdrop-filter]:bg-background/60 md:hidden">
      <div className="flex h-16 items-center justify-around px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          if (item.isFloating) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative -top-5 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-110 active:scale-95"
              >
                <item.icon className="h-6 w-6" />
                <span className="sr-only">{item.label}</span>
              </Link>
            )
          }
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 rounded-lg px-2 py-1 text-xs font-medium transition-colors hover:bg-muted focus:bg-muted active:bg-muted",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
