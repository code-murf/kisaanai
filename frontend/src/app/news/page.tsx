"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Bell, Loader2, AlertCircle, TrendingUp, Newspaper, CloudRain, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BentoGrid, BentoCard } from "@/components/magicui/bento-grid";

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

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/news`, { cache: 'no-store' });

        if (!response.ok) {
          throw new Error('Failed to fetch news');
        }
        const data = await response.json();
        setNews(data);
      } catch (err) {
        setError('Failed to load news. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  const getIcon = (category: string) => {
    switch(category) {
      case 'Market Trend': return TrendingUp;
      case 'Weather Alert': return CloudRain;
      case 'Policy': return FileText;
      default: return Newspaper;
    }
  };



  const getItemClassName = (idx: number) => {
    if (idx === 1) return "col-span-3 lg:col-span-2 row-span-2 rounded-none border-neutral-800";
    if (idx === 3) return "col-span-3 lg:col-span-3 rounded-none border-neutral-800";
    return "col-span-3 lg:col-span-1 rounded-none border-neutral-800";
  };

  return (
    <div className="min-h-screen bg-neutral-950 p-0 md:p-4 flex flex-col items-center">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[1600px] space-y-8"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 border-b border-neutral-800 pb-8 px-4 md:px-0">
          <div className="space-y-2 text-center md:text-left">
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-neutral-50">
              Newsroom
            </h1>
            <p className="text-lg text-neutral-400 max-w-xl">
              Curated insights, policy updates, and market intelligence.
            </p>
          </div>
          <Button variant="default" size="lg" className="rounded-full px-8 bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/20">
            <Bell className="mr-2 h-4 w-4" /> Subscribe
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-32">
            <Loader2 className="h-12 w-12 animate-spin text-emerald-600 opacity-50" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-600 bg-red-900/10 rounded-2xl border border-red-900/30">
            <AlertCircle className="h-10 w-10 mb-4 opacity-80" />
            <p className="text-lg font-medium">{error}</p>
            <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Retry</Button>
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
                        className="h-full w-full object-cover opacity-60 transition-transform duration-500 group-hover:scale-105"
                      />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/80 to-transparent" />
                  </div>
                }
                Icon={getIcon(item.category)}
                description={item.excerpt}
                href="#"
                cta="Read Full Story"
                iconClassName="h-8 w-8 text-white opacity-80"
              />
            ))}
          </BentoGrid>
        )}
      </motion.div>
    </div>
  );
}
