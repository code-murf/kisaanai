"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Map, BarChart3, Mic, Settings } from "lucide-react"
import { useTranslation } from "@/hooks/useTranslation"

import { cn } from "@/lib/utils"

export function BottomNav() {
  const pathname = usePathname()
  const { t } = useTranslation()

  const navItems = [
    {
      label: t("nav.home"),
      href: "/",
      icon: Home,
    },
    {
      label: t("nav.mandi"),
      href: "/mandi",
      icon: Map,
    },
    {
      label: t("nav.voice"),
      href: "/voice",
      icon: Mic,
      isFloating: true,
    },
    {
      label: t("nav.charts"),
      href: "/charts",
      icon: BarChart3,
    },
    {
      label: t("nav.settings"),
      href: "/settings",
      icon: Settings,
    },
  ]

  return (
    <div className="fixed bottom-4 left-0 right-0 z-50 px-2 md:bottom-6 md:px-6">
      <div className="mx-auto w-full max-w-screen-md rounded-2xl border bg-background/80 pb-[env(safe-area-inset-bottom)] shadow-lg backdrop-blur-lg supports-[backdrop-filter]:bg-background/60">
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
                  "flex flex-col items-center justify-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors hover:bg-muted focus:bg-muted active:bg-muted",
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
    </div>
  )
}
