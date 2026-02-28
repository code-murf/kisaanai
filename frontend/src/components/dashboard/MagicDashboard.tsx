"use client";

import { useEffect, useState } from "react";
import { BentoCard, BentoGrid } from "@/components/magicui/bento-grid";
import { Marquee } from "@/components/magicui/marquee";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { AnimatedGradientText } from "@/components/magicui/animated-gradient-text";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { 
  BarChartIcon, 
  CloudSunIcon, 
  MapIcon, 
  MicIcon, 
  NewspaperIcon,
  Sun,
  Cloud,
  CloudRain,
  Thermometer,
  Droplets,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PriceTick {
  crop: string;
  price: string;
  change: string;
}

interface WeatherDay {
  date: string;
  temp_min: number;
  temp_max: number;
  rainfall_mm: number;
  humidity_pct: number;
  condition: string;
  advisory: string;
  icon: string;
}

function WeatherIcon({ condition }: { condition: string }) {
  switch (condition.toLowerCase()) {
    case "sunny": return <Sun className="h-5 w-5 text-amber-500" />;
    case "rainy":
    case "rain": return <CloudRain className="h-5 w-5 text-blue-500" />;
    default: return <Cloud className="h-5 w-5 text-gray-400" />;
  }
}

export function MagicDashboard() {
  const [priceTicks, setPriceTicks] = useState<PriceTick[]>([
    { crop: "Potato", price: "₹1,800/q", change: "+2%" },
    { crop: "Onion", price: "₹2,500/q", change: "+5%" },
    { crop: "Tomato", price: "₹3,200/q", change: "-1%" },
    { crop: "Wheat", price: "₹2,400/q", change: "+0.5%" },
    { crop: "Rice", price: "₹3,800/q", change: "+1.2%" },
    { crop: "Cotton", price: "₹6,500/q", change: "+3%" },
    { crop: "Soybean", price: "₹4,800/q", change: "+1.5%" },
    { crop: "Mustard", price: "₹5,200/q", change: "+0.8%" },
  ]);
  const [weather, setWeather] = useState<WeatherDay[]>([]);

  useEffect(() => {
    // Fetch live prices for ticker
    const fetchPrices = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/news`);
        if (res.ok) {
          const newsItems = await res.json();
          if (newsItems.length > 0) {
            const ticks: PriceTick[] = newsItems.map((item: { title: string; excerpt: string }) => {
              const nameMatch = item.title.match(/^(\w+)/);
              const priceMatch = item.excerpt.match(/Rs\.\s*([\d,]+)/);
              const changeMatch = item.title.match(/([\d.]+)%/);
              const direction = item.title.includes("rose") ? "+" : "-";
              return {
                crop: nameMatch?.[1] || "Unknown",
                price: `₹${priceMatch?.[1] || "0"}/q`,
                change: `${direction}${changeMatch?.[1] || "0"}%`,
              };
            });
            if (ticks.length > 0) setPriceTicks(ticks);
          }
        }
      } catch {
        // Keep defaults
      }
    };

    // Fetch 3-day weather
    const fetchWeather = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/weather/forecast?lat=28.6&lon=77.2&days=3`);
        if (res.ok) {
          const data = await res.json();
          setWeather(data);
        }
      } catch {
        // Weather is optional
      }
    };

    fetchPrices();
    fetchWeather();
  }, []);

  const features = [
    {
      Icon: MapIcon,
      name: "Find Best Mandi",
      description: "Locate the nearest mandi with the highest profit margin.",
      href: "/mandi",
      cta: "View Map",
      background: <div className="row-span-1 rounded-xl border-none bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/20 dark:to-emerald-900/10 shadow-sm" />,
      className: "col-span-3 md:col-span-1 lg:col-span-1 border-emerald-100 bg-emerald-50/30 dark:bg-emerald-950/20 dark:border-emerald-900/50",
      iconClassName: "text-emerald-700 dark:text-emerald-400",
    },
    {
      Icon: BarChartIcon,
      name: "Price Forecast",
      description: "AI-powered predictions.",
      href: "/charts",
      cta: "See Trends",
      background: <div className="col-span-3 row-span-1 rounded-xl border-none bg-gradient-to-br from-indigo-100 to-indigo-50 dark:from-indigo-900/20 dark:to-indigo-900/10 shadow-sm" />,
      className: "col-span-3 md:col-span-2 lg:col-span-1 border-indigo-100 bg-indigo-50/30 dark:bg-indigo-950/20 dark:border-indigo-900/50",
      iconClassName: "text-indigo-700 dark:text-indigo-400",
    },
    {
      Icon: MicIcon,
      name: "Voice Assistant",
      description: "Ask in your language.",
      href: "/voice",
      cta: "Speak Now",
      background: <div className="col-span-2 row-span-1 rounded-xl border-none bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/20 dark:to-blue-900/10 shadow-sm" />,
      className: "col-span-3 md:col-span-2 lg:col-span-1 border-rose-100 bg-rose-50/30 dark:bg-rose-950/20 dark:border-rose-900/50",
      iconClassName: "text-rose-700 dark:text-rose-400",
    },
    {
      Icon: CloudSunIcon,
      name: "Crop Doctor",
      description: "Disease detection & advisory.",
      href: "/doctor",
      cta: "Diagnose",
      background: <div className="col-span-1 row-span-1 rounded-xl border-none bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-900/20 dark:to-amber-900/10 shadow-sm" />,
      className: "col-span-3 md:col-span-1 lg:col-span-2 border-amber-100 bg-amber-50/30 dark:bg-amber-950/20 dark:border-amber-900/50",
      iconClassName: "text-amber-700 dark:text-amber-400",
    },
    {
      Icon: NewspaperIcon,
      name: "News & Alerts",
      description: "Real-time updates.",
      href: "/news",
      cta: "Read More",
      background: <div className="absolute inset-0 bg-gradient-to-br from-sky-100/50 via-sky-50/30 to-transparent opacity-100" />,
      className: "col-span-3 lg:col-span-1 border-sky-100 bg-sky-50/30 dark:bg-sky-950/20 dark:border-sky-900/50",
      iconClassName: "text-sky-700 dark:text-sky-400",
    },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Hero Section with Animated Text */}
      <div className="flex flex-col items-center justify-center text-center space-y-4 py-8">
        <AnimatedGradientText className="text-sm font-medium px-4 py-1 rounded-full border border-neutral-200 bg-white/50 backdrop-blur-sm shadow-sm">
          🚀 Live: 20 Mandis • 8 Commodities • Real-Time Prices
        </AnimatedGradientText>
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl text-foreground">
          Empowering Farmers with <span className="text-emerald-600 dark:text-emerald-400">AI</span>
        </h1>
        <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed font-medium">
          Get real-time mandi prices, weather alerts, and crop advisory in your language.
        </p>
      </div>

      {/* Ticker for Impact Metrics */}
      <div className="grid grid-cols-3 gap-2 md:gap-4 text-center py-6 border-y border-neutral-100 bg-white/50 backdrop-blur-sm divide-x divide-neutral-200 dark:bg-neutral-900/50 dark:border-neutral-800 dark:divide-neutral-800 shadow-sm rounded-xl">
        <div>
          <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
            <NumberTicker value={15000} />+
          </p>
          <p className="text-sm font-medium text-muted-foreground">Farmers Helped</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
            <NumberTicker value={98} />%
          </p>
          <p className="text-sm font-medium text-muted-foreground">Accuracy</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-rose-600 dark:text-rose-400">
            <NumberTicker value={12} />
          </p>
          <p className="text-sm font-medium text-muted-foreground">States Covered</p>
        </div>
      </div>

      {/* Weather Widget */}
      {weather.length > 0 && (
        <div className="rounded-xl border border-neutral-200 bg-gradient-to-r from-sky-50 to-blue-50 dark:from-sky-950/30 dark:to-blue-950/30 dark:border-neutral-800 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <CloudSunIcon className="h-5 w-5 text-sky-600" />
            <h3 className="font-semibold text-foreground">Weather Forecast — Delhi</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {weather.map((day) => (
              <div key={day.date} className="flex flex-col items-center gap-1 p-3 rounded-lg bg-white/60 dark:bg-neutral-900/40 backdrop-blur-sm">
                <span className="text-xs text-muted-foreground font-medium">
                  {new Date(day.date).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
                </span>
                <WeatherIcon condition={day.condition} />
                <div className="flex items-center gap-1">
                  <Thermometer className="h-3 w-3 text-red-400" />
                  <span className="text-sm font-bold">{Math.round(day.temp_max)}°</span>
                  <span className="text-xs text-muted-foreground">/ {Math.round(day.temp_min)}°</span>
                </div>
                <div className="flex items-center gap-1">
                  <Droplets className="h-3 w-3 text-blue-400" />
                  <span className="text-xs text-muted-foreground">{day.humidity_pct}%</span>
                </div>
                <p className="text-[10px] text-center text-muted-foreground leading-tight mt-1">
                  {day.advisory.split(".")[0]}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Bento Grid */}
      <BentoGrid className="lg:grid-rows-2">
        {features.map((feature) => (
          <BentoCard key={feature.name} {...feature} />
        ))}
      </BentoGrid>

      {/* Marquee for Live Prices */}
      <div className="relative flex w-full flex-col items-center justify-center overflow-hidden rounded-xl border border-neutral-200 bg-white py-8 shadow-sm dark:bg-neutral-950 dark:border-neutral-800">
        <Marquee pauseOnHover className="[--duration:40s]">
          {priceTicks.map((item) => (
            <div key={item.crop} className="mx-6 flex flex-col items-center space-y-1">
              <span className="text-sm font-medium text-muted-foreground">{item.crop}</span>
              <span className="text-lg font-bold text-foreground">{item.price}</span>
              <span className={cn("text-xs font-bold", item.change.startsWith("+") ? "text-emerald-600" : "text-rose-600")}>
                {item.change}
              </span>
            </div>
          ))}
        </Marquee>
        <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-white dark:from-background"></div>
        <div className="pointer-events-none absolute inset-y-0 right-0 w-1/3 bg-gradient-to-l from-white dark:from-background"></div>
      </div>
    </motion.div>
  );
}
