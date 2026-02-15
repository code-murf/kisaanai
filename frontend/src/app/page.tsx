"use client"

import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowUpRight, TrendingUp, MapPin, Mic } from "lucide-react"
import { CommoditySelector } from "@/components/dashboard/CommoditySelector"
import { ForecastWidget } from "@/components/dashboard/ForecastWidget"
// import { VoiceAssistant } from "@/components/dashboard/VoiceAssistant" 
import { VoiceSidebar } from "@/components/dashboard/VoiceSidebar"
import { CommunityFeed } from "@/components/dashboard/CommunityFeed"
import { ResourceOptimizer } from "@/components/dashboard/ResourceOptimizer"
import { useState } from "react"
// Dynamically import MandiMap with SSR disabled because it uses Leaflet
const MandiMap = dynamic(
  () => import("@/components/dashboard/MandiMap"),
  { 
    loading: () => <div className="h-[600px] w-full flex items-center justify-center bg-muted animate-pulse rounded-md">Loading Map...</div>,
    ssr: false 
  }
)

const PriceChart = dynamic(
  () => import("@/components/dashboard/PriceChart").then((mod) => mod.PriceChart),
  {
    loading: () => <div className="h-[350px] w-full flex items-center justify-center bg-muted animate-pulse rounded-md">Loading Chart...</div>,
    ssr: false
  }
)

import { WeatherWidget } from "@/components/dashboard/WeatherWidget"
import { CropDoctor } from "@/components/dashboard/CropDoctor"

export default function Home() {
  const [selectedCommodityId, setSelectedCommodityId] = useState(2) // Default Potato

  return (
    <div className="flex flex-col min-h-screen bg-muted/40 pb-20 md:pb-0">
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/95 backdrop-blur-2xl px-6 shadow-xs">
         <div className="flex w-full items-center justify-between">
           <div className="flex items-center gap-2">
             <div className="h-6 w-6 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
                AB
             </div>
             <h1 className="text-lg font-semibold tracking-tight">KisaanAI</h1>
           </div>
           
           <div className="flex items-center gap-4">
              <span className="hidden md:inline-block text-sm text-muted-foreground mr-2">
                  Welcome, Ram Lal
              </span>
              <div className="flex items-center gap-2">
                <CommoditySelector onSelect={setSelectedCommodityId} />
                <Button size="icon" variant="outline" className="h-9 w-9 rounded-full shrink-0">
                    <Mic className="h-4 w-4" />
                    <span className="sr-only">Voice Assistant</span>
                </Button>
              </div>
           </div>
         </div>
      </header>

      <main className="flex-1 p-4 md:p-6 lg:p-8 grid gap-6 max-w-[1600px] mx-auto w-full">
        {/* Weather Widget Section */}
        <section>
          <WeatherWidget />
        </section>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Selected Crop</CardTitle>
              <TrendingUp className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Potato (Jyoti)</div>
              <p className="text-xs text-muted-foreground">
                Avg Market Price
              </p>
            </CardContent>
          </Card>
          <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Price</CardTitle>
              <ArrowUpRight className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
               <div className="text-2xl font-bold">₹1,240 / qt</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-emerald-500 font-medium">+2.5%</span> from yesterday
              </p>
            </CardContent>
          </Card>
           <Card className="shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Best Mandi</CardTitle>
              <MapPin className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Azadpur</div>
              <p className="text-xs text-muted-foreground">
                12 km away • High Demand
              </p>
            </CardContent>
          </Card>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-6">
          <div className="col-span-1 md:col-span-2 lg:col-span-4 space-y-6">
              <ForecastWidget commodityId={selectedCommodityId} />
              <PriceChart commodityId={selectedCommodityId} />
              <div className="grid md:grid-cols-2 gap-6">
                  <CropDoctor />
                  <ResourceOptimizer />
              </div>
          </div>
          <div className="col-span-1 md:col-span-2 lg:col-span-3 space-y-6">
               <Card className="flex flex-col shadow-xs">
                  <CardHeader className="pb-3">
                      <CardTitle>Recent Alerts</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-1">
                      <div className="flex items-start gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-border/50">
                          <div className="h-2 w-2 mt-2 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
                          <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">
                              Heavy Rain Alert
                          </p>
                          <p className="text-xs text-muted-foreground">
                              Expected in 2 days. Harvest soon.
                          </p>
                          </div>
                      </div>
                      <div className="flex items-start gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-border/50">
                          <div className="h-2 w-2 mt-2 rounded-full bg-emerald-500 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                          <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">
                              Market Up-trend
                          </p>
                          <p className="text-xs text-muted-foreground">
                              Onion prices rising in neighboring districts.
                          </p>
                          </div>
                      </div>
                  </CardContent>
              </Card>
              <div className="h-[500px]">
                  <CommunityFeed />
              </div>
          </div>
        </div>
        
        <section>
          <MandiMap />
        </section>
        
        <VoiceSidebar />
      </main>
    </div>
  )
}
