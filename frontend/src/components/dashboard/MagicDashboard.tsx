"use client";

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
  NewspaperIcon 
} from "lucide-react";

export function MagicDashboard() {
  const features = [
    {
      Icon: MapIcon,
      name: "Find Best Mandi",
      description: "Locate the nearest mandi with the highest profit margin.",
      href: "/mandi",
      cta: "View Map",
      background: <div className="absolute inset-0 bg-gradient-to-br from-emerald-100/50 via-emerald-50/30 to-transparent opacity-100" />,
      className: "col-span-3 md:col-span-1 lg:col-span-1 border-emerald-100 bg-emerald-50/30 dark:bg-emerald-950/20 dark:border-emerald-900/50",
      iconClassName: "text-emerald-700 dark:text-emerald-400",
    },
    {
      Icon: BarChartIcon,
      name: "Price Forecast",
      description: "AI-powered predictions.",
      href: "/charts",
      cta: "See Trends",
      background: <div className="absolute inset-0 bg-gradient-to-br from-indigo-100/50 via-indigo-50/30 to-transparent opacity-100" />,
      className: "col-span-3 md:col-span-2 lg:col-span-1 border-indigo-100 bg-indigo-50/30 dark:bg-indigo-950/20 dark:border-indigo-900/50",
      iconClassName: "text-indigo-700 dark:text-indigo-400",
    },
    {
      Icon: MicIcon,
      name: "Voice Assistant",
      description: "Ask in your language.",
      href: "/voice",
      cta: "Speak Now",
      background: <div className="absolute inset-0 bg-gradient-to-br from-rose-100/50 via-rose-50/30 to-transparent opacity-100" />,
      className: "col-span-3 md:col-span-2 lg:col-span-1 border-rose-100 bg-rose-50/30 dark:bg-rose-950/20 dark:border-rose-900/50",
      iconClassName: "text-rose-700 dark:text-rose-400",
    },
    {
      Icon: CloudSunIcon,
      name: "Crop Doctor",
      description: "Disease detection & advisory.",
      href: "/doctor",
      cta: "Diagnose",
      background: <div className="absolute inset-0 bg-gradient-to-br from-amber-100/50 via-amber-50/30 to-transparent opacity-100" />,
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
          🚀 New: WhatsApp Integration Live!
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

      {/* Main Bento Grid */}
      <BentoGrid className="lg:grid-rows-2">
        {features.map((feature) => (
          <BentoCard key={feature.name} {...feature} />
        ))}
      </BentoGrid>

      {/* Marquee for Prices */}
      <div className="relative flex w-full flex-col items-center justify-center overflow-hidden rounded-xl border border-neutral-200 bg-white py-8 shadow-sm dark:bg-neutral-950 dark:border-neutral-800">
        <Marquee pauseOnHover className="[--duration:40s]">
          {[
            { crop: "Potato", price: "₹1200/q", change: "+2%" },
            { crop: "Onion", price: "₹2500/q", change: "+5%" },
            { crop: "Tomato", price: "₹1800/q", change: "-1%" },
            { crop: "Wheat", price: "₹2100/q", change: "+0.5%" },
            { crop: "Rice", price: "₹3200/q", change: "+1.2%" },
            { crop: "Cotton", price: "₹6000/q", change: "+3%" }
          ].map((item) => (
            <div key={item.crop} className="mx-6 flex flex-col items-center space-y-1">
              <span className="text-sm font-medium text-muted-foreground">{item.crop}</span>
              <span className="text-lg font-bold text-foreground">{item.price}</span>
              <span className={cn("text-xs font-bold", item.change.startsWith("+") ? "text-emerald-600" : "text-rose-600")}>
                {item.change}
              </span>
            </div>
          ))}
        </Marquee>
        <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-white dark:from-neutral-950"></div>
        <div className="pointer-events-none absolute inset-y-0 right-0 w-1/4 bg-gradient-to-l from-white dark:from-neutral-950"></div>
      </div>
    </motion.div>
  );
}
