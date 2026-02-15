"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Droplets, Sprout, Leaf, ArrowRight } from "lucide-react";

interface OptimizationResult {
  water_liters: number;
  fertilizer_recommendation: string;
  crop_health_status: string;
  next_action: string;
}

export function ResourceOptimizer() {
  const [crop, setCrop] = useState("Potato");
  const [soil, setSoil] = useState("Loamy");
  const [days, setDays] = useState([45]);
  const [lastWatered, setLastWatered] = useState(3);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      // API call to backend
      const query = new URLSearchParams({
        crop,
        soil,
        days_sowing: days[0].toString(),
        last_watered_days: lastWatered.toString(),
        acres: "1.0"
      });
      
      const res = await fetch(`/api/v1/resources/optimize?${query}`);
      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error("Failed to optimize:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full bg-linear-to-br from-background to-blue-50/10 dark:to-blue-950/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Droplets className="h-5 w-5 text-blue-500" />
          Resource Optimizer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Crop</label>
            <Select value={crop} onValueChange={setCrop}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Potato">Potato</SelectItem>
                <SelectItem value="Wheat">Wheat</SelectItem>
                <SelectItem value="Rice">Rice</SelectItem>
                <SelectItem value="Onion">Onion</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Soil Data</label>
            <Select value={soil} onValueChange={setSoil}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Loamy">Loamy</SelectItem>
                <SelectItem value="Clay">Clay</SelectItem>
                <SelectItem value="Sandy">Sandy</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-4">
           <div className="flex justify-between">
              <label className="text-sm font-medium">Crop Age (Days)</label>
              <span className="text-sm text-muted-foreground">{days[0]} days</span>
           </div>
           <Slider value={days} onValueChange={setDays} min={10} max={120} step={1} className="py-2" />
        </div>

        <div className="space-y-2">
            <label className="text-sm font-medium">Last Watered (Days ago)</label>
            <div className="flex gap-2">
                {[1, 2, 3, 5, 7].map((d) => (
                    <Button 
                        key={d} 
                        variant={lastWatered === d ? "default" : "outline"} 
                        size="sm"
                        onClick={() => setLastWatered(d)}
                        className="flex-1"
                    >
                        {d}d
                    </Button>
                ))}
            </div>
        </div>

        <Button onClick={handleOptimize} className="w-full bg-blue-600 hover:bg-blue-700" disabled={loading}>
            {loading ? "Calculating..." : "Generate Advisory"}
            <ArrowRight className="h-4 w-4 ml-2" />
        </Button>

        {result && (
            <div className="p-4 rounded-lg bg-muted/50 border border-border mt-4 space-y-3 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Water Need</span>
                    <span className="text-lg font-bold text-blue-600 dark:text-blue-400">{result.water_liters} L/acre</span>
                </div>
                 <div className="flex items-start gap-2">
                    <Sprout className="h-4 w-4 text-green-500 mt-1 shrink-0" />
                    <p className="text-sm">{result.fertilizer_recommendation}</p>
                 </div>
                 <div className="flex items-center gap-2 pt-2 border-t border-border/50">
                    <Leaf className="h-4 w-4 text-emerald-500" />
                    <span className="text-sm font-medium">Status: {result.crop_health_status}</span>
                 </div>
            </div>
        )}
      </CardContent>
    </Card>
  );
}
