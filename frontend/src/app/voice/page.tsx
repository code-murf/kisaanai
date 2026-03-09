"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Mic, Volume2, Send, X, ChevronLeft } from "lucide-react"
import dynamic from "next/dynamic"
import { motion, AnimatePresence } from "framer-motion"

const Siriwave = dynamic(() => import("react-siriwave"), { ssr: false })

const API_BASE = ""



/* ------------------------------------------------------------------ */
/*  Chat Message Component                                              */
/* ------------------------------------------------------------------ */
interface ChatMessage {
  id: string
  role: "user" | "assistant"
  text: string
  audio?: string | null
  timestamp: Date
}

function ChatBubble({
  message,
  onPlayAudio,
}: {
  message: ChatMessage
  onPlayAudio: (audio: string | null, text: string) => void
}) {
  const isUser = message.role === "user"
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-emerald-600 text-white rounded-br-md"
            : "bg-zinc-800/80 text-zinc-100 rounded-bl-md"
        }`}
      >
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{message.text}</p>
        {!isUser && (
          <button
            onClick={() => onPlayAudio(message.audio ?? null, message.text)}
            className="mt-2 flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            <Volume2 className="h-3.5 w-3.5" /> Play audio
          </button>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main Voice Page                                                     */
/* ------------------------------------------------------------------ */
export default function VoicePage() {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isContinuousMode, setIsContinuousMode] = useState(false)
  const [language, setLanguage] = useState<"hi" | "en">("hi")
  const [transcript, setTranscript] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [textInput, setTextInput] = useState("")
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null)

  const recognitionRef = useRef<any>(null)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const isContinuousModeRef = useRef(false)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    isContinuousModeRef.current = isContinuousMode
  }, [isContinuousMode])

  // Get location on mount
  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          })
        },
        (error) => {
          console.warn("Location access denied or unavailable:", error)
        }
      )
    }
  }, [])

  // Initialize Speech Recognition
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      ("webkitSpeechRecognition" in window || "SpeechRecognition" in window)
    ) {
      const SR = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      const recognition = new SR()
      recognition.continuous = false
      recognition.interimResults = true
      recognition.lang = language === "hi" ? "hi-IN" : "en-US"

      recognition.onresult = (event: any) => {
        let interim = ""
        let final = ""
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript
          if (event.results[i].isFinal) final += t
          else interim += t
        }
        setTranscript(final || interim)
      }

      recognition.onerror = () => setIsListening(false)
      recognition.onend = () => setIsListening(false)

      recognitionRef.current = recognition
    }

    return () => {
      recognitionRef.current?.stop()
      currentAudioRef.current?.pause()
    }
  }, [language])

  // Setup microphone audio analyser for waveform
  const setupAudioAnalyser = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const ctx = new AudioContext()
      audioContextRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 2048
      analyser.smoothingTimeConstant = 0.85
      source.connect(analyser)
      analyserRef.current = analyser
    } catch (err) {
      console.error("Microphone access denied:", err)
    }
  }, [])

  const cleanupAudioAnalyser = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    audioContextRef.current?.close()
    analyserRef.current = null
    audioContextRef.current = null
    streamRef.current = null
  }, [])

  const toggleContinuousMode = async () => {
    if (isContinuousMode) {
      setIsContinuousMode(false)
      recognitionRef.current?.stop()
      setIsListening(false)
      if (currentAudioRef.current) currentAudioRef.current.pause()
      setIsSpeaking(false)
      if ("speechSynthesis" in window) window.speechSynthesis.cancel()
      cleanupAudioAnalyser()
    } else {
      setIsContinuousMode(true)
      setTranscript("")
      await setupAudioAnalyser()
      try {
        recognitionRef.current?.start()
        setIsListening(true)
      } catch {
        // Ignore errors if recognition fails to start
      }
    }
  }

  const fallbackTTS = useCallback(
    (text: string, onEnd: () => void) => {
      if ("speechSynthesis" in window) {
        const u = new SpeechSynthesisUtterance(text)
        u.lang = language === "hi" ? "hi-IN" : "en-US"
        u.onend = onEnd
        u.onerror = onEnd
        window.speechSynthesis.speak(u)
      } else {
        onEnd()
      }
    },
    [language]
  )

  const playResponseAudio = useCallback(
    (base64Audio: string | null, text: string) => {
      const handleEnded = () => {
        setIsSpeaking(false)
        if (isContinuousModeRef.current) {
          setTimeout(() => {
            try {
              if (isContinuousModeRef.current) {
                recognitionRef.current?.start()
                setIsListening(true)
              }
            } catch (e) {
              console.warn("Speech recognition restart error:", e)
            }
          }, 400)
        }
      }

      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current = null
      }

      setIsSpeaking(true)

      if (base64Audio) {
        const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`)
        currentAudioRef.current = audio
        audio.onended = handleEnded
        audio.onerror = () => fallbackTTS(text, handleEnded)
        audio.play().catch(() => fallbackTTS(text, handleEnded))
        return
      }

      fallbackTTS(text, handleEnded)
    },
    [fallbackTTS]
  )

  const processQuery = async (inputText?: string) => {
    const queryText = (inputText ?? transcript).trim()
    if (!queryText || isProcessing) return

    setIsProcessing(true)
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      text: queryText,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])

    try {
      const res = await fetch(`${API_BASE}/api/v1/voice/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: queryText,
          language: language === "hi" ? "hi-IN" : "en-IN",
          ...(location ? { lat: location.lat, lon: location.lon } : {}),
        }),
      })

      if (!res.ok) throw new Error(`API error (${res.status})`)

      const data = await res.json()
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text: data.response || "Sorry, I could not process that.",
        audio: data.audio || null,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      playResponseAudio(data.audio || null, data.response || "")
    } catch {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        text:
          language === "hi"
            ? "Maaf kijiye, abhi server se jawab nahi mila. Kripya dubara koshish karen."
            : "Sorry, I couldn't reach the server. Please try again.",
        timestamp: new Date(),
        audio: null
      }
      setMessages((prev) => [...prev, errorMsg])
      playResponseAudio(null, errorMsg.text)
    } finally {
      setIsProcessing(false)
    }
  }

  // Auto-submit when speech recognition ends with text, or restart if empty
  useEffect(() => {
    if (!isListening) {
      if (transcript.trim() && !isProcessing) {
        processQuery(transcript)
        setTranscript("")
      } else if (!transcript.trim() && isContinuousMode && !isProcessing && !isSpeaking) {
        const t = setTimeout(() => {
          if (isContinuousModeRef.current && !isProcessing && !isSpeaking) {
            try {
              recognitionRef.current?.start()
              setIsListening(true)
            } catch {
              // Ignore already-started errors
            }
          }
        }, 500)
        return () => clearTimeout(t)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isListening, transcript, isContinuousMode, isProcessing, isSpeaking])

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!textInput.trim()) return
    processQuery(textInput)
    setTextInput("")
  }

  const exampleQueries = [
    { hi: "Aaj aaloo ka bhaav kya hai?", en: "What is potato price today?" },
    { hi: "Sabse acchi mandi kaunsi hai?", en: "Which mandi is best?" },
    { hi: "Mausam kaisa rahega?", en: "How will the weather be?" },
  ]

  const greeting = language === "hi" ? "Namaste Kisaan" : "Hello Farmer"
  const hasMessages = messages.length > 0

  /* ---- Voice Mode UI ---- */
  return (
    <AnimatePresence mode="wait">
      {isContinuousMode ? (
        <motion.div
          key="continuous"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 1.05 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="relative flex h-[calc(100dvh-7rem)] w-full flex-col overflow-hidden md:h-[calc(100dvh-8rem)]" 
          style={{ background: '#05070A' }}
        >
        {/* Top bar with back button */}
        <div className="flex items-center gap-4 px-5 py-4 z-20 absolute top-0 w-full">
            <button
              onClick={toggleContinuousMode}
              className="flex items-center justify-center h-10 w-10 rounded-full bg-zinc-800/60 hover:bg-zinc-700/80 transition-colors"
            >
              <ChevronLeft className="h-6 w-6 text-zinc-300" />
            </button>
            <div className="flex items-center gap-2 flex-1 justify-center -ml-10">
              <span className="text-sm font-medium text-white/60 tracking-wider">
                {language === "hi" ? "HINDI" : "ENGLISH"}
              </span>
            </div>
        </div>
        
        {/* Central Orb / Bubble */}
        <div className="flex-1 flex flex-col items-center justify-center relative z-10 w-full mt-10">
            <div className="relative flex items-center justify-center w-full max-w-lg mx-auto h-[400px]">
                {/* The glowing bubble */}
                <div 
                    className="absolute rounded-full pointer-events-none transition-all duration-700 ease-in-out"
                    style={{
                        width: '350px',
                        height: '350px',
                        background: 'radial-gradient(50% 50% at 50% 50%, #0A0E1C 7.81%, rgba(10, 14, 28, 0) 73.44%, rgba(12, 130, 168, 0.81) 100%)',
                        boxShadow: 'inset -10.9948px -1.83246px 9.1623px rgba(255, 255, 255, 0.5), inset 7.32984px 1.83246px 12.8272px rgba(255, 255, 255, 0.5), inset 0px -5.49738px 7.32984px rgba(255, 255, 255, 0.3)',
                        opacity: isProcessing ? 0.6 : (isSpeaking ? 1 : (isListening ? 0.8 : 0.4)),
                        transform: isSpeaking ? 'scale(1.1)' : isProcessing ? 'scale(0.95)' : 'scale(1)',
                    }}
                />
                
                {/* The Waveform layered on top of the bubble */}
                <div className="absolute w-full px-4 sm:px-12 flex items-center justify-center pointer-events-none">
                    <Siriwave 
                      theme="ios9"
                      width={450}
                      height={200}
                      speed={isSpeaking ? 0.15 : isListening ? 0.08 : 0.02}
                      amplitude={isSpeaking ? 2.5 : isListening ? 1.5 : 0.3}
                      autostart={true}
                    />
                </div>
            </div>
            
            {/* Status & Transcript Text */}
            <div className="mt-4 text-center px-6 max-w-xl flex flex-col items-center min-h-[120px] w-full font-mono">
                <p 
                  className="text-[20px] font-light transition-all duration-300 h-16 w-full flex items-center justify-center mb-2" 
                  style={{ color: '#1CC0D1' }}
                >
                    {transcript 
                      ? `${transcript}` 
                      : (isSpeaking && messages.length > 0) 
                          ? `${messages[messages.length - 1].text.substring(0, 80)}${messages[messages.length - 1].text.length > 80 ? "..." : ""}` 
                          : ""
                    }
                </p>
                <h3 
                  className="text-4xl font-medium tracking-wide transition-colors duration-300"
                  style={{ color: '#FBFBFB' }}
                >
                    {isProcessing ? "Processing..." : isSpeaking ? "Speaking..." : "Listening..."}
                </h3>
            </div>
        </div>
        
        {/* Blur sides for edge effects */}
        <div className="absolute top-1/2 left-0 w-[70px] h-[181px] -translate-y-1/2 pointer-events-none hidden md:block" style={{ background: 'rgba(24, 25, 53, 0.96)', filter: 'blur(15px)' }} />
        <div className="absolute top-1/2 right-0 w-[70px] h-[181px] -translate-y-1/2 pointer-events-none hidden md:block" style={{ background: 'rgba(24, 25, 53, 0.96)', filter: 'blur(15px)' }} />
        
        {/* Bottom controls */}
        <div className="absolute bottom-24 z-20 flex w-full justify-center md:bottom-28">
             <button
                onClick={toggleContinuousMode}
                className="h-16 w-16 flex items-center justify-center rounded-full bg-red-600/90 hover:bg-red-500 transition-transform hover:scale-105 shadow-[0_4px_20px_rgba(220,38,38,0.4)]"
             >
                <X className="h-8 w-8 text-white" />
             </button>
        </div>
      </motion.div>
      ) : (
      <motion.div
        key="chat"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="relative flex h-[calc(100dvh-7rem)] flex-col overflow-hidden bg-black md:h-[calc(100dvh-8rem)]"
      >
      {/* ---- Top Bar ---- */}
      <div className="flex items-center justify-between px-5 py-4 z-10">
        <button
          onClick={() => window.history.back()}
          className="flex items-center justify-center h-10 w-10 rounded-full bg-zinc-800/60 hover:bg-zinc-700/80 transition-colors"
        >
          <ChevronLeft className="h-5 w-5 text-zinc-300" />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-[15px] font-semibold text-white">KisaanAI</span>
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => setLanguage("hi")}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              language === "hi"
                ? "bg-emerald-600 text-white"
                : "bg-zinc-800/60 text-zinc-400 hover:bg-zinc-700/80"
            }`}
          >
            हिं
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              language === "en"
                ? "bg-emerald-600 text-white"
                : "bg-zinc-800/60 text-zinc-400 hover:bg-zinc-700/80"
            }`}
          >
            EN
          </button>
        </div>
      </div>

      {/* ---- Hero / Chat Area ---- */}
      <div className="flex-1 overflow-y-auto px-5 relative">
        {!hasMessages ? (
          <div className="flex flex-col items-center justify-center h-full -mt-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-800/70 mb-6">
              <span className="text-base text-zinc-200">{greeting}</span>
              <span className="text-xl">👋</span>
            </div>

            <h1 className="text-center text-4xl md:text-5xl font-light text-white leading-tight mb-2">
              {language === "hi" ? "Kya madad" : "What can I"}
            </h1>
            <h1 className="text-center text-4xl md:text-5xl font-bold text-white leading-tight">
              {language === "hi" ? "chahiye aapko?" : "help you with?"}
            </h1>

            <div className="flex flex-wrap justify-center gap-2 mt-10">
              {exampleQueries.map((q, i) => (
                <button
                  key={i}
                  onClick={() => processQuery(language === "hi" ? q.hi : q.en)}
                  className="px-4 py-2.5 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 text-zinc-300 text-sm hover:bg-zinc-700/60 hover:border-emerald-500/30 hover:text-white transition-all"
                >
                  {language === "hi" ? q.hi : q.en}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="pt-4 pb-4">
            {messages.map((m) => (
              <ChatBubble key={m.id} message={m} onPlayAudio={playResponseAudio} />
            ))}
            {isProcessing && (
              <div className="flex justify-start mb-3">
                <div className="bg-zinc-800/80 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1.5 items-center">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0ms]" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:150ms]" />
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="relative z-10">
        <div className="px-5 py-4 flex items-center gap-3">
          <form onSubmit={handleTextSubmit} className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={
                language === "hi"
                  ? "Type karein ya mic dabayein..."
                  : "Type or tap the mic..."
              }
              className="flex-1 bg-zinc-800/70 border border-zinc-700/50 rounded-full px-5 py-3 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500/50 transition-colors"
              disabled={isProcessing}
            />
            {textInput.trim() && (
              <button
                type="submit"
                disabled={isProcessing}
                className="h-11 w-11 flex items-center justify-center rounded-full bg-emerald-600 hover:bg-emerald-500 transition-colors disabled:opacity-50"
              >
                <Send className="h-4 w-4 text-white" />
              </button>
            )}
          </form>

          <button
            onClick={toggleContinuousMode}
            disabled={isProcessing}
            className="relative h-14 w-14 flex items-center justify-center rounded-full bg-emerald-600 hover:bg-emerald-500 transition-all disabled:opacity-50"
          >
            <Mic className="h-6 w-6 text-white relative z-10" />
          </button>
        </div>
        <div className="h-2" />
        </div>
      </motion.div>
      )}
    </AnimatePresence>
  )
}
