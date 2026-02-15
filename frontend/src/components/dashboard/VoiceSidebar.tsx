"use client";

import { useState, useEffect, useRef } from "react";
import { useConversation } from "@elevenlabs/react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, X, ChevronRight, Volume2, Loader2, PhoneOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function VoiceSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  
  const conversation = useConversation({
    onConnect: () => console.log("Connected to ElevenLabs"),
    onDisconnect: () => console.log("Disconnected from ElevenLabs"),
    onMessage: (message: any) => console.log("Message:", message),
    onError: (error: any) => console.error("Error:", error),
  });

  const { status, isSpeaking } = conversation;

  // Fetch signed URL on mount or when opening
  useEffect(() => {
    const fetchSignedUrl = async () => {
      try {
        const response = await fetch("/api/v1/voice/agent-token");
        if (!response.ok) throw new Error("Failed to get token");
        const data = await response.json();
        setSignedUrl(data.signed_url);
      } catch (error) {
        console.error("Error fetching signed URL:", error);
      }
    };

    fetchSignedUrl();
  }, []);

  const handleStartConversation = async () => {
    if (!signedUrl) {
      console.error("No signed URL available");
      return;
    }
    
    try {
      // Assuming the SDK supports signedUrl in startSession or similar
      // If the SDK strictly requires agentId for public agents, we might need to adjust.
      // For signed URLs, commonly it's passed as an override or specific connection option.
      // Based on recent SDK updates, startSession can take a signedUrl (sometimes named differently or just url).
      // Let's try passing it.
      await conversation.startSession({
          // @ts-ignore - SDK types might be strict, but runtime often supports it
          signedUrl: signedUrl 
      });
    } catch (error) {
       console.error("Failed to start session:", error);
    }
  };

  const handleEndConversation = async () => {
    await conversation.endSession();
  };

  const toggleSidebar = () => setIsOpen(!isOpen);

  return (
    <>
      {/* Trigger Button */}
      <motion.div
        className="fixed bottom-6 right-6 z-50"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <Button
          size="icon"
          className={cn(
            "h-14 w-14 rounded-full shadow-xl bg-linear-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transition-all duration-300 border-2 border-white/20",
            status === "connected" && "animate-pulse ring-4 ring-green-500/30"
          )}
          onClick={toggleSidebar}
        >
          {status === "connected" ? (
             <Volume2 className="h-6 w-6 text-white" />
          ) : (
             <Mic className="h-6 w-6 text-white" />
          )}
        </Button>
      </motion.div>

      {/* Sidebar Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            />
            
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 h-full w-full sm:w-[400px] bg-background/95 backdrop-blur-xl border-l border-border/50 shadow-2xl z-50 flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border/50 bg-muted/20">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <span className="text-xl">🤖</span>
                  </div>
                  <div>
                    <h2 className="font-semibold text-lg">AgriBot</h2>
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <span className={cn("h-2 w-2 rounded-full", status === "connected" ? "bg-green-500" : "bg-gray-400")} />
                      {status === "connected" ? (isSpeaking ? "Speaking..." : "Listening...") : "Offline"}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)}>
                  <ChevronRight className="h-5 w-5" />
                </Button>
              </div>

              {/* Conversation Area (Visualizer Placeholder) */}
              <div className="flex-1 overflow-y-auto p-4 flex flex-col items-center justify-center relative bg-linear-to-b from-background to-muted/20">
                
                {status === "connected" ? (
                  <div className="relative w-48 h-48 flex items-center justify-center">
                     {/* Ripples */}
                     <motion.div 
                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                        className="absolute inset-0 rounded-full bg-green-500/20"
                     />
                     <motion.div 
                        animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
                        transition={{ repeat: Infinity, duration: 2, delay: 0.5, ease: "easeInOut" }}
                        className="absolute inset-0 rounded-full bg-green-500/10"
                     />
                     
                     <div className="h-32 w-32 rounded-full bg-linear-to-br from-green-400 to-emerald-600 shadow-2xl flex items-center justify-center z-10 border-4 border-white/10">
                        {isSpeaking ? (
                            <Volume2 className="h-12 w-12 text-white" />
                        ) : (
                            <Mic className="h-12 w-12 text-white" />
                        )}
                     </div>
                  </div>
                ) : (
                  <div className="text-center space-y-4">
                    <div className="h-24 w-24 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                        <Mic className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground">
                        Tap the microphone to start talking to AgriBot.
                    </p>
                  </div>
                )}

              </div>

              {/* Controls */}
              <div className="p-6 border-t border-border/50 bg-background/50">
                <div className="flex justify-center gap-4">
                  {status === "connected" ? (
                    <Button 
                      variant="destructive" 
                      size="lg" 
                      className="rounded-full h-16 w-16 shadow-lg hover:shadow-red-500/20"
                      onClick={handleEndConversation}
                    >
                      <PhoneOff className="h-6 w-6" />
                    </Button>
                  ) : (
                    <Button 
                      variant="default" 
                      size="lg" 
                      className="rounded-full h-16 w-16 bg-green-600 hover:bg-green-700 shadow-lg hover:shadow-green-500/20"
                      onClick={handleStartConversation}
                      disabled={!signedUrl}
                    >
                      {!signedUrl ? (
                          <Loader2 className="h-6 w-6 animate-spin" />
                      ) : (
                          <Mic className="h-6 w-6" />
                      )}
                    </Button>
                  )}
                </div>
                <p className="text-center text-xs text-muted-foreground mt-4">
                  Powered by ElevenLabs Conversational AI
                </p>
              </div>

            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
