"use client"

import { useEffect, useState } from "react"
import "leaflet/dist/leaflet.css"
import { MapContainer, Marker, Popup, TileLayer, Circle, useMap } from "react-leaflet"
import { useLocation } from "@/contexts/LocationContext"
import { Button } from "@/components/ui/button"
import { Locate } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ApiMandi {
  id: number
  name: string
  district: string
  state: string
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

// Component to handle map centering
function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo(center, 8)
  }, [center, map])
  return null
}

export default function MandiMap() {
  const [isMounted, setIsMounted] = useState(false)
  const [icons, setIcons] = useState<any>(null)
  const [apiMandis, setApiMandis] = useState<ApiMandi[]>([])
  const { location, requestLocation, isLoading: isLocating, error: locError } = useLocation()

  useEffect(() => {
    setIsMounted(true)
    // Initialize icons dynamically on client side
    import("leaflet").then((L) => {
        const mandiIcon = L.icon({
            iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
            iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
            shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
        })

        const userIcon = L.icon({
            iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
            shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })

        setIcons({ mandi: mandiIcon, user: userIcon })
    })

    // Auto-request location on mount
    requestLocation()
  }, [requestLocation])

  // Fetch mandis from API
  useEffect(() => {
    async function fetchMandis() {
      try {
        const res = await fetch(`/api/v1/mandis?page_size=50`)
        if (res.ok) {
          const data = await res.json()
          const items: ApiMandi[] = (data.items || []).filter(
            (m: ApiMandi) => m.latitude && m.longitude
          )
          setApiMandis(items)
        }
      } catch {
        // Keep empty — fallback to no markers
      }
    }
    fetchMandis()
  }, [])

  if (!isMounted || !icons) {
    return (
      <Card className="col-span-4 lg:col-span-4 h-[600px] flex items-center justify-center">
        <p>Loading Map...</p>
      </Card>
    )
  }

  const center: [number, number] = location
    ? [location.lat, location.lon]
    : [28.6139, 77.209] // Default to Delhi

  return (
    <Card className="col-span-4 lg:col-span-4 shadow-sm border">
      <CardHeader className="flex flex-row items-center justify-between bg-muted/50">
        <div>
            <CardTitle className="text-xl">Nearby Mandis</CardTitle>
            <p className="text-sm text-muted-foreground">Live market prices and locations</p>
            {locError && (
              <p className="text-xs text-red-600 mt-1">{locError}</p>
            )}
        </div>
        <Button
            variant="default"
            size="sm"
            onClick={() => requestLocation()}
            disabled={isLocating}
            className="shadow-sm"
        >
            <Locate className="h-4 w-4 mr-2" />
            {isLocating ? "Locating..." : "Find Me"}
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[350px] md:h-[500px] w-full relative z-0">
          <MapContainer
            center={center}
            zoom={8}
            scrollWheelZoom={false}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapUpdater center={center} />

            {/* User Location with 200km radius */}
            {location && (
                <>
                    <Marker position={[location.lat, location.lon]} icon={icons.user}>
                        <Popup>
                            <div className="font-bold p-1">Your Location</div>
                        </Popup>
                    </Marker>
                    <Circle
                        center={[location.lat, location.lon]}
                        pathOptions={{ fillColor: '#3b82f6', fillOpacity: 0.08, color: '#3b82f6', weight: 1.5, dashArray: '8 4' }}
                        radius={200000}
                    />
                </>
            )}

            {/* API Mandis — nearby within 200km shown with distance */}
            {apiMandis.map((mandi) => {
              const dist = location ? calculateDistance(location.lat, location.lon, mandi.latitude, mandi.longitude) : 0
              const isNearby = !location || dist <= 200
              return (
                <Marker key={mandi.id} position={[mandi.latitude, mandi.longitude]} icon={icons.mandi}>
                  <Popup className="mandi-popup">
                    <div className="w-[200px] flex flex-col gap-2">
                      <div>
                          <h3 className="font-bold text-lg leading-none">{mandi.name}</h3>
                          <p className="text-xs text-gray-500 mt-1">
                              {mandi.district}, {mandi.state}
                          </p>
                          {location && (
                            <p className={`text-sm font-semibold mt-1 ${isNearby ? 'text-green-600' : 'text-orange-600'}`}>
                              {dist} km {isNearby ? '(Nearby)' : '(Far)'}
                            </p>
                          )}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              )
            })}
          </MapContainer>
        </div>
      </CardContent>
    </Card>
  )
}
