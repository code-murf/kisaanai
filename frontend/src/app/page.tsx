import { MagicDashboard } from "@/components/dashboard/MagicDashboard";
import { Meteors } from "@/components/ui/meteors";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020b09] text-white">
      <video
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-55"
        src="/dashboard-loop.mp4"
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
      />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,197,94,0.16),transparent_30%),linear-gradient(180deg,rgba(2,12,10,0.08),rgba(1,8,8,0.68)_38%,rgba(0,0,0,0.88)_100%)]" />
      <div className="dashboard-ambient-orb dashboard-ambient-orb--a" />
      <div className="dashboard-ambient-orb dashboard-ambient-orb--b" />
      <div className="dashboard-shimmer-band" />

      <div className="relative z-10 flex min-h-screen flex-col items-center px-4 py-4 md:px-12 md:py-12 lg:px-24 lg:py-20">
        <div className="absolute inset-0 opacity-35">
          <Meteors number={18} />
        </div>

        <div className="relative z-10 w-full max-w-5xl rounded-[28px] border border-white/14 bg-black/28 p-4 shadow-[0_24px_90px_rgba(0,0,0,0.45)] backdrop-blur-xl md:p-8">
          <MagicDashboard />
        </div>
      </div>
    </main>
  );
}
