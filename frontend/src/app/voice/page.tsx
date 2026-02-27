"use client"

import { useState, useEffect, useRef } from "react"
import { Mic, MicOff, Volume2, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function VoicePage() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [response, setResponse] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [language, setLanguage] = useState<"hi" | "en">("hi")
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<any>(null)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (typeof window !== "undefined" && ("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = language === "hi" ? "hi-IN" : "en-US"

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = ""
        let finalTranscript = ""

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const chunk = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += chunk
          } else {
            interimTranscript += chunk
          }
        }

        setTranscript(finalTranscript || interimTranscript)
      }

      recognitionRef.current.onerror = () => {
        setError("Could not recognize speech. Please try again.")
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }

    return () => {
      recognitionRef.current?.stop()
      currentAudioRef.current?.pause()
    }
  }, [language])

  const toggleListening = () => {
    setError(null)
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
    } else {
      setTranscript("")
      setResponse("")
      recognitionRef.current?.start()
      setIsListening(true)
    }
  }

  const playResponseAudio = (base64Audio: string | null, text: string) => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current = null
    }

    if (base64Audio) {
      const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`)
      currentAudioRef.current = audio
      audio.play().catch(() => {
        if ("speechSynthesis" in window) {
          const utterance = new SpeechSynthesisUtterance(text)
          utterance.lang = language === "hi" ? "hi-IN" : "en-US"
          window.speechSynthesis.speak(utterance)
        }
      })
      return
    }

    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = language === "hi" ? "hi-IN" : "en-US"
      window.speechSynthesis.speak(utterance)
    }
  }

  const processQuery = async (inputText?: string) => {
    const queryText = (inputText ?? transcript).trim()
    if (!queryText) return

    setIsProcessing(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/api/v1/voice/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: queryText,
          language: language === "hi" ? "hi-IN" : "en-IN",
        }),
      })

      if (!res.ok) {
        throw new Error(`Voice API error (${res.status})`)
      }

      const data = await res.json()
      setResponse(data.response || "")
      playResponseAudio(data.audio || null, data.response || "")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process voice query")
    } finally {
      setIsProcessing(false)
    }
  }

  const exampleQueries = [
    { text: "What is potato price today?", hi: "Aaj aaloo ka bhaav kya hai?" },
    { text: "Which mandi is best now?", hi: "Abhi sabse acchi mandi kaunsi hai?" },
    { text: "Any weather alert for crops?", hi: "Kheti ke liye mausam alert hai kya?" },
  ]

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-20">
      <header className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Voice Assistant</h1>
          <p className="text-muted-foreground">Ask about prices, mandis, or weather in your language</p>
        </div>
        <div className="flex gap-2">
          <Button variant={language === "hi" ? "default" : "outline"} size="sm" onClick={() => setLanguage("hi")}>
            Hindi
          </Button>
          <Button variant={language === "en" ? "default" : "outline"} size="sm" onClick={() => setLanguage("en")}>
            English
          </Button>
        </div>
      </header>

      <Card className="relative overflow-hidden">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-primary/10">
            {isListening ? (
              <div className="relative">
                <Mic className="h-10 w-10 text-primary animate-pulse" />
                <span className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
              </div>
            ) : (
              <MicOff className="h-10 w-10 text-muted-foreground" />
            )}
          </div>
          <CardTitle>{isListening ? "Listening..." : "Tap the microphone to speak"}</CardTitle>
          <CardDescription>
            {language === "hi"
              ? "Bolkar puchhiye: Aaj aaloo ka bhaav kya hai?"
              : "Ask in your language: What is the potato price today?"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-center gap-4">
            <Button
              size="lg"
              variant={isListening ? "destructive" : "default"}
              className={`h-20 w-20 rounded-full ${isListening ? "animate-pulse" : ""}`}
              onClick={toggleListening}
            >
              {isListening ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
            </Button>
          </div>

          {transcript && (
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground mb-1">You said:</p>
              <p className="text-lg font-medium">{transcript}</p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-4 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {transcript && !isListening && (
            <div className="flex justify-center">
              <Button onClick={() => processQuery()} disabled={isProcessing} size="lg">
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Get Answer"
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {response && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Response</CardTitle>
              <Button size="icon" variant="ghost" onClick={() => playResponseAudio(null, response)}>
                <Volume2 className="h-5 w-5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-lg">{response}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Try asking</CardTitle>
          <CardDescription>Tap any question to ask</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2">
            {exampleQueries.map((query, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTranscript(query.hi)
                  processQuery(query.hi)
                }}
                className="rounded-lg border bg-card p-3 text-left transition-colors hover:bg-accent"
              >
                <p className="font-medium">{query.hi}</p>
                <p className="text-sm text-muted-foreground">{query.text}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
