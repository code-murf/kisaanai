"use client";

import { useEffect, useState } from "react";
import { BentoCard, BentoGrid } from "@/components/magicui/bento-grid";
import { Marquee } from "@/components/magicui/marquee";
import { AnimatedGradientText } from "@/components/magicui/animated-gradient-text";
import { DotPattern } from "@/components/ui/dot-pattern";
import { Meteors } from "@/components/ui/meteors";
import { ShineBorder } from "@/components/ui/shine-border";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useTranslation } from "@/hooks/useTranslation";
import { useLocation } from "@/contexts/LocationContext";
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
  UsersIcon,
} from "lucide-react";

const API_BASE_URL = "";

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

interface DashboardStats {
  totalMandis: number;
  totalCommodities: number;
  totalStates: number;
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
  const [priceTicks, setPriceTicks] = useState<PriceTick[]>([]);
  const [weather, setWeather] = useState<WeatherDay[]>([]);
  const [stats, setStats] = useState<DashboardStats>({ totalMandis: 0, totalCommodities: 0, totalStates: 0 });
  const { t, locale } = useTranslation();
  const { location } = useLocation();

  useEffect(() => {
    // Fetch real price data for ticker from gainers/losers
    const fetchPrices = async () => {
      try {
        const [gainersRes, losersRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/prices/gainers?period=7&limit=4`),
          fetch(`${API_BASE_URL}/api/v1/prices/losers?period=7&limit=4`),
        ]);
        const ticks: PriceTick[] = [];

        if (gainersRes.ok) {
          const gainers = await gainersRes.json();
          for (const g of gainers) {
            ticks.push({
              crop: t("entities." + String(g.commodity_name || g.name || "Unknown")),
              price: `₹${Math.round(Number(g.current_price || g.avg_price || 0)).toLocaleString("en-IN")}/q`,
              change: `+${Number(g.change_pct || 0).toFixed(1)}%`,
            });
          }
        }

        if (losersRes.ok) {
          const losers = await losersRes.json();
          for (const l of losers) {
            ticks.push({
              crop: t("entities." + String(l.commodity_name || l.name || "Unknown")),
              price: `₹${Math.round(Number(l.current_price || l.avg_price || 0)).toLocaleString("en-IN")}/q`,
              change: `${Number(l.change_pct || 0).toFixed(1)}%`,
            });
          }
        }

        if (ticks.length > 0) setPriceTicks(ticks);
      } catch {
        // Prices are optional — ticker stays empty
      }
    };

    // Fetch real stats from API
    const fetchStats = async () => {
      try {
        const [mandisRes, commoditiesRes, statesRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/mandis?page_size=1`),
          fetch(`${API_BASE_URL}/api/v1/commodities?page_size=1`),
          fetch(`${API_BASE_URL}/api/v1/mandis/states`),
        ]);

        let totalMandis = 0;
        let totalCommodities = 0;
        let totalStates = 0;

        if (mandisRes.ok) {
          const data = await mandisRes.json();
          totalMandis = data.total || (data.items || []).length || 0;
        }
        if (commoditiesRes.ok) {
          const data = await commoditiesRes.json();
          totalCommodities = data.total || (data.items || data || []).length || 0;
        }
        if (statesRes.ok) {
          const data = await statesRes.json();
          totalStates = Array.isArray(data) ? data.length : 0;
        }

        setStats({ totalMandis, totalCommodities, totalStates });
      } catch {
        // Stats are optional
      }
    };

