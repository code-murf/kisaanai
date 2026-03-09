"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, AlertCircle, TrendingUp, Newspaper, CloudRain, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BentoGrid, BentoCard } from "@/components/magicui/bento-grid";
import { useTranslation } from "@/hooks/useTranslation";

interface NewsItem {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  source: string;
  category: string;
  color: string;
  image_url: string;
  video_url: string | null;
}

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch(
          `/api/v1/news`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch news");
        }

        const data = await response.json();
        setNews(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load news");
        setNews([]);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  const getIcon = (category: string) => {
    switch (category) {
      case "Market Trend":
        return TrendingUp;
      case "Weather Alert":
        return CloudRain;
      case "Policy":
        return FileText;
      default:
        return Newspaper;
    }
  };

  const getItemClassName = (idx: number) => {
    if (idx === 1) return "col-span-3 lg:col-span-2 row-span-2 rounded-none border-neutral-800";
    if (idx === 3) return "col-span-3 lg:col-span-3 rounded-none border-neutral-800";
    return "col-span-3 lg:col-span-1 rounded-none border-neutral-800";
  };

  return (
    <div className="min-h-screen bg-neutral-950 p-0 pb-28 md:p-4 md:pb-16 flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[1600px] space-y-8"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 border-b border-neutral-800 pb-8 px-4 md:px-0">
          <div className="space-y-2 text-center md:text-left">
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-neutral-50">{t("news.title")}</h1>
            <p className="text-lg text-neutral-400 max-w-xl">
              {t("news.subtitle")}
            </p>
          </div>
          <Button
            variant="default"
            size="lg"
            className="rounded-full px-8 bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/20"
          >
            <Bell className="mr-2 h-4 w-4" /> {t("news.subscribe")}
          </Button>
        </div>

        {loading ? (
          <div className="grid grid-cols-3 gap-0 auto-rows-[22rem]">
            <Skeleton className="col-span-3 lg:col-span-1 h-full rounded-none bg-neutral-900" />
            <Skeleton className="col-span-3 lg:col-span-2 row-span-2 h-full rounded-none bg-neutral-900" />
            <Skeleton className="col-span-3 lg:col-span-1 h-full rounded-none bg-neutral-900" />
            <Skeleton className="col-span-3 lg:col-span-3 h-full rounded-none bg-neutral-900" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-600 bg-red-900/10 rounded-2xl border border-red-900/30">
            <AlertCircle className="h-10 w-10 mb-4 opacity-80" />
            <p className="text-lg font-medium">{error}</p>
            <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        ) : (
          <BentoGrid className="lg:grid-rows-2 auto-rows-[22rem] gap-0">
            {news.map((item, idx) => (
              <BentoCard
                key={item.id}
                name={item.title}
                className={getItemClassName(idx)}
                background={
                  <div className="absolute inset-0 h-full w-full">
                    {item.video_url ? (
                      <video
                        src={item.video_url}
                        autoPlay
                        muted
                        loop
                        playsInline
                        className="h-full w-full object-cover opacity-90 transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={item.image_url}
                        alt="Background"
                        className="h-full w-full object-cover object-center opacity-60 transition-transform duration-500 group-hover:scale-105"
                        onError={(e) => {
                          const target = e.currentTarget;
                          target.style.display = "none";
                          if (target.parentElement) {
                            target.parentElement.classList.add("bg-gradient-to-br", "from-neutral-800", "to-neutral-900");
                          }
                        }}
                      />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/80 to-transparent" />
                  </div>
                }
                Icon={getIcon(item.category)}
                description={item.excerpt}
                href="#"
                cta={t("news.readFullStory")}
                iconClassName="h-8 w-8 text-white opacity-80"
              />
            ))}
          </BentoGrid>
        )}
      </motion.div>
    </div>
  );
}
