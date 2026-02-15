
"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Minus, Info } from "lucide-react"

interface ForecastData {
  commodity_name: string
  mandi_name: string
  current_price: number
  predicted_price: number
  price_change_pct: number
  trend: "up" | "down" | "stable"
  confidence: number
  explanation?: {
      text: string
  }
  prediction_date: string
  target_date: string
}

interface ForecastWidgetProps {
  commodityId: number
}

export function ForecastWidget({ commodityId }: ForecastWidgetProps) {
  const [data, setData] = useState<ForecastData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchForecast() {
      try {
        setLoading(true)
        // Defaulting to mandi_id=1 (Azadpur) for demo
        const res = await fetch(`http://localhost:8000/api/v1/forecasts/${commodityId}/1?horizon_days=7`)
        if (!res.ok) throw new Error("Failed to fetch forecast")
        const json = await res.json()
        setData(json)
      } catch (error) {
        console.error(error)
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchForecast()
  }, [commodityId])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Price Forecast (7 Days)</CardTitle>
          <CardDescription>AI-powered price prediction</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-24 flex items-center justify-center text-muted-foreground">
            Analyzing market trends...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Price Forecast</CardTitle>
        </CardHeader>
        <CardContent>
            <p className="text-muted-foreground">Forecast unavailable for this item.</p>
        </CardContent>
      </Card>
    )
  }

  const isUp = data.trend === "up"
  const isDown = data.trend === "down"

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">7-Day Price Forecast</CardTitle>
        <CardDescription>
            {data.mandi_name}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
            <div>
                <span className="text-3xl font-bold">₹{data.predicted_price}</span>
                <span className="text-muted-foreground text-sm ml-1">/ quintal</span>
            </div>
            <div className={`flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                isUp ? "bg-green-100 text-green-700" : 
                isDown ? "bg-red-100 text-red-700" : 
                "bg-gray-100 text-gray-700"
            }`}>
                {isUp ? <TrendingUp className="h-4 w-4 mr-1" /> : 
                 isDown ? <TrendingDown className="h-4 w-4 mr-1" /> : 
                 <Minus className="h-4 w-4 mr-1" />}
                {Math.abs(data.price_change_pct).toFixed(1)}%
            </div>
        </div>
        
        <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Current Price</span>
                <span className="font-medium">₹{data.current_price}</span>
            </div>
             <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Confidence</span>
                <span className="font-medium">{(data.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>

        {data.explanation && (
            <div className="mt-4 pt-4 border-t text-sm text-muted-foreground">
                <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 mt-0.5 shrink-0" />
                    <p>{data.explanation.text}</p>
                </div>
            </div>
        )}
      </CardContent>
    </Card>
  )
}
