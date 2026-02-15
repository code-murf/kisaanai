"use client"

import { useEffect, useState } from "react"
import type { Map as LeafletMap } from "leaflet"
import "leaflet/dist/leaflet.css" 
import { MapContainer, Marker, Popup, TileLayer, Circle, useMap } from "react-leaflet"
import { useLocation } from "@/contexts/LocationContext"
import { Button } from "@/components/ui/button"
import { Locate } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const mandis = [
  { 
    id: 1, 
    name: "Azadpur Mandi", 
    lat: 28.7131, 
    lng: 77.1678, 
    price: 1240,
    image: "https://images.unsplash.com/photo-1605335198952-49141f4eb41f?q=80&w=800&auto=format&fit=crop" // Indian Market
  },
  { 
    id: 2, 
    name: "Okhla Mandi", 
    lat: 28.5398, 
    lng: 77.2721, 
    price: 1210,
    image: "https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=800&auto=format&fit=crop" // Vegetables
  },
  { 
    id: 3, 
    name: "Ghazipur Mandi", 
    lat: 28.6289, 
    lng: 77.3328, 
    price: 1260,
    image: "https://images.unsplash.com/photo-1573485868686-25442d00160d?q=80&w=800&auto=format&fit=crop" // Market Stall
  },
]

// Component to handle map centering
function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo(center, 13)
  }, [center, map])
  return null
}

export default function MandiMap() {
  const [isMounted, setIsMounted] = useState(false)
  const [icons, setIcons] = useState<any>(null)
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
        <div className="h-[600px] w-full relative z-0">
          <MapContainer
            center={center}
            zoom={11}
            scrollWheelZoom={false}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            <MapUpdater center={center} />

            {/* User Location */}
            {location && (
                <>
                    <Marker position={[location.lat, location.lon]} icon={icons.user}>
                        <Popup>
                            <div className="font-bold p-1">Your Location</div>
                        </Popup>
                    </Marker>
                    <Circle 
                        center={[location.lat, location.lon]} 
                        pathOptions={{ fillColor: '#3b82f6', fillOpacity: 0.1, color: '#3b82f6' }} 
                        radius={2000} 
                    />
                </>
            )}

            {/* Mandis */}
            {mandis.map((mandi) => (
              <Marker key={mandi.id} position={[mandi.lat, mandi.lng]} icon={icons.mandi}>
                <Popup className="mandi-popup">
                  <div className="w-[200px] flex flex-col gap-2">
                    <img 
                        src={mandi.image} 
                        alt={mandi.name}
                        className="w-full h-[120px] object-cover rounded-md shadow-sm"
                        style={{ display: "block" }}
                    />
                    <div>
                        <h3 className="font-bold text-lg leading-none">{mandi.name}</h3>
                        <p className="text-sm text-green-600 font-medium mt-1">
                            Price: ₹{mandi.price}/qt
                        </p>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </CardContent>
    </Card>
  )
}
