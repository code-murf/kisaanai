"use client";

import { useState, useRef, useEffect } from "react";
import { Music, Music3 } from "lucide-react";

export function BackgroundMusic() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Create audio element only on client side
    audioRef.current = new Audio("/ambient-farm.mp3");
    audioRef.current.loop = true;
    audioRef.current.volume = 0.3; // Soft background volume

    const handleInteraction = () => {
      if (!hasInteracted) {
        setHasInteracted(true);
        // We do not auto-play immediately on interaction, users have to click the button.
        // Or if preferred, we could auto-play here: audioRef.current?.play(); setIsPlaying(true);
      }
    };

    window.addEventListener("click", handleInteraction, { once: true });
    
    return () => {
      window.removeEventListener("click", handleInteraction);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }
    };
  }, [hasInteracted]);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise.catch(error => {
            console.error("Audio playback failed:", error);
          });
        }
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <button
      onClick={togglePlay}
      className={`fixed bottom-24 right-6 z-50 p-3 rounded-full shadow-lg backdrop-blur-md transition-all duration-300 hover:scale-110 flex items-center justify-center 
        ${isPlaying 
          ? "bg-emerald-600/90 text-white shadow-emerald-500/50" 
          : "bg-neutral-900/80 text-neutral-400 border border-neutral-700/50 hover:bg-neutral-800"}`}
      aria-label={isPlaying ? "Mute background music" : "Play background music"}
      title={isPlaying ? "Mute background music" : "Play background music"}
    >
      {isPlaying ? (
        <Music className="w-5 h-5 animate-pulse" />
      ) : (
        <Music3 className="w-5 h-5 opacity-70" />
      )}
      
      {/* Subtle glowing ring when playing */}
      {isPlaying && (
        <span className="absolute inset-0 rounded-full animate-ping opacity-30 bg-emerald-400 border border-emerald-300"></span>
      )}
    </button>
  );
}
