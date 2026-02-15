
"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"
import { Sun, Cloud, CloudRain, Droplets, Wind, AlertTriangle } from "lucide-react"
import { format } from "date-fns"

interface WeatherForecast {
  date: string
  temp_min: number
  temp_max: number
  rainfall_mm: number
  humidity_pct: number
  condition: string
  advisory: string
  icon: string
}

export function WeatherWidget() {
  const [forecasts, setForecasts] = useState<WeatherForecast[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch weather data
    // In a real app, use React Query and proper API client
    const fetchWeather = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/weather/forecast?lat=28.7041&lon=77.1025&days=14`)
        if (!res.ok) throw new Error("Failed to fetch weather data")
        const data = await res.json()
        setForecasts(data)
      } catch (err) {
            console.error(err)
            // Fallback mock data for demo if API fails (e.g. if backend not running/cors issues)
             const mockData: WeatherForecast[] = Array.from({ length: 14 }).map((_, i) => {
                const date = new Date()
                date.setDate(date.getDate() + i)
                return {
                    date: date.toISOString().split('T')[0],
                    temp_min: 20 + Math.random() * 5,
                    temp_max: 30 + Math.random() * 5,
                    rainfall_mm: Math.random() > 0.7 ? Math.random() * 10 : 0,
                    humidity_pct: 50 + Math.random() * 20,
                    condition: Math.random() > 0.7 ? "rain" : "sunny",
                    advisory: "Conditions match fallback mock.",
                    icon: Math.random() > 0.7 ? "cloud-rain" : "sun"
                }
            })
            setForecasts(mockData)
            // setError("Using offline mode") 
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [])

  if (loading) return <div className="h-48 w-full bg-muted animate-pulse rounded-md" />

  const todayForecast = forecasts[0]

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "sun": return <Sun className="h-6 w-6 text-yellow-500" />
      case "cloud": return <Cloud className="h-6 w-6 text-gray-400" />
      case "cloud-rain": return <CloudRain className="h-6 w-6 text-blue-500" />
      default: return <Sun className="h-6 w-6 text-yellow-500" />
    }
  }

  return (
    <Card className="w-full shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            14-Day Weather & Advisory
          </CardTitle>
          {todayForecast && (
             <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-3 py-1 rounded-full border border-amber-200 dark:border-amber-800/50">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">Advisory: {todayForecast.advisory}</span>
             </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="w-full whitespace-nowrap pb-4">
          <div className="flex w-max space-x-4 p-1">
            {forecasts.map((day, i) => (
              <div
                key={i}
                className={`flex flex-col items-center p-3 rounded-lg border w-28 shrink-0 transition-colors ${
                  i === 0 ? "bg-primary/5 border-primary/20 shadow-sm" : "bg-card hover:bg-muted/50"
                }`}
              >
                <span className="text-xs font-medium text-muted-foreground mb-1">
                    {format(new Date(day.date), "EEE, MMM d")}
                </span>
                <div className="my-2 p-2 bg-background/50 rounded-full shadow-sm ring-1 ring-inset ring-border">
                    {getIcon(day.icon)}
                </div>
                <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-lg font-bold">{Math.round(day.temp_max)}°</span>
                    <span className="text-xs text-muted-foreground">/ {Math.round(day.temp_min)}°</span>
                </div>
                <div className="flex items-center gap-1 mt-2 text-xs text-blue-500 dark:text-blue-400 font-medium">
                    <Droplets className="h-3 w-3" />
                    <span>{Number(day.rainfall_mm).toFixed(1)}mm</span>
                </div>
              </div>
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
