"use client";

import { useState } from "react";
import { UploadCloud, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/useTranslation";

interface DiagnosisResult {
  disease_name: string;
  confidence: number;
  severity: string;
  treatment: string;
  image_url?: string;
  storage_mode?: string;
}

export default function CropDoctor() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [image, setImage] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setError(null);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result as string);
        setResult(null);
      };
      reader.readAsDataURL(f);
    }
  };

  const analyzeImage = async () => {
    if (!file) return;
    setAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/v1/diseases/diagnose", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `Diagnosis failed (${res.status})`);
      }

      const data: DiagnosisResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to diagnose. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const treatmentSteps = result?.treatment
    ? result.treatment.split(/[.;]\s*/).filter((s) => s.trim().length > 0)
    : [];

  const isHealthy = result?.disease_name === "Healthy";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.16),_transparent_38%),linear-gradient(180deg,_#f8fafc_0%,_#eefbf3_100%)] dark:bg-slate-950 p-4 pb-28 md:p-8 md:pb-16 flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-5xl space-y-8"
      >
        <div className="text-center space-y-3">
          <div className="inline-flex items-center rounded-full border border-emerald-200 bg-white/80 px-4 py-1 text-sm font-medium text-emerald-700 shadow-sm">
            Verified plant disease diagnosis
          </div>
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            {t("doctor.title")}
          </h1>
          <p className="mx-auto max-w-2xl text-slate-600 dark:text-slate-400">
            {t("doctor.subtitle")}
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="bg-white/90 dark:bg-slate-900 rounded-3xl p-6 shadow-lg border border-emerald-100 dark:border-slate-800 backdrop-blur">
            <div className="mb-5 flex flex-wrap items-center gap-3 text-sm">
              <span className="rounded-full bg-emerald-100 px-3 py-1 font-medium text-emerald-700">Real image upload</span>
              <span className="rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">AI diagnosis + treatment</span>
              <span className="rounded-full bg-amber-100 px-3 py-1 font-medium text-amber-700">Local fallback if S3 fails</span>
            </div>

            <div className="flex flex-col items-center justify-center border-2 border-dashed border-emerald-200 dark:border-slate-700 rounded-2xl p-6 md:p-8 bg-emerald-50/60 dark:bg-slate-900/60 hover:bg-emerald-50 transition-colors cursor-pointer relative min-h-[340px]">
              <input
                type="file"
                accept="image/*"
                onChange={handleUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              {!image ? (
                <div className="flex flex-col items-center gap-3 text-slate-500 text-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-white shadow-sm">
                    <UploadCloud className="h-10 w-10 text-emerald-500" />
                  </div>
                  <p className="text-lg font-semibold text-slate-800">{t("doctor.upload")}</p>
                  <p className="text-sm">{t("doctor.uploadHint")}</p>
                </div>
              ) : (
                <div className="relative w-full">
                  <div className="overflow-hidden rounded-2xl border border-slate-200 bg-black shadow-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={image} alt="Crop Preview" className="h-[320px] w-full object-contain" />
                  </div>
                  <div className="absolute right-3 top-3">
                    <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); setImage(null); setFile(null); setResult(null); setError(null); }}>
                      {t("doctor.remove")}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex flex-col items-center gap-3">
              <Button
                size="lg"
                onClick={analyzeImage}
                disabled={!file || analyzing}
                className={cn("w-full md:w-auto min-w-[240px] rounded-full px-8", analyzing ? "bg-slate-400" : "bg-emerald-600 hover:bg-emerald-700 text-white")}
              >
                {analyzing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> {t("doctor.analyzing")}
                  </>
                ) : (
                  t("doctor.diagnoseDisease")
                )}
              </Button>
              <p className="text-center text-xs text-slate-500">
                Upload a clear leaf or crop image to get disease name, severity, confidence, and treatment steps.
              </p>
            </div>

            {error && (
              <p className="mt-4 text-sm text-red-600 text-center">{error}</p>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">What you get</h2>
              <div className="mt-4 grid gap-3 text-sm text-slate-600 dark:text-slate-300">
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                  Disease name with confidence score from the model
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                  Severity marker to quickly prioritize action
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60">
                  Recommended treatment steps for the farmer
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-emerald-100 bg-emerald-50/80 p-6 shadow-sm dark:border-emerald-900/30 dark:bg-emerald-950/20">
              <h2 className="text-lg font-semibold text-emerald-900 dark:text-emerald-100">Reliability</h2>
              <p className="mt-2 text-sm text-emerald-800 dark:text-emerald-200">
                If S3 storage is unavailable, KisaanAI now stores the uploaded image locally and still returns the diagnosis result.
              </p>
            </div>
          </div>
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-lg border border-emerald-100 dark:border-emerald-900/30"
          >
            <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="space-y-4">
                <div className={cn("inline-flex items-center rounded-full px-3 py-1 text-sm font-medium", isHealthy ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700")}>
                  {isHealthy ? "Healthy crop" : "Disease detected"}
                </div>
                {image && (
                  <div className="overflow-hidden rounded-2xl border border-slate-200 bg-black">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={image} alt="Analyzed crop" className="h-[260px] w-full object-contain" />
                  </div>
                )}
                {result.image_url && (
                  <a
                    href={result.image_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800"
                  >
                    View stored image
                  </a>
                )}
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className={cn("p-3 rounded-full", isHealthy ? "bg-emerald-100 dark:bg-emerald-900/30" : "bg-red-100 dark:bg-red-900/30")}>
                    {isHealthy ? (
                      <CheckCircle className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                  <div className="space-y-4 flex-1">
                    <div>
                      <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-50">{result.disease_name}</h3>
                      <div className="mt-3 flex flex-wrap gap-3 text-sm">
                        <span className={cn("px-3 py-1 rounded-full font-medium", isHealthy ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300" : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400")}>
                          {t("doctor.severity")}: {result.severity}
                        </span>
                        <span className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full font-medium dark:bg-emerald-900/30 dark:text-emerald-400">
                          {t("doctor.confidence")}: {(result.confidence * 100).toFixed(0)}%
                        </span>
                        {result.storage_mode && (
                          <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full font-medium dark:bg-slate-800 dark:text-slate-300">
                            Stored via {result.storage_mode}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-4">
                      <h4 className="font-semibold text-slate-900 dark:text-slate-200 mb-2 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-emerald-500" /> {t("doctor.recommendedTreatment")}
                      </h4>
                      {treatmentSteps.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300 text-sm">
                          {treatmentSteps.map((step, idx) => (
                            <li key={idx}>{step}.</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-slate-700 dark:text-slate-300 text-sm">{result.treatment}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
