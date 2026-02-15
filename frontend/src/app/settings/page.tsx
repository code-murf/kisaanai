"use client"

import { useState } from "react"
import { User, MapPin, Bell, Globe, Shield, Moon, Sun, ChevronRight } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { usePathname } from "next/navigation"

export default function SettingsPage() {
  const pathname = usePathname()
  const [darkMode, setDarkMode] = useState(true)
  const [language, setLanguage] = useState("hi")
  const [notifications, setNotifications] = useState(true)

  const settingsSections = [
    {
      title: "Account",
      icon: User,
      items: [
        { label: "Phone Number", value: "+91 98765 43210", action: "Edit" },
        { label: "Name", value: "Ram Lal", action: "Edit" },
        { label: "Email", value: "ram@example.com", action: "Edit" },
      ],
    },
    {
      title: "Location",
      icon: MapPin,
      items: [
        { label: "State", value: "Uttar Pradesh", action: "Change" },
        { label: "District", value: "Meerut", action: "Change" },
        { label: "Default Mandi", value: "Meerut Mandi", action: "Change" },
      ],
    },
    {
      title: "Preferences",
      icon: Globe,
      items: [
        { label: "Language", value: language === "hi" ? "हिंदी (Hindi)" : "English", action: "Change", isLanguage: true },
        { label: "Dark Mode", value: darkMode ? "Enabled" : "Disabled", action: "", isToggle: true },
        { label: "Default Commodity", value: "Potato (Jyoti)", action: "Change" },
      ],
    },
    {
      title: "Notifications",
      icon: Bell,
      items: [
        { label: "Price Alerts", value: notifications ? "On" : "Off", action: "", isToggle: true },
        { label: "Weather Alerts", value: "On", action: "", isToggle: true },
        { label: "Market Updates", value: "Off", action: "", isToggle: true },
        { label: "WhatsApp Notifications", value: "Enabled", action: "Manage" },
      ],
    },
    {
      title: "Security",
      icon: Shield,
      items: [
        { label: "Change PIN", value: "", action: "Update" },
        { label: "Biometric Login", value: "Enabled", action: "", isToggle: true },
        { label: "Privacy Policy", value: "", action: "View" },
        { label: "Terms of Service", value: "", action: "View" },
      ],
    },
  ]

  const renderSettingItem = (item: any, sectionIndex: number, itemIndex: number) => {
    if (item.isToggle) {
      return (
        <div
          key={`${sectionIndex}-${itemIndex}`}
          className="flex items-center justify-between py-3 border-b last:border-0"
        >
          <div>
            <p className="font-medium">{item.label}</p>
            <p className="text-sm text-muted-foreground">{item.value}</p>
          </div>
          <button
            onClick={() => {
              if (item.label === "Dark Mode") setDarkMode(!darkMode)
              if (item.label.includes("Alerts") || item.label.includes("Login")) {
                // Toggle the specific setting
              }
            }}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              item.value === "On" || item.value === "Enabled" || darkMode ? "bg-primary" : "bg-muted"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${
                item.value === "On" || item.value === "Enabled" || darkMode ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>
      )
    }

    if (item.isLanguage) {
      return (
        <div key={`${sectionIndex}-${itemIndex}`} className="flex items-center justify-between py-3 border-b last:border-0">
          <div>
            <p className="font-medium">{item.label}</p>
            <p className="text-sm text-muted-foreground">{item.value}</p>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={language === "hi" ? "default" : "outline"}
              onClick={() => setLanguage("hi")}
            >
              हिंदी
            </Button>
            <Button
              size="sm"
              variant={language === "en" ? "default" : "outline"}
              onClick={() => setLanguage("en")}
            >
              English
            </Button>
          </div>
        </div>
      )
    }

    return (
      <button
        key={`${sectionIndex}-${itemIndex}`}
        className="flex items-center justify-between py-3 border-b last:border-0 w-full text-left hover:bg-accent/50 px-2 -mx-2 rounded transition-colors"
      >
        <div>
          <p className="font-medium">{item.label}</p>
          {item.value && <p className="text-sm text-muted-foreground">{item.value}</p>}
        </div>
        <div className="flex items-center gap-1 text-muted-foreground">
          <span className="text-sm">{item.action}</span>
          <ChevronRight className="h-4 w-4" />
        </div>
      </button>
    )
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-20">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your account and preferences</p>
      </header>

      {/* Profile Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
              RL
            </div>
            <div>
              <h3 className="text-lg font-semibold">Ram Lal</h3>
              <p className="text-sm text-muted-foreground">+91 98765 43210</p>
              <p className="text-xs text-primary">Verified Farmer</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Settings Sections */}
      {settingsSections.map((section, sectionIndex) => {
        const Icon = section.icon
        return (
          <Card key={sectionIndex}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Icon className="h-5 w-5 text-primary" />
                {section.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="px-6">
                {section.items.map((item, itemIndex) => renderSettingItem(item, sectionIndex, itemIndex))}
              </div>
            </CardContent>
          </Card>
        )
      })}

      {/* App Info */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="text-center space-y-2">
            <p className="font-medium">Agri-Analytics Platform</p>
            <p className="text-sm text-muted-foreground">Version 1.0.0</p>
            <p className="text-xs text-muted-foreground">Made with ❤️ for Indian Farmers</p>
          </div>
        </CardContent>
      </Card>

      {/* Logout Button */}
      <Button variant="destructive" className="w-full">
        Logout
      </Button>
    </div>
  )
}
