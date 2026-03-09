"use client"

import { useState, useEffect } from "react"
import { MapPin, Navigation, TrendingUp, TrendingDown, Search, Filter, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import dynamic from "next/dynamic"
import { useTranslation } from "@/hooks/useTranslation"

const MandiMap = dynamic(
  () => import("@/components/dashboard/MandiMap"),
  {
    loading: () => <div className="h-[400px] w-full flex items-center justify-center bg-muted animate-pulse rounded-md">Loading Map...</div>,
    ssr: false
  }
)

const API_BASE_URL = ""

interface ApiMandi {
  id: number
  name: string
  district: string
  state: string
  latitude: number
  longitude: number
  market_type: string
  is_active: boolean
}

interface ApiPrice {
  mandi_id: number
  commodity_id: number
  price_date: string
  modal_price: number
  min_price: number
  max_price: number
  arrival_qty: number
}

interface Mandi {
  id: number
  name: string
  district: string
  state: string
  price: number
  trend: number
  distance: number
  arrival: number
  latitude: number
  longitude: number
}

function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return Math.round(R * c)
}

export default function MandiPage() {
  const [mandis, setMandis] = useState<Mandi[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"price" | "distance" | "arrival" | "nearby">("nearby")
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const { t } = useTranslation()

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          })
        },
        () => {
          // Default to Delhi if location denied
          setUserLocation({ lat: 28.6139, lng: 77.2090 })
        }
      )
    } else {
      setUserLocation({ lat: 28.6139, lng: 77.2090 })
    }
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)

        // Fetch mandis and latest prices in parallel
        const [mandisRes, pricesRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/mandis?page_size=50`),
          fetch(`${API_BASE_URL}/api/v1/prices?commodity_id=1&page_size=200`),
        ])

        if (!mandisRes.ok || !pricesRes.ok) {
          throw new Error("Failed to fetch data from API")
        }

        const mandisData = await mandisRes.json()
        const pricesData = await pricesRes.json()

        const apiMandis: ApiMandi[] = mandisData.items || []
        const apiPrices: ApiPrice[] = pricesData.items || []

        // Group prices by mandi — get latest price and previous price for trend
        const pricesByMandi = new Map<number, ApiPrice[]>()
        for (const p of apiPrices) {
          if (!pricesByMandi.has(p.mandi_id)) {
            pricesByMandi.set(p.mandi_id, [])
          }
          pricesByMandi.get(p.mandi_id)!.push(p)
        }

        const userLat = userLocation?.lat || 28.6139
        const userLng = userLocation?.lng || 77.2090

        const enrichedMandis: Mandi[] = apiMandis.map((m) => {
          const mandiPrices = pricesByMandi.get(m.id) || []
          // Sort by date descending
          mandiPrices.sort((a, b) => b.price_date.localeCompare(a.price_date))

          const latestPrice = mandiPrices[0]?.modal_price || 0
          const prevPrice = mandiPrices[1]?.modal_price || latestPrice
          const trend = prevPrice > 0 ? ((latestPrice - prevPrice) / prevPrice) * 100 : 0
          const totalArrival = mandiPrices[0]?.arrival_qty || 0
          const distance = calculateDistance(userLat, userLng, m.latitude, m.longitude)

          return {
            id: m.id,
            name: m.name,
            district: m.district,
            state: m.state,
            price: Math.round(latestPrice),
            trend: Math.round(trend * 10) / 10,
            distance,
            arrival: totalArrival,
            latitude: m.latitude,
            longitude: m.longitude,
          }
        })

        setMandis(enrichedMandis)
        setError(null)
      } catch (err) {
        console.error("Error fetching mandi data:", err)
        setError(err instanceof Error ? err.message : "Failed to load mandi data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [userLocation])

  const filteredAndSortedMandis = mandis
    .filter((mandi) => {
      const matchesSearch = mandi.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mandi.district.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mandi.state.toLowerCase().includes(searchTerm.toLowerCase())
      if (sortBy === "nearby") return matchesSearch && mandi.distance <= 200
      return matchesSearch
    })
    .sort((a, b) => {
      if (sortBy === "price") return b.price - a.price
      if (sortBy === "distance" || sortBy === "nearby") return a.distance - b.distance
      return b.arrival - a.arrival
    })

  const calculatePotentialEarning = (price: number, distance: number) => {
    const transportCost = distance * 2 // ₹2 per km
    const netPrice = price - transportCost
    return { transportCost, netPrice }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-6 p-4 pb-28 md:p-8 md:pb-16">
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-5 w-64" />
          <Skeleton className="h-10 w-full rounded-md" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-24 rounded-md" />
            <Skeleton className="h-9 w-24 rounded-md" />
            <Skeleton className="h-9 w-24 rounded-md" />
          </div>
        </div>
        <Skeleton className="h-[400px] w-full rounded-lg" />
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-destructive font-medium">{error}</p>
        <Button onClick={() => window.location.reload()}>{t("mandi.retry")}</Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 p-4 pb-28 md:p-8 md:pb-16">
      <header className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("mandi.title")}</h1>
          <p className="text-muted-foreground">{t("mandi.subtitle")} {mandis.length} {t("mandi.mandis")}</p>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder={t("mandi.searchPlaceholder")}
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Sort Buttons */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <Button
            variant={sortBy === "nearby" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("nearby")}
          >
            <MapPin className="mr-2 h-4 w-4" />
            Nearby (&lt;200km)
          </Button>
          <Button
            variant={sortBy === "price" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("price")}
          >
            <TrendingUp className="mr-2 h-4 w-4" />
            {t("mandi.bestPrice")}
          </Button>
          <Button
            variant={sortBy === "distance" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("distance")}
          >
            <Navigation className="mr-2 h-4 w-4" />
            {t("mandi.nearest")}
          </Button>
          <Button
            variant={sortBy === "arrival" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("arrival")}
          >
            <Filter className="mr-2 h-4 w-4" />
            {t("mandi.highDemand")}
          </Button>
        </div>
      </header>

      {/* Map Section */}
      <section>
        <MandiMap />
      </section>

      {/* Mandi List */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">
          {filteredAndSortedMandis.length} {t("mandi.mandisFound")}
        </h2>

        <div className="grid gap-4">
          {filteredAndSortedMandis.map((mandi) => {
            const { transportCost, netPrice } = calculatePotentialEarning(mandi.price, mandi.distance)
            const isBestPrice = sortBy === "price" && mandi === filteredAndSortedMandis[0]

            return (
              <Card
                key={mandi.id}
                className={`transition-all hover:shadow-md ${isBestPrice ? "border-primary ring-2 ring-primary/20" : ""}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                        <MapPin className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{mandi.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">
                          {mandi.district}, {mandi.state}
                        </p>
                      </div>
                    </div>
                    {isBestPrice && (
                      <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                        {t("mandi.bestPrice")}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">{t("mandi.price")}</p>
                      <p className="text-lg font-bold">₹{mandi.price.toLocaleString("en-IN")}<span className="text-sm font-normal text-muted-foreground">/Q</span></p>
                      <div className={`flex items-center text-xs ${mandi.trend >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {mandi.trend >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                        {mandi.trend > 0 ? "+" : ""}{mandi.trend}%
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t("mandi.distance")}</p>
                      <p className="text-lg font-bold">{mandi.distance} km</p>
                      <p className="text-xs text-muted-foreground">≈ ₹{transportCost} {t("mandi.transport")}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t("mandi.netEarning")}</p>
                      <p className="text-lg font-bold text-primary">₹{netPrice.toLocaleString("en-IN")}</p>
                      <p className="text-xs text-muted-foreground">{t("mandi.afterTransport")}</p>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{t("mandi.arrivalToday")}</span>
                      <span className="font-medium">{mandi.arrival.toLocaleString()} {t("mandi.quintals")}</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${Math.min((mandi.arrival / 500) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* Location Access Banner */}
      {!userLocation && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <MapPin className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">{t("mandi.enableLocation")}</p>
                <p className="text-sm text-muted-foreground">
                  {t("mandi.enableLocationDesc")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
