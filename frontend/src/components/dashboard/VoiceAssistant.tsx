
"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Mic, MicOff, Loader2, X } from "lucide-react"

export function VoiceAssistant() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [response, setResponse] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null)
  
  // VAD Refs
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const silenceStartRef = useRef<number | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  const stopPlayback = () => {
    if (audioPlayerRef.current) {
        audioPlayerRef.current.pause()
        audioPlayerRef.current.currentTime = 0
    }
  }

  const startRecording = async () => {
    try {
      stopPlayback() // Barge-in: Stop any playing audio
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Determine supported mime type
      let mimeType = 'audio/webm' 
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus'
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4' // Safari
      }
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      // VAD Setup
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)
      analyser.fftSize = 256
      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser

      const checkSilence = () => {
        analyser.getByteFrequencyData(dataArray)
        const sum = dataArray.reduce((a, b) => a + b, 0)
        const average = sum / bufferLength
        
        // Threshold for silence (adjustable)
        if (average < 10) { 
            if (silenceStartRef.current === null) {
                silenceStartRef.current = Date.now()
            } else if (Date.now() - silenceStartRef.current > 2500) { // 2.5 seconds of silence
                stopRecording()
                return // Stop loop
            }
        } else {
            silenceStartRef.current = null // Reset if sound detected
        }
        
        animationFrameRef.current = requestAnimationFrame(checkSilence)
      }
      
      checkSilence()

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
        if (audioContextRef.current) audioContextRef.current.close()
            
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        const ext = mimeType.includes('mp4') ? 'm4a' : 'webm'
        await handleAudioUpload(audioBlob, ext)
        
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setIsOpen(true)
      setTranscript(null)
      setResponse(null)
      silenceStartRef.current = Date.now() + 1000 // Give 1s grace period at start
      
    } catch (error) {
      console.error("Error accessing microphone:", error)
      alert("Could not access microphone. Please ensure permissions are granted.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const handleAudioUpload = async (audioBlob: Blob, ext: string = 'webm') => {
    try {
      const formData = new FormData()
      formData.append("file", audioBlob, `recording.${ext}`)
      formData.append("language", "hi-IN") 

      const res = await fetch("http://localhost:8000/api/v1/voice/query", {
        method: "POST",
        body: formData,
      })

      if (!res.ok) throw new Error("Voice query failed")

      const data = await res.json()
      setTranscript(data.query)
      setResponse(data.response)
      
      if (data.audio) {
        playAudio(data.audio)
      }
    } catch (error) {
      console.error("Error processing voice query:", error)
      setResponse("Sorry, I encountered an error processing your request.")
    } finally {
      setIsProcessing(false)
    }
  }
  
  const playAudio = (base64Audio: string) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = `data:audio/wav;base64,${base64Audio}`
      audioPlayerRef.current.play()
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-4">
      {isOpen && (
        <Card className="w-80 shadow-xl border-2 border-primary/20">
          <CardContent className="p-4 space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="font-semibold flex items-center gap-2">
                <Mic className="h-4 w-4 text-primary" />
                Kisan Sahayak
              </h3>
              <div className="flex gap-1">
                 {/* Close Button */}
                 <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => {
                     stopPlayback()
                     setIsOpen(false)
                 }}>
                    <X className="h-4 w-4" />
                 </Button>
              </div>
            </div>
            
            <div className="space-y-3">
               {isRecording && (
                <div className="flex flex-col items-center justify-center py-4 text-primary animate-pulse">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-2">
                        <Mic className="h-6 w-6" />
                    </div>
                    <p className="text-sm font-medium">Listening... (Auto-stop in 2.5s)</p>
                </div>
               )}

               {isProcessing && (
                <div className="flex flex-col items-center justify-center py-4 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mb-2" />
                    <p className="text-sm">Processing...</p>
                </div>
               )}

               {!isRecording && !isProcessing && (transcript || response) && (
                   <div className="space-y-3 text-sm max-h-60 overflow-y-auto">
                       {transcript && (
                           <div className="bg-muted p-2 rounded-lg">
                               <p className="font-medium text-xs text-muted-foreground mb-1">You said:</p>
                               <p>{transcript}</p>
                           </div>
                       )}
                       {response && (
                           <div className="bg-primary/5 p-2 rounded-lg border border-primary/10">
                               <p className="font-medium text-xs text-primary mb-1">Assistant:</p>
                               <p>{response}</p>
                           </div>
                       )}
                   </div>
               )}
            </div>
            
            <audio ref={audioPlayerRef} className="hidden" />
          </CardContent>
        </Card>
      )}

      <Button
        size="icon"
        variant={isRecording ? "destructive" : "default"}
        className={`h-14 w-14 rounded-full shadow-lg transition-all duration-300 ${isRecording ? "scale-110 ring-4 ring-destructive/30" : "hover:scale-105"}`}
        onClick={isRecording ? stopRecording : startRecording}
      >
        {isRecording ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
        <span className="sr-only">Voice Assistant</span>
      </Button>
    </div>
  )
}
