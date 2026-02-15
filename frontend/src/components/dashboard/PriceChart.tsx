"use client"


import { useEffect, useState } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface PriceData {
  date: string
  modal_price: number
  min_price: number
  max_price: number
}

interface PriceChartProps {
  commodityId?: number
}

export function PriceChart({ commodityId = 2 }: PriceChartProps) {
  const [data, setData] = useState<PriceData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/prices/trend/${commodityId}?days=7`)
        if (!res.ok) throw new Error("Failed to fetch")
        const json = await res.json()
        
        // Transform data for chart
        const chartData = json.map((item: any) => ({
          date: new Date(item.date).toLocaleDateString('en-US', { day: 'numeric', month: 'short' }),
          price: item.modal_price, // usage 'price' to match existing area chart dataKey
          ...item
        })).reverse() // Endpoint returns descending, chart wants ascending
        
        setData(chartData)
      } catch (error) {
        console.error("Error fetching price history:", error)
        // Fallback or empty
        setData([]) 
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [commodityId])

  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>Price Trends</CardTitle>
        <CardDescription>
          Daily average price in nearby mandis over the last 7 days.
        </CardDescription>
      </CardHeader>
      <CardContent className="pl-2">
        <ResponsiveContainer width="100%" height={350}>
            {loading ? (
                <div className="flex items-center justify-center h-full">Loading...</div>
            ) : (
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: number) => `₹${value}`}
            />
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
             <Tooltip
                content={({ active, payload }: { active?: boolean; payload?: any }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex flex-col">
                            <span className="text-[0.70rem] uppercase text-muted-foreground">
                              Date
                            </span>
                            <span className="font-bold text-muted-foreground">
                              {payload[0].payload.date}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[0.70rem] uppercase text-muted-foreground">
                              Price
                            </span>
                            <span className="font-bold">
                              ₹{payload[0].value}
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  }
                  return null
                }}
              />
            <Area
              type="monotone"
              dataKey="price"
              stroke="hsl(var(--primary))"
              fillOpacity={1}
              fill="url(#colorPrice)"
            />
          </AreaChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
