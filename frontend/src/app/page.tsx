import { MagicDashboard } from "@/components/dashboard/MagicDashboard";
import { AuroraText } from "@/components/ui/aurora-text";
import { RetroGrid } from "@/components/ui/retro-grid";
import { Meteors } from "@/components/ui/meteors";

export default function Home() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-between p-4 md:p-12 lg:p-24 bg-neutral-50 dark:bg-neutral-950 overflow-hidden overflow-y-auto">
      <Meteors number={30} />
      <div className="z-10 w-full max-w-5xl items-center justify-center font-mono text-sm flex mb-12 mt-8">
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tighter text-center">
          KisaanAI <br className="md:hidden" />
          <AuroraText>Predicts the Future</AuroraText>
        </h1>
      </div>

      <div className="w-full max-w-5xl z-10 bg-white/50 dark:bg-black/50 backdrop-blur-md rounded-xl p-4 md:p-8 shadow-2xl border border-white/20 dark:border-white/10 relative">
        <MagicDashboard />
      </div>
      
      <RetroGrid />
    </main>
  );
}
