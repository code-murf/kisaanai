"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Mic, Square, Play, Pause, Users, Heart, MapPin, Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslation } from "@/hooks/useTranslation"
import { cn } from "@/lib/utils"

interface AudioNote {
  id: string
  user_id: string
  user_name: string
  location_lat: number
  location_lng: number
  tags: string[]
  audio_url: string
  created_at: string
  likes: number
  is_helpful: boolean
}

export default function CommunityPage() {
  const [notes, setNotes] = useState<AudioNote[]>([])
  const [loading, setLoading] = useState(true)
  const [recording, setRecording] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [playingId, setPlayingId] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const { t } = useTranslation()

  const fetchNotes = async () => {
    try {
      const res = await fetch("/api/v1/community/notes")
      if (res.ok) {
        const data = await res.json()
        setNotes(data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNotes()
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        const url = URL.createObjectURL(audioBlob)
        setAudioUrl(url)
      }

      recorder.start()
      mediaRecorderRef.current = recorder
      setRecording(true)
      setAudioUrl(null)
    } catch (err) {
      console.error("Mic access denied", err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop())
      setRecording(false)
    }
  }

  const handlePublish = async () => {
    if (!audioUrl) return
    setUploading(true)
    
    try {
      const blob = await fetch(audioUrl).then((r) => r.blob())
      const file = new File([blob], "voice_note.webm", { type: "audio/webm" })

      const formData = new FormData()
      formData.append("audio", file)
      formData.append("user_id", "web-user-123")
      formData.append("user_name", "KisaanAI Farmer")
      formData.append("location_lat", "22.7196")
      formData.append("location_lng", "75.8577")
      formData.append("tags", JSON.stringify(["Crop Advice"]))

      const res = await fetch("/api/v1/community/notes", {
        method: "POST",
        body: formData,
      })

      if (res.ok) {
        setAudioUrl(null)
        await fetchNotes()
      }
    } catch (err) {
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const togglePlay = (id: string, url: string) => {
    if (playingId === id) {
      audioRef.current?.pause()
      setPlayingId(null)
    } else {
      if (audioRef.current) {
        audioRef.current.pause()
      }
      const audio = new Audio(url)
      audio.onended = () => setPlayingId(null)
      audio.play()
      audioRef.current = audio
      setPlayingId(id)
    }
  }

  const handleLike = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/community/notes/${id}/like`, { method: "POST" })
      if (res.ok) {
        setNotes((prev) => prev.map((n) => n.id === id ? { ...n, likes: n.likes + 1 } : n))
      }
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 flex flex-col items-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl space-y-8"
      >
        <div className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-4">
            <Users className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            KisaanAI Community
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Voice forum for farmers to share experiences, ask questions, and help each other.
          </p>
        </div>

        {/* Recording Section */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-800 text-center">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">
            {audioUrl ? "Review your Voice Note" : "Record a Voice Note"}
          </h2>
          
          {!audioUrl ? (
            <div className="flex flex-col items-center gap-4">
              <Button
                size="lg"
                onClick={recording ? stopRecording : startRecording}
                className={cn(
                  "rounded-full w-20 h-20 p-0 shadow-lg transition-all",
                  recording ? "bg-red-500 hover:bg-red-600 animate-pulse" : "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {recording ? <Square className="h-8 w-8 text-white fill-current" /> : <Mic className="h-8 w-8 text-white" />}
              </Button>
              <p className={cn("text-sm font-medium", recording ? "text-red-500" : "text-slate-500")}>
                {recording ? "Recording... Tap to stop" : "Tap to start recording"}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg p-4 flex items-center gap-4">
                <Button variant="outline" size="icon" onClick={() => togglePlay("preview", audioUrl)} className="rounded-full">
                  {playingId === "preview" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
                <div className="flex-1 h-2 bg-slate-300 dark:bg-slate-700 rounded-full overflow-hidden">
                  {playingId === "preview" && (
                    <motion.div 
                      className="h-full bg-blue-500"
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 5, ease: "linear" }}
                    />
                  )}
                </div>
              </div>
              
              <div className="flex gap-4 w-full">
                <Button variant="outline" className="flex-1" onClick={() => setAudioUrl(null)} disabled={uploading}>
                  Delete
                </Button>
                <Button className="flex-1 bg-blue-600 hover:bg-blue-700" onClick={handlePublish} disabled={uploading}>
                  {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                  Publish to Community
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Rules/Tags Placeholder */}
        
        {/* Feed Section */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">Recent Community Notes</h3>
          
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full rounded-2xl" />
              <Skeleton className="h-32 w-full rounded-2xl" />
            </div>
          ) : notes.length === 0 ? (
            <div className="text-center py-12 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
              <p className="text-slate-500">No voice notes in your area yet. Be the first!</p>
            </div>
          ) : (
            <AnimatePresence>
              {notes.map((note) => (
                <motion.div
                  key={note.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-white dark:bg-slate-900 rounded-2xl p-5 shadow-sm border border-slate-200 dark:border-slate-800"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-emerald-400 rounded-full flex items-center justify-center text-white font-bold">
                        {note.user_name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-slate-100">{note.user_name}</p>
                        <div className="flex items-center text-xs text-slate-500 gap-2">
                          <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {note.location_lat.toFixed(1)}, {note.location_lng.toFixed(1)}</span>
                          <span>•</span>
                          <span>{new Date(note.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {note.tags && note.tags.length > 0 && (
                     <div className="flex gap-2 mb-4">
                       {note.tags.map(t => (
                         <span key={t} className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded-md">
                           {t}
                         </span>
                       ))}
                     </div>
                  )}

                  <div className="w-full bg-slate-50 dark:bg-slate-950 rounded-xl p-3 flex items-center gap-4 border border-slate-100 dark:border-slate-800">
                    <Button 
                      variant="secondary" 
                      size="icon" 
                      onClick={() => togglePlay(note.id, note.audio_url)} 
                      className="rounded-full shadow-sm bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-blue-600 dark:text-blue-400"
                    >
                      {playingId === note.id ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 fill-current" />}
                    </Button>
                    <div className="flex-1 h-3 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden flex items-center">
                       {/* Purely visual waveform representation */}
                       <div className="w-full flex items-center justify-around h-full opacity-30">
                         {Array.from({length: 40}).map((_, i) => (
                           <div key={i} className="w-1 bg-blue-500 rounded-full" style={{ height: `${Math.max(20, Math.random() * 100)}%` }} />
                         ))}
                       </div>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-4">
                    <button 
                      onClick={() => handleLike(note.id)}
                      className="flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-rose-500 transition-colors"
                    >
                      <Heart className={cn("h-4 w-4", note.likes > 0 && "fill-rose-500 text-rose-500")} /> 
                      {note.likes || "Like"}
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>
      </motion.div>
    </div>
  )
}