    fetchPrices();
    fetchStats();
  }, [t]);

  // Fetch weather using real location or fallback to Delhi
  useEffect(() => {
    const fetchWeather = async () => {
      const lat = location?.lat ?? 28.6;
      const lon = location?.lon ?? 77.2;
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/weather/forecast?lat=${lat}&lon=${lon}&days=3`);
        if (res.ok) {
          const data = await res.json();
          setWeather(data);
        }
      } catch {
        // Weather is optional
      }
    };

    fetchWeather();
  }, [location]);

  const features = [
    {
      Icon: MapIcon,
      name: t("dashboard.findMandi"),
      description: t("dashboard.findMandiDesc"),
      href: "/mandi",
      cta: t("dashboard.viewMap"),
      background: <div className="row-span-1 rounded-xl border-none bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/20 dark:to-emerald-900/10 shadow-sm" />,
      className: "md:col-span-1 lg:col-span-1 border-emerald-100 bg-emerald-50/30 dark:bg-emerald-950/20 dark:border-emerald-900/50",
      iconClassName: "text-emerald-700 dark:text-emerald-400",
    },
    {
      Icon: BarChartIcon,
      name: t("dashboard.priceForecast"),
      description: t("dashboard.priceForecastDesc"),
      href: "/charts",
      cta: t("dashboard.seeTrends"),
      background: <div className="col-span-3 row-span-1 rounded-xl border-none bg-gradient-to-br from-indigo-100 to-indigo-50 dark:from-indigo-900/20 dark:to-indigo-900/10 shadow-sm" />,
      className: "md:col-span-2 lg:col-span-1 border-indigo-100 bg-indigo-50/30 dark:bg-indigo-950/20 dark:border-indigo-900/50",
      iconClassName: "text-indigo-700 dark:text-indigo-400",
    },
    {
      Icon: MicIcon,
      name: t("dashboard.voiceAssistant"),
      description: t("dashboard.voiceAssistantDesc"),
      href: "/voice",
      cta: t("dashboard.speakNow"),
      background: <div className="col-span-2 row-span-1 rounded-xl border-none bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/20 dark:to-blue-900/10 shadow-sm" />,
      className: "md:col-span-2 lg:col-span-1 border-rose-100 bg-rose-50/30 dark:bg-rose-950/20 dark:border-rose-900/50",
      iconClassName: "text-rose-700 dark:text-rose-400",
    },
    {
      Icon: CloudSunIcon,
      name: t("dashboard.cropDoctor"),
      description: t("dashboard.cropDoctorDesc"),
      href: "/doctor",
      cta: t("dashboard.diagnose"),
      background: <div className="col-span-1 row-span-1 rounded-xl border-none bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-900/20 dark:to-amber-900/10 shadow-sm" />,
      className: "md:col-span-1 lg:col-span-2 border-amber-100 bg-amber-50/30 dark:bg-amber-950/20 dark:border-amber-900/50",
      iconClassName: "text-amber-700 dark:text-amber-400",
    },
    {
      Icon: NewspaperIcon,
      name: t("dashboard.newsAlerts"),
      description: t("dashboard.newsAlertsDesc"),
      href: "/news",
      cta: t("dashboard.readMore"),
      background: <div className="absolute inset-0 bg-gradient-to-br from-sky-100/50 via-sky-50/30 to-transparent opacity-100" />,
      className: "md:col-span-1 lg:col-span-1 border-sky-100 bg-sky-50/30 dark:bg-sky-950/20 dark:border-sky-900/50",
      iconClassName: "text-sky-700 dark:text-sky-400",
    },
    {
      Icon: UsersIcon,
      name: "Community",
      description: "Listen to voice notes and advice from farmers in your area.",
      href: "/community",
      cta: "Join Discussion",
      background: <div className="absolute inset-0 bg-gradient-to-br from-purple-100/50 via-purple-50/30 to-transparent opacity-100" />,
      className: "md:col-span-3 lg:col-span-3 !h-[8rem] md:!h-[10rem] border-purple-100 bg-purple-50/30 dark:bg-purple-950/20 dark:border-purple-900/50",
      iconClassName: "text-purple-700 dark:text-purple-400",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Hero Section with Animated Background */}
      <div className="relative flex flex-col items-center justify-center text-center space-y-6 py-16 overflow-hidden rounded-2xl border border-neutral-200/50 dark:border-neutral-800/50 bg-gradient-to-b from-white via-emerald-50/30 to-white dark:from-neutral-950 dark:via-emerald-950/20 dark:to-neutral-950">
        <DotPattern
          className="[mask-image:radial-gradient(350px_circle_at_center,white,transparent)] opacity-60"
          cr={1.5}
          cx={1}
          cy={1}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <AnimatedGradientText className="text-sm font-medium px-6 py-2 rounded-full border border-emerald-200/50 bg-white/80 backdrop-blur-md shadow-lg shadow-emerald-500/5 dark:border-emerald-700/30 dark:bg-neutral-900/80">
            {t("dashboard.badge")}
          </AnimatedGradientText>
        </motion.div>
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl text-foreground relative z-10"
        >
          {t("dashboard.title")} <span className="bg-gradient-to-r from-emerald-600 via-green-500 to-teal-500 bg-clip-text text-transparent dark:from-emerald-400 dark:via-green-400 dark:to-teal-400">{t("dashboard.titleHighlight")}</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed font-medium relative z-10"
        >
          {t("dashboard.subtitle")}
        </motion.p>
      </div>

      {/* Real Stats from API */}
      {/* Stats Cards */}
      {(stats.totalMandis > 0 || stats.totalCommodities > 0 || stats.totalStates > 0) && (
        <div className="grid grid-cols-3 gap-3 md:gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="relative overflow-hidden text-center py-6 px-3 rounded-xl border border-emerald-200/50 bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-950/30 dark:to-green-950/20 dark:border-emerald-800/30 shadow-md"
          >
            <p className="text-3xl font-bold bg-gradient-to-br from-emerald-600 to-green-500 bg-clip-text text-transparent">
              {stats.totalMandis}
            </p>
            <p className="text-sm font-medium text-muted-foreground mt-1">Mandis Tracked</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            className="relative overflow-hidden text-center py-6 px-3 rounded-xl border border-indigo-200/50 bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-indigo-950/30 dark:to-violet-950/20 dark:border-indigo-800/30 shadow-md"
          >
            <p className="text-3xl font-bold bg-gradient-to-br from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              {stats.totalCommodities}
            </p>
            <p className="text-sm font-medium text-muted-foreground mt-1">Commodities</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
            className="relative overflow-hidden text-center py-6 px-3 rounded-xl border border-rose-200/50 bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-950/30 dark:to-pink-950/20 dark:border-rose-800/30 shadow-md"
          >
            <p className="text-3xl font-bold bg-gradient-to-br from-rose-600 to-pink-500 bg-clip-text text-transparent">
              {stats.totalStates}
            </p>
            <p className="text-sm font-medium text-muted-foreground mt-1">States Covered</p>
          </motion.div>
        </div>
      )}

      {/* Weather Widget with ShineBorder */}
      {weather.length > 0 && (
        <div className="relative rounded-2xl overflow-hidden">
          <ShineBorder
            shineColor={["#38bdf8", "#818cf8", "#c084fc"]}
            borderWidth={2}
          />
          <div className="rounded-2xl bg-gradient-to-br from-sky-50/80 via-blue-50/50 to-indigo-50/30 dark:from-sky-950/40 dark:via-blue-950/30 dark:to-indigo-950/20 p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg bg-sky-100 dark:bg-sky-900/40">
                <CloudSunIcon className="h-5 w-5 text-sky-600 dark:text-sky-400" />
              </div>
              <h3 className="font-semibold text-foreground">{t("dashboard.weatherTitle")}</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {weather.map((day) => (
                <motion.div
                  key={day.date}
                  whileHover={{ scale: 1.03 }}
                  className="flex flex-col items-center gap-1.5 p-4 rounded-xl bg-white/70 dark:bg-neutral-900/50 backdrop-blur-md shadow-sm border border-white/50 dark:border-neutral-800/50 transition-shadow hover:shadow-md"
                >
                  <span className="text-xs text-muted-foreground font-semibold">
                    {new Date(day.date).toLocaleDateString(locale === "hi" ? "hi-IN" : "en-US", { weekday: "short", month: "short", day: "numeric" })}
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
                    {t("entities." + day.advisory).split("।")[0].split(".")[0]}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Bento Grid with Meteors */}
      <div className="relative overflow-hidden rounded-2xl">
        <Meteors number={12} />
        <BentoGrid className="lg:grid-rows-2">
          {features.map((feature) => (
            <BentoCard key={feature.name} {...feature} />
          ))}
        </BentoGrid>
      </div>

      {/* Marquee for Live Prices */}
      {priceTicks.length > 0 && (
        <div className="relative flex w-full flex-col items-center justify-center overflow-hidden rounded-2xl border border-neutral-200/50 bg-gradient-to-r from-white via-emerald-50/20 to-white py-8 shadow-lg dark:from-neutral-950 dark:via-emerald-950/10 dark:to-neutral-950 dark:border-neutral-800/50">
          <Marquee pauseOnHover className="[--duration:40s]">
            {priceTicks.map((item) => (
              <div key={item.crop} className="mx-8 flex flex-col items-center space-y-1.5 px-4 py-2 rounded-xl hover:bg-neutral-50/80 dark:hover:bg-neutral-900/50 transition-colors">
                <span className="text-sm font-semibold text-muted-foreground">{item.crop}</span>
                <span className="text-xl font-bold text-foreground tracking-tight">{item.price}</span>
                <span className={cn("text-xs font-bold px-2 py-0.5 rounded-full", item.change.startsWith("+") ? "text-emerald-700 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/40" : "text-rose-700 bg-rose-100 dark:text-rose-400 dark:bg-rose-900/40")}>
                  {item.change}
                </span>
              </div>
            ))}
          </Marquee>
          <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-white dark:from-neutral-950"></div>
          <div className="pointer-events-none absolute inset-y-0 right-0 w-1/4 bg-gradient-to-l from-white dark:from-neutral-950"></div>
        </div>
      )}
    </motion.div>
  );
}
