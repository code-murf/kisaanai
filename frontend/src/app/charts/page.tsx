"use client"

import { useState } from "react"
import { TrendingUp, TrendingDown, Calendar, Download, Info } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

// Mock data
const priceHistoryData = [
  { date: "Jan 01", price: 1180, min: 1150, max: 1210 },
  { date: "Jan 02", price: 1195, min: 1170, max: 1220 },
  { date: "Jan 03", price: 1180, min: 1155, max: 1205 },
  { date: "Jan 04", price: 1210, min: 1180, max: 1240 },
  { date: "Jan 05", price: 1230, min: 1200, max: 1260 },
  { date: "Jan 06", price: 1240, min: 1210, max: 1270 },
  { date: "Jan 07", price: 1240, min: 1220, max: 1260 },
  { date: "Jan 08", price: 1255, min: 1230, max: 1280 },
  { date: "Jan 09", price: 1240, min: 1210, max: 1270 },
  { date: "Jan 10", price: 1260, min: 1230, max: 1290 },
  { date: "Jan 11", price: 1275, min: 1240, max: 1310 },
  { date: "Jan 12", price: 1280, min: 1250, max: 1310 },
]

const forecastData = [
  { date: "Jan 12", price: 1280, lower: 1250, upper: 1310, type: "historical" },
  { date: "Jan 13", price: 1290, lower: 1240, upper: 1340, type: "forecast" },
  { date: "Jan 14", price: 1295, lower: 1230, upper: 1360, type: "forecast" },
  { date: "Jan 15", price: 1285, lower: 1210, upper: 1360, type: "forecast" },
  { date: "Jan 16", price: 1270, lower: 1180, upper: 1360, type: "forecast" },
  { date: "Jan 17", price: 1260, lower: 1160, upper: 1360, type: "forecast" },
  { date: "Jan 18", price: 1255, lower: 1140, upper: 1370, type: "forecast" },
]

const mandiComparisonData = [
  { name: "Azadpur", price: 1240, arrival: 4500 },
  { name: "Okhla", price: 1210, arrival: 3200 },
  { name: "Ghazipur", price: 1260, arrival: 2800 },
  { name: "Keshopur", price: 1230, arrival: 1900 },
  { name: "Narela", price: 1195, arrival: 2400 },
  { name: "Bahadurgarh", price: 1250, arrival: 1600 },
]

const timeRanges = [
  { label: "7D", value: "7d" },
  { label: "30D", value: "30d" },
  { label: "90D", value: "90d" },
  { label: "1Y", value: "1y" },
]

export default function ChartsPage() {
  const [timeRange, setTimeRange] = useState("7d")
  const [chartType, setChartType] = useState<"price" | "forecast" | "comparison">("price")

  const currentPrice = priceHistoryData[priceHistoryData.length - 1].price
  const previousPrice = priceHistoryData[0].price
  const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100

  interface TooltipPayload {
    color: string
    name: string
    value: number | string
  }

  interface CustomTooltipProps {
    active?: boolean
    payload?: TooltipPayload[]
    label?: string
  }

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-background p-3 shadow-md">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-20">
      <header className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Price Analytics</h1>
          <p className="text-muted-foreground">Historical trends and forecasts for Potato (Jyoti)</p>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2">
          {timeRanges.map((range) => (
            <Button
              key={range.value}
              variant={timeRange === range.value ? "default" : "outline"}
              size="sm"
              onClick={() => setTimeRange(range.value)}
            >
              {range.label}
            </Button>
          ))}
        </div>
      </header>

      {/* Price Summary Cards */}
      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Price</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{currentPrice}</div>
            <p className="text-xs text-muted-foreground">per quintal</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Price Change</CardTitle>
            {priceChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${priceChange >= 0 ? "text-green-500" : "text-red-500"}`}>
              {priceChange > 0 ? "+" : ""}{priceChange.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">vs {timeRanges.find(r => r.value === timeRange)?.label}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Best Day to Sell</CardTitle>
            <Calendar className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Wed-Thu</div>
            <p className="text-xs text-muted-foreground">Based on historical data</p>
          </CardContent>
        </Card>
      </section>

      {/* Chart Type Selector */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Button
          variant={chartType === "price" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("price")}
        >
          Price History
        </Button>
        <Button
          variant={chartType === "forecast" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("forecast")}
        >
          AI Forecast
        </Button>
        <Button
          variant={chartType === "comparison" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("comparison")}
        >
          Mandi Comparison
        </Button>
      </div>

      {/* Charts */}
      {chartType === "price" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Price History</CardTitle>
                <CardDescription>Daily price movement over selected period</CardDescription>
              </div>
              <Button size="sm" variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={priceHistoryData}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="hsl(var(--primary))"
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {chartType === "forecast" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>AI Price Forecast</CardTitle>
                <CardDescription>7-day prediction with confidence interval</CardDescription>
              </div>
              <Button size="icon" variant="outline">
                <Info className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={forecastData}>
                <defs>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(142, 76%, 36%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(142, 76%, 36%)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--muted-foreground) / 0.2)" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="hsl(var(--muted-foreground) / 0.05)" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="transparent"
                  fill="url(#colorConfidence)"
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="transparent"
                  fill="hsl(var(--background))"
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="hsl(142, 76%, 36%)"
                  fillOpacity={1}
                  fill="url(#colorForecast)"
                  name="Predicted Price"
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                  name="Historical Price"
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-4 rounded-lg bg-muted/50 p-4">
              <p className="text-sm font-medium mb-2">AI Insights</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Price expected to peak on Jan 14 (₹1,295)</li>
                <li>• Moderate confidence due to upcoming weather</li>
                <li>• Consider selling before Jan 16 for better returns</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {chartType === "comparison" && (
        <Card>
          <CardHeader>
            <CardTitle>Mandi Price Comparison</CardTitle>
            <CardDescription>Compare prices across nearby mandis</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={mandiComparisonData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis type="category" dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis type="number" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="price" fill="hsl(var(--primary))" name="Price (₹/Q)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Additional Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Price Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Highest (7 days)</p>
              <p className="text-xl font-bold">₹1,280</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Lowest (7 days)</p>
              <p className="text-xl font-bold">₹1,180</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Average</p>
              <p className="text-xl font-bold">₹1,237</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Volatility</p>
              <p className="text-xl font-bold">Low</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
