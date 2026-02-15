import { MagicDashboard } from "@/components/dashboard/MagicDashboard";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4 md:p-12 lg:p-24 bg-neutral-50 dark:bg-neutral-950">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        {/* Header/Nav could go here */}
      </div>

      <div className="w-full max-w-5xl">
        <MagicDashboard />
      </div>

      <div className="mb-32 grid text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-4 lg:text-left">
        {/* Footer or extra links could go here */}
      </div>
    </main>
  );
}
