import { useState, useEffect, useRef } from "react";
import { useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Download,
  ArrowLeft,
  Sparkles,
  Video,
  FileImage,
  ChevronDown,
  Loader2,
  Play,
  Pause,
} from "lucide-react";
import confuciusLogo from "@/assets/confucius-logo.png";
import heroBackground from "@/assets/hero-background-2.png";
import { useVoiceRecording } from "@/hooks/useVoiceRecording";
import { ConficiusWidget } from "@/components/ConficiusWidget";
import { ChatBubbles } from "@/components/ChatBubbles";

type WidgetState = "idle" | "listening" | "processing" | "answering";

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: number;
}

const Results = () => {
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [processingStep, setProcessingStep] = useState("Starting...");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoLoading, setVideoLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);

  // Voice Q&A state
  const [widgetState, setWidgetState] = useState<WidgetState>("idle");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState<string>("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false); // Prevent race conditions
  const recognitionRef = useRef<any>(null); // Web Speech API recognition instance

  const {
    startRecording,
    stopRecording,
    isRecording,
    audioBlob,
    error: recordingError,
  } = useVoiceRecording();

  // API timeout configuration
  const API_TIMEOUT_MS = 30000; // 30 seconds

  // Helper function to parse detailed status messages
  const getStatusMessage = (statusString: string): string => {
    const parts = statusString.split(":");
    const mainStatus = parts[0];
    const subStatus = parts[1];

    // Transcript generation
    if (mainStatus === "generating_slide_text") {
      if (subStatus === "loading_transcript")
        return "Loading transcript data...";
      if (subStatus === "calling_ai_model")
        return "Asking AI to generate slides... (30-60 sec)";
      if (subStatus === "saving_slides") return "Saving slide content...";
      return "Generating slide content... (Step 2/5)";
    }

    // Slide image generation
    if (mainStatus === "generating_slide_images") {
      if (subStatus?.startsWith("slide_")) {
        const match = subStatus.match(/slide_(\d+)_of_(\d+)/);
        if (match) {
          return `Creating slide image ${match[1]} of ${match[2]}... (Step 3/5)`;
        }
      }
      return "Creating slide images... (Step 3/5)";
    }

    // Audio generation
    if (mainStatus === "generating_audio") {
      if (subStatus?.startsWith("audio_")) {
        const match = subStatus.match(/audio_(\d+)_of_(\d+)/);
        if (match) {
          return `Synthesizing audio ${match[1]} of ${match[2]}... (Step 4/5)`;
        }
      }
      return "Synthesizing narration... (Step 4/5)";
    }

    // Video stitching
    if (mainStatus === "stitching_video") {
      if (subStatus?.startsWith("segment_")) {
        const match = subStatus.match(/segment_(\d+)/);
        if (match) {
          return `Stitching video segment ${match[1]}... (Step 5/5)`;
        }
      }
      if (subStatus === "merging_segments")
        return "Merging all segments... (Step 5/5)";
      return "Stitching final video... (Step 5/5)";
    }

    // Default mappings
    const defaultMessages: Record<string, string> = {
      initializing: "Setting up workspace...",
      decoding_video: "Extracting audio and frames... (Step 1/5)",
      complete: "Your video is ready!",
    };

    return defaultMessages[mainStatus] || "Processing...";
  };

  useEffect(() => {
    let intervalId: number;

    const pollStatus = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/get-video-status/");
        const data = await response.json();

        if (data.status === "complete") {
          setIsProcessing(false);
          const videoUrlWithTimestamp = `http://127.0.0.1:8000/get-video/?t=${Date.now()}`;
          setVideoUrl(videoUrlWithTimestamp);
          setVideoLoading(true);
          setVideoError(null);
          clearInterval(intervalId);
        } else if (data.status === "failed") {
          setIsProcessing(false);
          setError(data.detail || "Processing failed");
          clearInterval(intervalId);
        } else if (data.status === "processing") {
          setProcessingStep(getStatusMessage(data.step));
        }
      } catch (error) {
        setError("Failed to connect to server");
        setIsProcessing(false);
        clearInterval(intervalId);
      }
    };

    // Start polling every 3 seconds
    pollStatus();
    intervalId = window.setInterval(pollStatus, 3000);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, []);

  // ----------------------------
  // Download handlers
  // ----------------------------
  const handleDownloadVideo = async () => {
    if (!videoUrl) return;

    try {
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "confucius-lecture-summary.mp4";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
    }
  };

  const handleDownloadSlides = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/download-slides/");
      if (!response.ok) {
        throw new Error("Failed to download slides");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "confucius-lecture-slides.zip";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download slides failed:", error);
    }
  };

  // ----------------------------
  // Voice Q&A handlers
  // ----------------------------
  /**
   * Handle microphone button click with state machine logic
   * - Idle: Start recording and pause video
   * - Listening: Stop recording and process question
   * - Answering: Barge-in (interrupt TTS)
   */
  const handleMicClick = async () => {
    // Prevent race conditions
    if (isProcessingRef.current) {
      console.warn("Already processing a request");
      return;
    }

    try {
      if (widgetState === "idle") {
        // Start recording
        const video = videoRef.current;
        if (video && !video.paused) {
          video.pause();
        }

        // Initialize Web Speech API for live transcription
        if (
          "webkitSpeechRecognition" in window ||
          "SpeechRecognition" in window
        ) {
          const SpeechRecognition =
            (window as any).webkitSpeechRecognition ||
            (window as any).SpeechRecognition;
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = "en-US";

          recognition.onresult = (event: any) => {
            let interim = "";
            let final = "";

            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcript = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                final += transcript + " ";
              } else {
                interim += transcript;
              }
            }

            setLiveTranscript(final + interim);
          };

          recognition.onerror = (event: any) => {
            console.error("Speech recognition error:", event.error);
          };

          recognition.start();
          recognitionRef.current = recognition;
        }

        setLiveTranscript("");
        await startRecording();
        setWidgetState("listening");
        setRecordingDuration(0);

        // Start duration timer
        if (recordingIntervalRef.current) {
          clearInterval(recordingIntervalRef.current);
        }
        recordingIntervalRef.current = setInterval(() => {
          setRecordingDuration(prev => prev + 1);
        }, 1000);
      } else if (widgetState === "listening") {
        // Stop recording and process
        if (recordingIntervalRef.current) {
          clearInterval(recordingIntervalRef.current);
          recordingIntervalRef.current = null;
        }

        // Stop Web Speech API
        if (recognitionRef.current) {
          recognitionRef.current.stop();
          recognitionRef.current = null;
        }

        const blob = await stopRecording();
        if (blob && blob.size > 0) {
          await processQuestion(blob);
        } else {
          setWidgetState("idle");
          const errorMsg: ChatMessage = {
            id: `error-${Date.now()}`,
            text: "No audio was recorded. Please try again.",
            isUser: false,
            timestamp: Date.now(),
          };
          setChatMessages(prev => [...prev, errorMsg]);
        }
      } else if (widgetState === "answering") {
        // Barge-in: stop TTS and return to idle
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current.currentTime = 0;
          audioRef.current = null;
        }
        setWidgetState("idle");
      }
    } catch (err) {
      console.error("Mic click error:", err);
      setWidgetState("idle");
      setLiveTranscript("");
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
        recordingIntervalRef.current = null;
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    }
  };

  /**
   * Fetch with timeout wrapper
   */
  const fetchWithTimeout = async (
    url: string,
    options: RequestInit,
    timeoutMs: number = API_TIMEOUT_MS
  ): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof Error && err.name === "AbortError") {
        throw new Error("Request timeout. Please try again.");
      }
      throw err;
    }
  };

  /**
   * Process recorded audio through STT → QA → TTS pipeline
   *
   * @param audioBlob - Recorded audio blob
   */
  const processQuestion = async (audioBlob: Blob) => {
    // Prevent concurrent processing
    if (isProcessingRef.current) {
      return;
    }

    isProcessingRef.current = true;
    setWidgetState("processing");

    try {
      // Validate audio blob
      if (!audioBlob || audioBlob.size === 0) {
        throw new Error("Invalid audio recording");
      }

      // 1. STT: Convert audio to text
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const sttResponse = await fetchWithTimeout(
        "http://127.0.0.1:8000/api/stt",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!sttResponse.ok) {
        const errorData = await sttResponse.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `STT failed with status ${sttResponse.status}`
        );
      }

      const sttData = await sttResponse.json();
      const question = sttData.transcript?.trim();

      if (!question || question === "") {
        throw new Error("No speech detected in recording");
      }

      // Add user message to chat
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        text: question,
        isUser: true,
        timestamp: Date.now(),
      };
      setChatMessages(prev => [...prev, userMessage]);

      // 2. QA: Get answer
      const currentTime = Math.max(0, videoRef.current?.currentTime || 0);
      const qaResponse = await fetchWithTimeout(
        "http://127.0.0.1:8000/api/qa",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            currentTime,
          }),
        }
      );

      if (!qaResponse.ok) {
        const errorData = await qaResponse.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `QA failed with status ${qaResponse.status}`
        );
      }

      const qaData = await qaResponse.json();
      const { answerText, action, targetTime } = qaData;

      if (!answerText || answerText.trim() === "") {
        throw new Error("No answer received from server");
      }

      // Add Conficius message to chat
      const conficiusMessage: ChatMessage = {
        id: `conficius-${Date.now()}`,
        text: answerText,
        isUser: false,
        timestamp: Date.now(),
      };
      setChatMessages(prev => [...prev, conficiusMessage]);

      // 3. Handle video action
      if (videoRef.current) {
        const video = videoRef.current;
        if (action === "jump" && targetTime !== undefined) {
          const seekTime = Math.max(
            0,
            Math.min(targetTime - 0.5, video.duration || 0)
          );
          video.currentTime = seekTime;
        } else if (action === "rewatch" && targetTime !== undefined) {
          const seekTime = Math.max(
            0,
            Math.min(targetTime, video.duration || 0)
          );
          video.currentTime = seekTime;
        }
      }

      // 4. TTS: Generate and play audio
      setWidgetState("answering");
      const ttsResponse = await fetchWithTimeout(
        "http://127.0.0.1:8000/api/tts",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: answerText }),
        }
      );

      if (ttsResponse.ok) {
        const ttsData = await ttsResponse.json();
        const audioUrl = `http://127.0.0.1:8000${ttsData.audioUrl}`;

        // Play audio with error handling
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        // Set up event handlers before playing
        audio.onended = () => {
          setWidgetState("idle");
          audioRef.current = null;
          isProcessingRef.current = false;
          // DO NOT resume video - chat is still open, user can choose to watch or chat
          // Video will only play when chat is completely closed (idle + no messages)
        };

        audio.onerror = err => {
          console.error("Audio playback error:", err);
          setWidgetState("idle");
          audioRef.current = null;
          isProcessingRef.current = false;
        };

        try {
          await audio.play();
        } catch (playError) {
          console.error("Failed to play audio:", playError);
          setWidgetState("idle");
          audioRef.current = null;
          isProcessingRef.current = false;
        }
      } else {
        // TTS failed, just show text
        setWidgetState("idle");
        isProcessingRef.current = false;
      }
    } catch (err) {
      console.error("Q&A error:", err);
      setWidgetState("idle");
      isProcessingRef.current = false;

      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      const errorChatMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        text: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        isUser: false,
        timestamp: Date.now(),
      };
      setChatMessages(prev => [...prev, errorChatMessage]);
    }
  };

  const handleDismissMessage = (id: string) => {
    setChatMessages(prev => prev.filter(msg => msg.id !== id));
  };

  // Track if chat window is open (full window, not collapsed badge)
  const [isChatWindowOpen, setIsChatWindowOpen] = useState(false);

  // Pause video when chat window is open - user can either chat OR watch video, not both
  useEffect(() => {
    if (isChatWindowOpen && videoRef.current && !videoRef.current.paused) {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  }, [isChatWindowOpen]);

  const handleChatStateChange = (isOpen: boolean) => {
    setIsChatWindowOpen(isOpen);
  };

  // Toggle play/pause - but prevent playing if chat is open
  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    // Don't allow video to play if chat window is open
    if (isChatWindowOpen) {
      console.log("Cannot play video while chat is open. Close chat first.");
      return;
    }

    if (video.paused) {
      video.play().catch(err => {
        console.error("Failed to play video:", err);
      });
    } else {
      video.pause();
    }
  };

  // Handle recording errors
  useEffect(() => {
    if (recordingError) {
      setWidgetState("idle");
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        text: `Recording error: ${recordingError}`,
        isUser: false,
        timestamp: Date.now(),
      };
      setChatMessages(prev => [...prev, errorMsg]);
    }
  }, [recordingError]);

  // Handle video URL changes and ensure video loads
  useEffect(() => {
    if (videoUrl && videoRef.current) {
      const video = videoRef.current;
      setVideoLoading(true);
      setVideoError(null);

      // Force reload the video when URL changes
      // This ensures the video element picks up the new URL
      video.load();
    }
  }, [videoUrl]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      isProcessingRef.current = false;
    };
  }, []);

  return (
    <div className="h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center blur-sm opacity-50"
        style={{
          backgroundImage: `url(${heroBackground})`,
        }}
      />
      <div className="absolute inset-0 bg-hero-gradient" />

      {/* Content */}
      <div className="relative z-10 h-screen flex flex-col overflow-hidden">
        {/* Logo */}
        <div className="p-4 md:p-6 animate-fade-in flex-shrink-0">
          <Link to="/">
            <img
              src={confuciusLogo}
              alt="Confucius"
              className="h-12 md:h-16 w-auto hover:scale-110 transition-transform duration-300 cursor-pointer"
              loading="eager"
            />
          </Link>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col px-4 md:px-8 lg:px-16 xl:px-24 pb-12 md:pb-16 overflow-hidden">
          {/* Heading */}
          <div className="mb-4 md:mb-6 animate-fade-in flex-shrink-0">
            <div className="relative inline-block">
              <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-accent mb-2 relative z-10 font-body-elegant text-on-gradient">
                Clarity for Your Lecture
              </h1>
            </div>
            <p className="text-base md:text-lg text-primary-foreground/95 mt-2 animate-slide-in-left animation-delay-200 font-body text-on-gradient-light">
              <span className="font-semibold font-body-elegant">Confucius</span>{" "}
              is here to explain, clarify, and help you learn.
            </p>
          </div>

          {/* Video Player */}
          <div className="w-full max-w-4xl animate-scale-in mb-4 flex-1 flex flex-col">
            <div className="relative group">
              {/* Glow - reduced */}
              <div className="absolute inset-0 bg-accent/3 rounded-lg blur-md group-hover:bg-accent/8 transition-all duration-500" />

              <div className="relative bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 rounded-lg shadow-card aspect-video flex items-center justify-center border-2 border-accent/30 backdrop-blur-sm">
                {isProcessing ? (
                  <div className="flex flex-col items-center gap-6 p-8">
                    {/* Animated loading dots */}
                    <div className="flex gap-2">
                      <div
                        className="w-3 h-3 bg-accent rounded-full animate-bounce"
                        style={{ animationDelay: "0s" }}
                      />
                      <div
                        className="w-3 h-3 bg-accent rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      />
                      <div
                        className="w-3 h-3 bg-accent rounded-full animate-bounce"
                        style={{ animationDelay: "0.4s" }}
                      />
                    </div>
                    {/* Sparkles icon */}
                    <div className="relative">
                      <Sparkles className="w-16 h-16 text-accent animate-spin relative z-10" />
                    </div>
                    {/* Processing step text */}
                    <div
                      className="text-center"
                      role="status"
                      aria-live="polite"
                    >
                      <p className="text-primary-foreground text-xl font-semibold font-body mb-2">
                        {processingStep}
                      </p>
                      <div className="w-64 h-1 bg-accent/20 rounded-full overflow-hidden mt-4">
                        <div
                          className="h-full bg-accent rounded-full animate-pulse"
                          style={{ width: "60%" }}
                        />
                      </div>
                    </div>
                  </div>
                ) : error ? (
                  <div
                    className="flex flex-col items-center gap-4"
                    role="alert"
                    aria-live="assertive"
                  >
                    <p className="text-red-500 text-lg">Error: {error}</p>
                    <Link to="/">
                      <Button aria-label="Try uploading again">
                        Try Again
                      </Button>
                    </Link>
                  </div>
                ) : videoUrl ? (
                  <div className="w-full h-full relative">
                    {videoLoading && (
                      <div className="absolute inset-0 flex items-center justify-center bg-primary/20 z-10">
                        <Loader2 className="w-8 h-8 text-accent animate-spin" />
                      </div>
                    )}
                    {videoError ? (
                      <div className="flex flex-col items-center justify-center h-full gap-4 p-8">
                        <p className="text-red-500 text-lg font-semibold">
                          Video playback error
                        </p>
                        <p className="text-primary-foreground/70 text-sm">
                          {videoError}
                        </p>
                        <Button
                          onClick={() => {
                            setVideoError(null);
                            setVideoLoading(true);
                            if (videoRef.current) {
                              // Force reload with new timestamp
                              const newUrl = `http://127.0.0.1:8000/get-video/?t=${Date.now()}`;
                              setVideoUrl(newUrl);
                              videoRef.current.load();
                            }
                          }}
                          variant="outline"
                        >
                          Retry
                        </Button>
                      </div>
                    ) : (
                      <video
                        ref={videoRef}
                        controls
                        controlsList=""
                        preload="auto"
                        playsInline
                        className="w-full h-full object-contain rounded-lg"
                        src={videoUrl}
                        style={{ maxHeight: "100%" }}
                        onLoadStart={() => {
                          setVideoLoading(true);
                          setVideoError(null);
                        }}
                        onLoadedData={() => {
                          setVideoLoading(false);
                          setVideoError(null);
                        }}
                        onLoadedMetadata={() => {
                          setVideoLoading(false);
                          setVideoError(null);
                        }}
                        onCanPlay={() => {
                          setVideoLoading(false);
                          setVideoError(null);
                        }}
                        onCanPlayThrough={() => {
                          setVideoLoading(false);
                          setVideoError(null);
                        }}
                        onError={e => {
                          console.error("Video error:", e);
                          setVideoLoading(false);
                          const video = videoRef.current;
                          let errorMessage = "Failed to load video.";

                          if (video) {
                            const error = video.error;
                            if (error) {
                              switch (error.code) {
                                case error.MEDIA_ERR_ABORTED:
                                  errorMessage = "Video loading was aborted.";
                                  break;
                                case error.MEDIA_ERR_NETWORK:
                                  errorMessage =
                                    "Network error while loading video.";
                                  break;
                                case error.MEDIA_ERR_DECODE:
                                  errorMessage = "Video decoding error.";
                                  break;
                                case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                                  errorMessage = "Video format not supported.";
                                  break;
                                default:
                                  errorMessage =
                                    "Unknown video error occurred.";
                              }
                            }
                          }
                          setVideoError(errorMessage);
                        }}
                        onWaiting={() => {
                          setVideoLoading(true);
                        }}
                        onPlaying={() => {
                          setVideoLoading(false);
                          // Only set playing if chat window is not open
                          if (!isChatWindowOpen) {
                            setIsPlaying(true);
                          } else {
                            // Chat window is open, pause video immediately
                            if (videoRef.current) {
                              videoRef.current.pause();
                            }
                          }
                        }}
                        onPlay={() => {
                          // Prevent video from playing if chat window is open
                          if (isChatWindowOpen) {
                            if (videoRef.current) {
                              videoRef.current.pause();
                            }
                            setIsPlaying(false);
                            return;
                          }
                          setIsPlaying(true);
                        }}
                        onPause={() => {
                          setIsPlaying(false);
                        }}
                        onEnded={() => {
                          setIsPlaying(false);
                        }}
                      >
                        Your browser does not support the video tag.
                      </video>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <div className="w-24 h-24 rounded-full bg-primary-foreground flex items-center justify-center hover:scale-110 transition-transform cursor-pointer">
                      <div className="w-0 h-0 border-l-[20px] border-l-primary border-y-[12px] border-y-transparent ml-2" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Row under video: Download left, text centered */}
          <div className="w-full max-w-4xl mt-4 pb-6 md:pb-8 relative flex items-center justify-between flex-shrink-0">
            {/* Download dropdown aligned to left edge of video */}
            <div className="relative inline-flex">
              <div className="absolute inset-0 bg-accent/10 rounded-full blur-md group-hover:blur-lg transition-all" />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="default"
                    disabled={isProcessing || !videoUrl}
                    className="relative bg-accent hover:bg-accent/90 text-primary-foreground px-6 py-2 text-base rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 disabled:opacity-50 border border-accent/60 hover:border-accent"
                    aria-label="Download options"
                  >
                    <Download className="mr-2 h-5 w-5" />
                    Download
                    <ChevronDown className="ml-2 h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="start"
                  className="w-56 bg-card/98 backdrop-blur-sm border border-accent/30 shadow-xl"
                >
                  <DropdownMenuItem
                    onClick={handleDownloadVideo}
                    disabled={isProcessing || !videoUrl}
                    className="cursor-pointer focus:bg-accent/20 focus:text-accent-foreground"
                    aria-label="Download video file"
                  >
                    <Video className="mr-2 h-4 w-4" />
                    <span>Download as Video</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={handleDownloadSlides}
                    disabled={isProcessing}
                    className="cursor-pointer focus:bg-accent/20 focus:text-accent-foreground"
                    aria-label="Download slides as ZIP"
                  >
                    <FileImage className="mr-2 h-4 w-4" />
                    <span>Download as Slides</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Center text */}
            <p className="whitespace-nowrap text-sm md:text-base text-primary-foreground/90 font-medium">
              <span className="italic">Confused?</span> Ask{" "}
              <span className="font-semibold font-body-elegant">Confucius</span>
            </p>
          </div>

          {/* Upload another video (left under the row) */}
          <Link
            to="/"
            className="mt-4 mb-8 md:mb-12 text-accent hover:text-accent/80 flex items-center gap-2 transition-all duration-300 hover:gap-3 relative group text-sm md:text-base flex-shrink-0"
          >
            <ArrowLeft className="h-4 w-4 group-hover:-translate-x-1 transition-transform" />
            <span className="relative">
              Upload another video
              <span className="absolute inset-x-0 -bottom-1 h-0.5 bg-accent scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </span>
          </Link>
        </div>

        {/* Chat Bubbles */}
        {!isProcessing &&
          (widgetState !== "idle" || chatMessages.length > 0) && (
            <ChatBubbles
              messages={chatMessages}
              onDismiss={handleDismissMessage}
              widgetState={widgetState}
              isVideoPlaying={isPlaying}
              liveTranscript={liveTranscript}
              onChatStateChange={handleChatStateChange}
            />
          )}

        {/* Conficius Widget */}
        {!isProcessing && (
          <ConficiusWidget
            state={widgetState}
            recordingDuration={recordingDuration}
            onMicClick={handleMicClick}
          />
        )}

        {/* Chinese Decorations */}
        <div className="absolute top-1/2 left-4 md:left-8 -translate-y-1/2 text-4xl md:text-8xl font-bold text-accent/5 pointer-events-none select-none rotate-90 hidden md:block">
          学习
        </div>
      </div>
    </div>
  );
};

export default Results;
