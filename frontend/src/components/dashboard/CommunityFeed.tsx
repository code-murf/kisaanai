"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Pause, Mic, MapPin, ThumbsUp, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocation } from "@/contexts/LocationContext";

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

const API_BASE = "";

function resolveAudioUrl(audioUrl: string) {
  if (!audioUrl) return audioUrl;
  if (audioUrl.startsWith("http://") || audioUrl.startsWith("https://")) return audioUrl;
  return `${API_BASE}${audioUrl}`;
}

export function CommunityFeed() {
  const [notes, setNotes] = useState<AudioNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioRef, setAudioRef] = useState<HTMLAudioElement | null>(null);
  const { location } = useLocation();

  useEffect(() => {
    const fetchNotes = async () => {
      const lat = location?.lat ?? 28.61;
      const lng = location?.lon ?? 77.23;
      try {
        const response = await fetch(`${API_BASE}/api/v1/community/notes?lat=${lat}&lng=${lng}&radius=50`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Community API error (${response.status})`);
        }

        const data = (await response.json()) as AudioNote[];
        setNotes(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load community feed");
        setNotes([]);
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
  }, [location]);

  const togglePlay = (note: AudioNote) => {
    const audioUrl = resolveAudioUrl(note.audio_url);

    if (playingId === note.id) {
      audioRef?.pause();
      setPlayingId(null);
      return;
    }

    if (audioRef) audioRef.pause();
    const audio = new Audio(audioUrl);
    audio.onended = () => setPlayingId(null);
    audio
      .play()
      .then(() => {
        setAudioRef(audio);
        setPlayingId(note.id);
      })
      .catch(() => {
        setPlayingId(null);
      });
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
        {loading ? (
          <div className="p-4 text-sm text-muted-foreground">Loading community notes...</div>
        ) : error ? (
          <div className="p-4 flex items-start gap-2 text-sm text-red-500">
            <AlertCircle className="h-4 w-4 mt-0.5" />
            <span>{error}</span>
          </div>
        ) : notes.length === 0 ? (
          <div className="p-4 text-sm text-muted-foreground">No community notes available yet.</div>
        ) : (
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
                      <p className="text-xs text-muted-foreground">{new Date(note.created_at).toLocaleString()}</p>
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
                      playingId === note.id
                        ? "bg-orange-500 hover:bg-orange-600"
                        : "bg-white dark:bg-zinc-800 text-foreground hover:bg-gray-100"
                    )}
                    onClick={() => togglePlay(note)}
                  >
                    {playingId === note.id ? (
                      <Pause className="h-4 w-4 text-white" />
                    ) : (
                      <Play className="h-4 w-4 fill-current" />
                    )}
                  </Button>
                  <div className="h-1 flex-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full bg-orange-500 animate-pulse w-2/3",
                        playingId === note.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">{note.likes} likes</span>
                </div>

                <div className="flex flex-wrap gap-1">
                  {note.tags.map((tag) => (
                    <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground border border-border/50">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
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

