"use client"

import { useEffect, useMemo, useState } from "react"
import { TrendingUp, TrendingDown, Calendar, Download, Info } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslation } from "@/hooks/useTranslation"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

const timeRanges = [
  { label: "7D", value: "7d", days: 7 },
  { label: "30D", value: "30d", days: 30 },
  { label: "90D", value: "90d", days: 90 },
  { label: "1Y", value: "1y", days: 365 },
]

const API_BASE_URL = ""
const DEFAULT_MANDI_ID = Number(process.env.NEXT_PUBLIC_DEFAULT_MANDI_ID || "1")

interface TrendPoint {
  date: string
  modal_price: number
  min_price: number
  max_price: number
}

interface ForecastPoint {
  date: string
  price: number
  lower: number
  upper: number
  horizon: number
}

interface MandiPricePoint {
  name: string
  price: number
  arrival: number
}

interface Commodity {
  id: number
  name: string
}

function formatDate(rawDate: string): string {
  return new Date(rawDate).toLocaleDateString("en-US", { day: "numeric", month: "short" })
}

function formatCurrency(value: number): string {
  return `Rs ${Math.round(value).toLocaleString("en-IN")}`
}

export default function ChartsPage() {
  const [timeRange, setTimeRange] = useState("7d")
  const [chartType, setChartType] = useState<"price" | "forecast" | "comparison">("price")
  const [trendData, setTrendData] = useState<TrendPoint[]>([])
  const [forecastData, setForecastData] = useState<ForecastPoint[]>([])
  const [mandiComparisonData, setMandiComparisonData] = useState<MandiPricePoint[]>([])
  const [commodityName, setCommodityName] = useState("Selected Commodity")
  const [mandiName, setMandiName] = useState(`Mandi ${DEFAULT_MANDI_ID}`)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [commodities, setCommodities] = useState<Commodity[]>([])
  const [selectedCommodityId, setSelectedCommodityId] = useState<number>(
    Number(process.env.NEXT_PUBLIC_DEFAULT_COMMODITY_ID || "2")
  )
  const { t } = useTranslation()

  const selectedDays = useMemo(
    () => timeRanges.find((range) => range.value === timeRange)?.days ?? 7,
    [timeRange]
  )

  // Fetch commodities list on mount
  useEffect(() => {
    async function fetchCommodities() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/commodities`)
        if (res.ok) {
          const data = await res.json()
          const items: Commodity[] = (data.items || data || []).map((c: Record<string, unknown>) => ({
            id: Number(c.id),
            name: String(c.name || ""),
          }))
          if (items.length > 0) setCommodities(items)
        }
      } catch {
        // Keep empty — selector will be hidden
      }
    }
    fetchCommodities()
  }, [])

  useEffect(() => {
    let cancelled = false

    async function fetchAnalyticsData() {
      setLoading(true)
      setError(null)
      try {
        const [trendRes, currentRes, forecastRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/prices/trend/${selectedCommodityId}?days=${selectedDays}`),
          fetch(`${API_BASE_URL}/api/v1/prices/current/commodity/${selectedCommodityId}?limit=8`),
          fetch(
            `${API_BASE_URL}/api/v1/forecasts/${selectedCommodityId}/${DEFAULT_MANDI_ID}/multi-horizon?horizons=1,3,7,14,30`
          ),
        ])

        if (!trendRes.ok) {
          throw new Error("Unable to load price trend data from API.")
        }
        if (!currentRes.ok) {
          throw new Error("Unable to load current mandi prices from API.")
        }

        const trendJson = (await trendRes.json()) as Array<Record<string, unknown>>
        const currentJson = (await currentRes.json()) as Array<Record<string, unknown>>

        const parsedTrendData: TrendPoint[] = trendJson
          .map((item) => ({
            date: formatDate(String(item.date ?? "")),
            modal_price: Number(item.modal_price ?? 0),
            min_price: Number(item.min_price ?? 0),
            max_price: Number(item.max_price ?? 0),
          }))
          .reverse()

        const parsedMandiComparison: MandiPricePoint[] = currentJson.slice(0, 8).map((item) => {
          const mandi = item.mandi as Record<string, unknown> | undefined
          return {
            name: String(item.mandi_name ?? mandi?.name ?? "Unknown"),
            price: Number(item.modal_price ?? 0),
            arrival: Number(item.arrival_qty ?? 0),
          }
        })

        const currentFirst = currentJson[0]
        if (currentFirst) {
          const commodity = currentFirst.commodity as Record<string, unknown> | undefined
          const mandi = currentFirst.mandi as Record<string, unknown> | undefined
          const nextCommodityName = String(currentFirst.commodity_name ?? commodity?.name ?? "").trim()
          const nextMandiName = String(currentFirst.mandi_name ?? mandi?.name ?? "").trim()
          if (nextCommodityName) setCommodityName(nextCommodityName)
          if (nextMandiName) setMandiName(nextMandiName)
        }

        let parsedForecastData: ForecastPoint[] = []
        if (forecastRes.ok) {
          const forecastJson = (await forecastRes.json()) as {
            forecasts?: Record<string, Record<string, unknown>>
          }
          const forecastEntries = Object.values(forecastJson.forecasts ?? {})
          parsedForecastData = forecastEntries
            .map((entry) => ({
              date: formatDate(String(entry.target_date ?? "")),
              price: Number(entry.predicted_price ?? 0),
              lower: Number(entry.confidence_lower ?? 0),
              upper: Number(entry.confidence_upper ?? 0),
              horizon: Number(entry.horizon_days ?? 0),
            }))
            .sort((a, b) => a.horizon - b.horizon)

          const forecastFirst = forecastEntries[0]
          if (forecastFirst) {
            const nextCommodityName = String(forecastFirst.commodity_name ?? "").trim()
            const nextMandiName = String(forecastFirst.mandi_name ?? "").trim()
            if (nextCommodityName) setCommodityName(nextCommodityName)
            if (nextMandiName) setMandiName(nextMandiName)
          }
        } else if (forecastRes.status !== 404) {
          throw new Error("Unable to load forecast data from API.")
        }

        if (!cancelled) {
          setTrendData(parsedTrendData)
          setMandiComparisonData(parsedMandiComparison)
          setForecastData(parsedForecastData)
        }
      } catch (fetchError) {
        if (!cancelled) {
          setTrendData([])
          setMandiComparisonData([])
          setForecastData([])
          setError(fetchError instanceof Error ? fetchError.message : "Failed to load analytics data.")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchAnalyticsData()
    return () => {
      cancelled = true
    }
  }, [selectedDays, selectedCommodityId])

  const currentPrice = trendData.length > 0 ? trendData[trendData.length - 1].modal_price : 0
  const previousPrice = trendData.length > 0 ? trendData[0].modal_price : 0
  const priceChange = previousPrice > 0 ? ((currentPrice - previousPrice) / previousPrice) * 100 : 0
  const bestSellDate =
    trendData.length > 0
      ? trendData.reduce((best, point) => (point.modal_price > best.modal_price ? point : best), trendData[0]).date
      : "N/A"
  const highestPrice = trendData.length > 0 ? Math.max(...trendData.map((point) => point.modal_price)) : 0
  const lowestPrice = trendData.length > 0 ? Math.min(...trendData.map((point) => point.modal_price)) : 0
  const averagePrice =
    trendData.length > 0
      ? trendData.reduce((sum, point) => sum + point.modal_price, 0) / trendData.length
      : 0
  const volatility = (() => {
    if (trendData.length === 0 || averagePrice === 0) return 0
    const variance =
      trendData.reduce((sum, point) => sum + (point.modal_price - averagePrice) ** 2, 0) / trendData.length
    return (Math.sqrt(variance) / averagePrice) * 100
  })()

  // Compute Y-axis domain with 10% padding so price line is clearly visible
  const trendYDomain = useMemo(() => {
    if (trendData.length === 0) return [0, 100]
    const prices = trendData.map((p) => p.modal_price).filter((v) => v > 0)
    if (prices.length === 0) return [0, 100]
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const padding = Math.max((max - min) * 0.15, 50)
    return [Math.floor(min - padding), Math.ceil(max + padding)]
  }, [trendData])

  const forecastYDomain = useMemo(() => {
    if (forecastData.length === 0) return [0, 100]
    const allValues = forecastData.flatMap((p) => [p.price, p.lower, p.upper]).filter((v) => v > 0)
    if (allValues.length === 0) return [0, 100]
    const min = Math.min(...allValues)
    const max = Math.max(...allValues)
    const padding = Math.max((max - min) * 0.15, 50)
    return [Math.floor(min - padding), Math.ceil(max + padding)]
  }, [forecastData])

  const comparisonYDomain = useMemo(() => {
    if (mandiComparisonData.length === 0) return [0, 100]
    const prices = mandiComparisonData.map((p) => p.price).filter((v) => v > 0)
    if (prices.length === 0) return [0, 100]
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const padding = Math.max((max - min) * 0.15, 50)
    return [Math.floor(min - padding), Math.ceil(max + padding)]
  }, [mandiComparisonData])

  const exportTrendData = () => {
    if (trendData.length === 0) return

    const csvHeader = "date,modal_price,min_price,max_price\n"
    const csvRows = trendData
      .map((point) => `${point.date},${point.modal_price},${point.min_price},${point.max_price}`)
      .join("\n")
    const blob = new Blob([csvHeader + csvRows], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `kisaanai-price-trend-${timeRange}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

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
          <h1 className="text-2xl font-bold tracking-tight">{t("charts.title")}</h1>
          <p className="text-muted-foreground">{t("charts.subtitle")} {t("entities." + commodityName)}</p>
        </div>

        {/* Commodity Selector */}
        {commodities.length > 0 && (
          <Select
            value={String(selectedCommodityId)}
            onValueChange={(val) => setSelectedCommodityId(Number(val))}
          >
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Select commodity" />
            </SelectTrigger>
            <SelectContent>
              {commodities.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

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

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Summary Cards with Skeletons */}
      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t("charts.currentPrice")}</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <div className="text-2xl font-bold">
                {currentPrice > 0 ? formatCurrency(currentPrice) : t("charts.noData")}
              </div>
            )}
            <p className="text-xs text-muted-foreground">{t("charts.perQuintal")}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t("charts.priceChange")}</CardTitle>
            {priceChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className={`text-2xl font-bold ${priceChange >= 0 ? "text-green-500" : "text-red-500"}`}>
                {previousPrice > 0
                  ? `${priceChange > 0 ? "+" : ""}${priceChange.toFixed(1)}%`
                  : t("charts.noData")}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              vs {timeRanges.find((r) => r.value === timeRange)?.label}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t("charts.bestDayToSell")}</CardTitle>
            <Calendar className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-28" />
            ) : (
              <div className="text-2xl font-bold">{bestSellDate}</div>
            )}
            <p className="text-xs text-muted-foreground">{t("charts.basedOnHistory")}</p>
          </CardContent>
        </Card>
      </section>

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
          {t("charts.aiForecast")}
        </Button>
        <Button
          variant={chartType === "comparison" ? "default" : "outline"}
          size="sm"
          onClick={() => setChartType("comparison")}
        >
          {t("charts.mandiComparison")}
        </Button>
      </div>

      {chartType === "price" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t("charts.priceHistory")}</CardTitle>
                <CardDescription>{t("charts.dailyMovement")}</CardDescription>
              </div>
              <Button size="sm" variant="outline" disabled={trendData.length === 0} onClick={exportTrendData}>
                <Download className="mr-2 h-4 w-4" />
                {t("charts.export")}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                <Skeleton className="h-[350px] w-full rounded-lg" />
              </div>
            ) : trendData.length === 0 ? (
              <div className="flex h-[350px] items-center justify-center text-sm text-muted-foreground">
                {t("charts.noTrend")}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    domain={trendYDomain}
                    tickFormatter={(value: number) => formatCurrency(value)}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="modal_price"
                    name="Modal Price"
                    stroke="hsl(var(--primary))"
                    fillOpacity={1}
                    fill="url(#colorPrice)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      )}

      {chartType === "forecast" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t("charts.aiForecast")}</CardTitle>
                <CardDescription>{t("charts.forecastDesc")}</CardDescription>
              </div>
              <Button size="icon" variant="outline">
                <Info className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[350px] w-full rounded-lg" />
            ) : forecastData.length === 0 ? (
              <div className="flex h-[350px] items-center justify-center text-sm text-muted-foreground">
                Forecast unavailable for commodity {selectedCommodityId} at {mandiName}.
              </div>
            ) : (
              <>
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
                    <YAxis
                      stroke="#888888"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      domain={forecastYDomain}
                      tickFormatter={(value: number) => formatCurrency(value)}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="upper"
                      stroke="transparent"
                      fill="url(#colorConfidence)"
                      name="Upper Bound"
                    />
                    <Area
                      type="monotone"
                      dataKey="lower"
                      stroke="transparent"
                      fill="hsl(var(--background))"
                      name="Lower Bound"
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
                      name="Forecast Line"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                <div className="mt-4 rounded-lg bg-muted/50 p-4">
                  <p className="mb-2 text-sm font-medium">{t("charts.forecastContext")}</p>
                  <p className="text-sm text-muted-foreground">
                    Multi-horizon model forecast for {commodityName} at {mandiName}.
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {chartType === "comparison" && (
        <Card>
          <CardHeader>
            <CardTitle>{t("charts.mandiComparison")}</CardTitle>
            <CardDescription>{t("charts.compareDesc")}</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-[350px] w-full rounded-lg" />
            ) : mandiComparisonData.length === 0 ? (
              <div className="flex h-[350px] items-center justify-center text-sm text-muted-foreground">
                {t("charts.noMandiPrices")}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={mandiComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis
                    stroke="#888888"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    domain={comparisonYDomain}
                    tickFormatter={(value: number) => formatCurrency(value)}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="price" fill="hsl(var(--primary))" name="Price (Rs/Q)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t("charts.priceStats")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">
                {t("charts.highest")} ({timeRanges.find((r) => r.value === timeRange)?.label})
              </p>
              <p className="text-xl font-bold">{highestPrice > 0 ? formatCurrency(highestPrice) : t("charts.noData")}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">
                {t("charts.lowest")} ({timeRanges.find((r) => r.value === timeRange)?.label})
              </p>
              <p className="text-xl font-bold">{lowestPrice > 0 ? formatCurrency(lowestPrice) : t("charts.noData")}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t("charts.average")}</p>
              <p className="text-xl font-bold">{averagePrice > 0 ? formatCurrency(averagePrice) : t("charts.noData")}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{t("charts.volatility")}</p>
              <p className="text-xl font-bold">{trendData.length > 0 ? `${volatility.toFixed(1)}%` : t("charts.noData")}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
