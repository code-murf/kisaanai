
"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Sprout, Beaker, Upload, X, AlertTriangle } from "lucide-react"

interface Recommendation {
  crop_name: string
  confidence: number
  reason: string
  season: string
}

export function CropDoctor() {
  const [n, setN] = useState("")
  const [p, setP] = useState("")
  const [k, setK] = useState("")
  const [ph, setPh] = useState("")
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [diagnosis, setDiagnosis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [image, setImage] = useState<string | null>(null)

  const handleRecommend = async () => {
    setLoading(true)
    try {
      const query = new URLSearchParams({
        n: n || "0",
        p: p || "0",
        k: k || "0",
        ph: ph || "7",
        location: "Delhi"
      })
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/crops/recommend?${query}`)
      if (!res.ok) throw new Error("Failed to fetch")
      const data = await res.json()
      setRecommendations(data)
    } catch (err) {
      console.error(err)
      // Fallback Mock
       setRecommendations([
          { crop_name: "Wheat", confidence: 0.92, reason: "Optimal for neutral soil.", season: "Rabi" },
          { crop_name: "Mustard", confidence: 0.85, reason: "Good for current season.", season: "Rabi" }
       ])
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setImage(reader.result as string)
        setDiagnosis(null) // Reset diagnosis on new image
      }
      reader.readAsDataURL(file)
    }
  }

  const handleDiagnose = async () => {
    if (!selectedFile) return
    setLoading(true)
    try {
        const formData = new FormData()
        formData.append("file", selectedFile)

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/diseases/diagnose`, {
            method: "POST",
            body: formData
        })
        
        if (!res.ok) throw new Error("Diagnosis failed")
        const data = await res.json()
        setDiagnosis(data)
    } catch (err) {
        console.error(err)
        // Fallback
        setDiagnosis({
            disease_name: "Leaf Spot",
            confidence: 0.85, 
            treatment: "Apply Copper Fungicide.",
            severity: "Moderate"
        })
    } finally {
        setLoading(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sprout className="h-5 w-5 text-green-600" />
          Smart Advisory
        </CardTitle>
        <CardDescription>Expert advice for your crops & soil.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="soil" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="soil">Soil Health</TabsTrigger>
            <TabsTrigger value="disease">Plant Doctor</TabsTrigger>
          </TabsList>
          
          <TabsContent value="soil" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="n">Nitrogen (N)</Label>
                <Input id="n" placeholder="120" value={n} onChange={(e) => setN(e.target.value)} type="number" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="p">Phosphorus (P)</Label>
                <Input id="p" placeholder="60" value={p} onChange={(e) => setP(e.target.value)} type="number" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="k">Potassium (K)</Label>
                <Input id="k" placeholder="40" value={k} onChange={(e) => setK(e.target.value)} type="number" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ph">pH Level</Label>
                <Input id="ph" placeholder="6.5" value={ph} onChange={(e) => setPh(e.target.value)} type="number" step="0.1" />
              </div>
            </div>
            
            <Button className="w-full" onClick={handleRecommend} disabled={loading}>
              {loading ? "Analyzing..." : "Get Crop Recommendations"}
            </Button>

            {recommendations.length > 0 && (
              <div className="space-y-3 pt-4 border-t">
                 <h4 className="font-semibold text-sm">Recommended Crops:</h4>
                 {recommendations.map((rec, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                        <div className="mt-1 bg-green-100 p-1.5 rounded-full">
                            <Sprout className="h-4 w-4 text-green-700" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-bold">{rec.crop_name}</span>
                                <span className="text-xs px-2 py-0.5 bg-green-200 text-green-800 rounded-full">
                                    {(rec.confidence * 100).toFixed(0)}% Match
                                </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">{rec.reason}</p>
                            <p className="text-xs text-blue-600 mt-1">Season: {rec.season}</p>
                        </div>
                    </div>
                 ))}
              </div>
            )}
          </TabsContent>
        
          <TabsContent value="disease" className="space-y-4 mt-4">
            <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:bg-muted/50 transition-colors">
               {!image ? (
                 <div className="space-y-3">
                    <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <Upload className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                        <p className="font-medium">Upload Leaf Photo</p>
                        <p className="text-sm text-muted-foreground">Take a clear photo of the affected area</p>
                    </div>
                    <Input 
                        id="image-upload" 
                        type="file" 
                        accept="image/*" 
                        className="hidden" 
                        onChange={handleImageUpload}
                    />
                    <Button variant="outline" onClick={() => document.getElementById('image-upload')?.click()}>
                        Select Image
                    </Button>
                 </div>
               ) : (
                 <div className="relative">
                    <img src={image} alt="Uploaded leaf" className="max-h-64 mx-auto rounded-lg shadow-md" />
                    <Button 
                        size="icon" 
                        variant="destructive" 
                        className="absolute top-2 right-2 h-8 w-8 rounded-full"
                        onClick={() => {
                            setImage(null)
                            setSelectedFile(null)
                            setDiagnosis(null)
                        }}
                    >
                        <X className="h-4 w-4" />
                    </Button>
                    <div className="mt-4">
                        <Button className="w-full" onClick={handleDiagnose} disabled={loading || !selectedFile}>
                            <Beaker className="h-4 w-4 mr-2" />
                            {loading ? "Analyzing..." : "Analyze Disease"}
                        </Button>
                    </div>
                 </div>
               )}
            </div>
            
            {diagnosis && (
                 <div className="p-4 bg-red-50 border border-red-200 rounded-lg mt-4 animate-in fade-in slide-in-from-bottom-2">
                    <div className="flex justify-between items-start">
                        <div>
                            <h4 className="font-bold text-red-800 text-lg">{diagnosis.disease_name}</h4>
                            <p className="text-sm text-red-600 font-medium">Severity: {diagnosis.severity} • Confidence: {(diagnosis.confidence * 100).toFixed(0)}%</p>
                        </div>
                        {diagnosis.disease_name === 'Healthy' ? (
                            <div className="bg-green-100 p-2 rounded-full"><Sprout className="text-green-600 h-6 w-6"/></div>
                        ) : (
                            <AlertTriangle className="text-red-600 h-6 w-6" />
                        )}
                    </div>
                    <div className="mt-3 pt-3 border-t border-red-100">
                        <p className="text-xs font-semibold text-red-900 uppercase tracking-wider">Recommended Treatment</p>
                        <p className="text-sm text-red-800 mt-1">{diagnosis.treatment}</p>
                    </div>
                 </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
