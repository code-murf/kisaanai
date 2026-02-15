"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Pause, Mic, MapPin, ThumbsUp } from "lucide-react";
import { cn } from "@/lib/utils";

type AudioNote = {
  id: string;
  user_name: string;
  location_lat: number;
  location_lng: number;
  audio_url: string;
  created_at: string;
  likes: number;
  tags: string[];
};

export function CommunityFeed() {
  const [notes, setNotes] = useState<AudioNote[]>([]);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioRef, setAudioRef] = useState<HTMLAudioElement | null>(null);

  // Mock Data Load (replace with API call later)
  useEffect(() => {
    // In real app: fetch('/api/v1/community/notes')
    const mockNotes: AudioNote[] = [
      {
        id: "1",
        user_name: "Rinesh Patel",
        location_lat: 28.6,
        location_lng: 77.2,
        audio_url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", // Demo URL
        created_at: "2 hours ago",
        likes: 12,
        tags: ["Azadpur", "Road Block"],
      },
      {
        id: "2",
        user_name: "Suresh Kumar",
        location_lat: 28.5,
        location_lng: 77.1,
        audio_url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        created_at: "5 hours ago",
        likes: 8,
        tags: ["Market Price", "Tomato"],
      },
    ];
    setNotes(mockNotes);
  }, []);

  const togglePlay = (note: AudioNote) => {
    if (playingId === note.id) {
      audioRef?.pause();
      setPlayingId(null);
    } else {
      if (audioRef) audioRef.pause();
      const audio = new Audio(note.audio_url);
      audio.onended = () => setPlayingId(null);
      audio.play();
      setAudioRef(audio);
      setPlayingId(note.id);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5 text-orange-500" />
            Community Voice
          </CardTitle>
          <Button size="sm" variant="outline" className="h-8 text-xs">
            <MapPin className="h-3 w-3 mr-1" />
            Nearby: 50km
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-0">
        <div className="divide-y divide-border/50">
          {notes.map((note) => (
            <div key={note.id} className="p-4 hover:bg-muted/30 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-xs font-bold text-orange-700 dark:text-orange-400">
                    {note.user_name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium leading-none">{note.user_name}</p>
                    <p className="text-xs text-muted-foreground">{note.created_at}</p>
                  </div>
                </div>
                <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground hover:text-green-500">
                    <ThumbsUp className="h-4 w-4" />
                    <span className="sr-only">Like</span>
                </Button>
              </div>

              <div className="flex items-center gap-3 bg-muted/50 p-2 rounded-lg mb-2">
                 <Button
                    size="icon"
                    className={cn(
                        "h-8 w-8 rounded-full shadow-sm transition-all",
                        playingId === note.id ? "bg-orange-500 hover:bg-orange-600" : "bg-white dark:bg-zinc-800 text-foreground hover:bg-gray-100"
                    )}
                    onClick={() => togglePlay(note)}
                 >
                    {playingId === note.id ? <Pause className="h-4 w-4 text-white" /> : <Play className="h-4 w-4 fill-current" />}
                 </Button>
                 <div className="h-1 flex-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div className={cn("h-full bg-orange-500 animate-pulse w-2/3", playingId === note.id ? "opacity-100" : "opacity-0")} />
                 </div>
                 <span className="text-xs font-mono text-muted-foreground">0:15s</span>
              </div>

              <div className="flex flex-wrap gap-1">
                {note.tags.map(tag => (
                    <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-border/50">
                        #{tag}
                    </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
      <div className="p-3 border-t border-border/50 bg-muted/20">
         <Button className="w-full bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white shadow-md">
            <Mic className="h-4 w-4 mr-2" />
            Record Note
         </Button>
      </div>
    </Card>
  );
}
