"use client";

import { useState } from "react";
import { UploadCloud, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export default function CropDoctor() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [image, setImage] = useState<string | null>(null);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result as string);
        setResult(null); // Reset result on new upload
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeImage = () => {
    if (!image) return;
    setAnalyzing(true);
    // Simulate AI analysis delay
    setTimeout(() => {
      setAnalyzing(false);
      setResult({
        disease: "Early Blight (Alternaria solani)",
        confidence: "92%",
        severity: "Moderate",
        treatment: [
          "Apply fungicide like Mancozeb or Chlorothalonil.",
          "Improve air circulation between plants.",
          "Avoid overhead watering to keep foliage dry."
        ]
      });
    }, 2500);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 flex flex-col items-center">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl space-y-8"
      >
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            🌿 Crop Doctor
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Upload a photo of your crop to detect diseases instantly using AI.
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 bg-slate-50/50 dark:bg-slate-900/50 hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer relative">
            
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            {!image ? (
              <div className="flex flex-col items-center gap-2 text-slate-500">
                <UploadCloud className="h-10 w-10 text-emerald-500" />
                <p className="font-medium">Click to upload or drag and drop</p>
                <p className="text-xs">Supports JPG, PNG (Max 5MB)</p>
              </div>
            ) : (
              <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-black">
                 {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={image} alt="Crop Preview" className="w-full h-full object-contain" />
                <div className="absolute top-2 right-2">
                   <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); setImage(null); setResult(null); }}>
                     Remove
                   </Button>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-center">
            <Button 
              size="lg" 
              onClick={analyzeImage} 
              disabled={!image || analyzing || result}
              className={cn("w-full md:w-auto min-w-[200px]", analyzing ? "bg-slate-400" : "bg-emerald-600 hover:bg-emerald-700 text-white")}
            >
              {analyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...
                </>
              ) : result ? (
                "Analysis Complete"
              ) : (
                "Diagnose Disease"
              )}
            </Button>
          </div>
        </div>

        {result && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-emerald-100 dark:border-emerald-900/30"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <div className="space-y-4 flex-1">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">Diagnosis: {result.disease}</h3>
                  <div className="flex gap-3 mt-2 text-sm">
                    <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium dark:bg-red-900/30 dark:text-red-400">
                      Severity: {result.severity}
                    </span>
                    <span className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium dark:bg-emerald-900/30 dark:text-emerald-400">
                      Confidence: {result.confidence}
                    </span>
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-4">
                  <h4 className="font-semibold text-slate-900 dark:text-slate-200 mb-2 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-500" /> Recommended Treatment
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300 text-sm">
                    {result.treatment.map((step: string, idx: number) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
