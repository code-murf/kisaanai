"use client"

import { useState, useEffect } from "react"
import { MapPin, Navigation, TrendingUp, TrendingDown, Search, Filter } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import dynamic from "next/dynamic"

const MandiMap = dynamic(
  () => import("@/components/dashboard/MandiMap"),
  {
    loading: () => <div className="h-[400px] w-full flex items-center justify-center bg-muted animate-pulse rounded-md">Loading Map...</div>,
    ssr: false
  }
)

interface Mandi {
  id: number
  name: string
  district: string
  state: string
  price: number
  trend: number
  distance: number
  arrival: number
}

const mandisData: Mandi[] = [
  { id: 1, name: "Azadpur Mandi", district: "Delhi", state: "DL", price: 1240, trend: 2.5, distance: 12, arrival: 4500 },
  { id: 2, name: "Okhla Mandi", district: "Delhi", state: "DL", price: 1210, trend: -1.2, distance: 15, arrival: 3200 },
  { id: 3, name: "Ghazipur Mandi", district: "Delhi", state: "DL", price: 1260, trend: 3.8, distance: 18, arrival: 2800 },
  { id: 4, name: "Keshopur Mandi", district: "Delhi", state: "DL", price: 1230, trend: 0.5, distance: 22, arrival: 1900 },
  { id: 5, name: "Narela Mandi", district: "Delhi", state: "DL", price: 1195, trend: -2.1, distance: 35, arrival: 2400 },
  { id: 6, name: "Bahadurgarh Mandi", district: "Jhajjar", state: "HR", price: 1250, trend: 4.2, distance: 28, arrival: 1600 },
]

export default function MandiPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"price" | "distance" | "arrival">("price")
  const [selectedMandi, setSelectedMandi] = useState<Mandi | null>(null)
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)

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
          console.log("Location access denied")
        }
      )
    }
  }, [])

  const filteredAndSortedMandis = mandisData
    .filter((mandi) =>
      mandi.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      mandi.district.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === "price") return b.price - a.price
      if (sortBy === "distance") return a.distance - b.distance
      return b.arrival - a.arrival
    })

  const calculatePotentialEarning = (price: number, distance: number) => {
    const transportCost = distance * 2 // ₹2 per km
    const netPrice = price - transportCost
    return { transportCost, netPrice }
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-20">
      <header className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Nearby Mandis</h1>
          <p className="text-muted-foreground">Find the best market to sell your produce</p>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search mandis by name or location..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Sort Buttons */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <Button
            variant={sortBy === "price" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("price")}
          >
            <TrendingUp className="mr-2 h-4 w-4" />
            Best Price
          </Button>
          <Button
            variant={sortBy === "distance" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("distance")}
          >
            <Navigation className="mr-2 h-4 w-4" />
            Nearest
          </Button>
          <Button
            variant={sortBy === "arrival" ? "default" : "outline"}
            size="sm"
            onClick={() => setSortBy("arrival")}
          >
            <Filter className="mr-2 h-4 w-4" />
            High Demand
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
          {filteredAndSortedMandis.length} Mandis found
        </h2>

        <div className="grid gap-4">
          {filteredAndSortedMandis.map((mandi) => {
            const { transportCost, netPrice } = calculatePotentialEarning(mandi.price, mandi.distance)
            const isBestPrice = sortBy === "price" && mandi === filteredAndSortedMandis[0]

            return (
              <Card
                key={mandi.id}
                className={`transition-all hover:shadow-md ${isBestPrice ? "border-primary ring-2 ring-primary/20" : ""}`}
                onClick={() => setSelectedMandi(mandi)}
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
                        Best Price
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Price</p>
                      <p className="text-lg font-bold">₹{mandi.price}<span className="text-sm font-normal text-muted-foreground">/Q</span></p>
                      <div className={`flex items-center text-xs ${mandi.trend >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {mandi.trend >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                        {mandi.trend > 0 ? "+" : ""}{mandi.trend}%
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Distance</p>
                      <p className="text-lg font-bold">{mandi.distance} km</p>
                      <p className="text-xs text-muted-foreground">≈ ₹{transportCost} transport</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Net Earning</p>
                      <p className="text-lg font-bold text-primary">₹{netPrice}</p>
                      <p className="text-xs text-muted-foreground">after transport</p>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Arrival today</span>
                      <span className="font-medium">{mandi.arrival.toLocaleString()} quintals</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${Math.min((mandi.arrival / 5000) * 100, 100)}%` }}
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
                <p className="font-medium">Enable location access</p>
                <p className="text-sm text-muted-foreground">
                  Allow location access to see mandis sorted by distance from your current location.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
