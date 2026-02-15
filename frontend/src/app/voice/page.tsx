"use client"

import { useState, useEffect, useRef } from "react"
import { Mic, MicOff, Volume2, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function VoicePage() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const [response, setResponse] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [language, setLanguage] = useState<"hi" | "en">("hi")
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<any>(null)
  const synthesisRef = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = language === "hi" ? "hi-IN" : "en-US"

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = ""
        let finalTranscript = ""

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }

        setTranscript(finalTranscript || interimTranscript)
      }

      recognitionRef.current.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error)
        setError("Could not recognize speech. Please try again.")
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
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

  const processQuery = async () => {
    if (!transcript.trim()) return

    setIsProcessing(true)
    setError(null)

    // Simulate API call for demo
    setTimeout(() => {
      const responses: Record<string, string> = {
        "aaj aaloo ka bhaav": "Aaj aaloo ka bhaav Azadpur mandi mein ₹1,240 per quintal hai. Kal se 2.5% badne ka anumaan hai.",
        "potato price": "Today potato price in Azadpur mandi is ₹1,240 per quintal. Expected to rise by 2.5% tomorrow.",
        "best mandi": "Aapke liye sabse behtar mandi Azadpur hai. Waheen ₹1,240 ka bhaav hai aur sirf 12 km doori hai.",
        "weather": "Agle 2 din mein heavy rain hone ki sambhavna hai. Fasal jaldi katein behtar hoga.",
      }

      const lowerTranscript = transcript.toLowerCase()
      const matchedResponse =
        Object.keys(responses).find((key) => lowerTranscript.includes(key)) || responses["potato price"]

      setResponse(matchedResponse)
      speakResponse(matchedResponse)
      setIsProcessing(false)
    }, 1500)
  }

  const speakResponse = (text: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel()
      synthesisRef.current = new SpeechSynthesisUtterance(text)
      synthesisRef.current.lang = language === "hi" ? "hi-IN" : "en-US"
      synthesisRef.current.rate = 0.9
      synthesisRef.current.pitch = 1
      window.speechSynthesis.speak(synthesisRef.current)
    }
  }

  const exampleQueries = [
    { text: "Aaj aaloo ka bhaav kya hai?", hi: "Aaj aaloo ka bhaav kya hai?" },
    { text: "Best mandi kaha hai?", hi: "Best mandi kaha hai?" },
    { text: "Weather kaisa rahega?", hi: "Weather kaisa rahega?" },
  ]

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-20">
      <header className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Voice Assistant</h1>
          <p className="text-muted-foreground">Ask about prices, mandis, or weather in your language</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={language === "hi" ? "default" : "outline"}
            size="sm"
            onClick={() => setLanguage("hi")}
          >
            हिंदी
          </Button>
          <Button
            variant={language === "en" ? "default" : "outline"}
            size="sm"
            onClick={() => setLanguage("en")}
          >
            English
          </Button>
        </div>
      </header>

      {/* Voice Input Section */}
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
          <CardTitle>
            {isListening ? "Listening..." : "Tap the microphone to speak"}
          </CardTitle>
          <CardDescription>
            {language === "hi"
              ? "अपनी भाषा में पूछें: आज आलू का भाव क्या है?"
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
              <Button onClick={processQuery} disabled={isProcessing} size="lg">
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

      {/* Response Section */}
      {response && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Response</CardTitle>
              <Button size="icon" variant="ghost" onClick={() => speakResponse(response)}>
                <Volume2 className="h-5 w-5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-lg">{response}</p>
          </CardContent>
        </Card>
      )}

      {/* Example Queries */}
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
                  processQuery()
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

      {/* Language Tips */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-primary mt-0.5" />
            <div className="space-y-1">
              <p className="font-medium">Tips for better results</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Speak clearly and at a normal pace</li>
                <li>• Use commodity names like "aaloo", "pyaaz", "gehoo"</li>
                <li>• Ask about specific mandis for better accuracy</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
