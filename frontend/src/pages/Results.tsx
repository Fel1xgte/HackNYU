import { useState, useEffect } from "react";
import { useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Download, ArrowLeft, Sparkles, Mic } from "lucide-react";
import confuciusAvatar from "@/assets/confucius-avatar.jpg";
import confuciusLogo from "@/assets/confucius-logo.png";
import heroBackground from "@/assets/hero-background-2.png";

const Results = () => {
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [processingStep, setProcessingStep] = useState("Starting...");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
          setVideoUrl("http://127.0.0.1:8000/get-video/");
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
  // Download handler
  // ----------------------------
  const handleDownload = async () => {
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

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: `url(${heroBackground})`,
        }}
      />
      <div className="absolute inset-0 bg-hero-gradient" />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Logo */}
        <div className="p-8 animate-fade-in">
          <Link to="/">
            <img
              src={confuciusLogo}
              alt="Confucius"
              className="h-20 w-auto hover:scale-110 transition-transform duration-300 cursor-pointer animate-glow"
            />
          </Link>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col px-36 pb-16">
          {/* Heading */}
          <div className="mb-12 animate-fade-in">
            <div className="relative inline-block">
              <h1 className="text-5xl md:text-6xl font-bold text-accent mb-4 relative z-10">
                Clarity for Your Lecture
              </h1>
              <div className="absolute inset-0 blur-2xl bg-accent/20 animate-pulse" />
            </div>
            <p className="text-xl text-primary-foreground mt-4 animate-slide-in-left animation-delay-200">
              <span className="font-semibold">Confucius</span> is here to
              explain, clarify, and help you learn.
            </p>
          </div>

          {/* Video Player */}
          <div className="w-full max-w-4xl animate-scale-in">
            <div className="relative group">
              {/* Decorative corners */}
              <div className="absolute -top-2 -left-2 w-8 h-8 border-t-4 border-l-4 border-accent rounded-tl-lg opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="absolute -top-2 -right-2 w-8 h-8 border-t-4 border-r-4 border-accent rounded-tr-lg opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="absolute -bottom-2 -left-2 w-8 h-8 border-b-4 border-l-4 border-accent rounded-bl-lg opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="absolute -bottom-2 -right-2 w-8 h-8 border-b-4 border-r-4 border-accent rounded-br-lg opacity-60 group-hover:opacity-100 transition-opacity" />

              {/* Glow */}
              <div className="absolute inset-0 bg-accent/10 rounded-lg blur-xl group-hover:bg-accent/20 transition-all duration-500" />

              <div className="relative bg-black rounded-lg overflow-hidden shadow-card aspect-video flex items-center justify-center border-2 border-accent/30">
                {isProcessing ? (
                  <div className="flex flex-col items-center gap-4">
                    <Sparkles className="w-12 h-12 text-accent animate-spin" />
                    <p className="text-primary-foreground text-lg">
                      {processingStep}
                    </p>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center gap-4">
                    <p className="text-red-500 text-lg">Error: {error}</p>
                    <Link to="/">
                      <Button>Try Again</Button>
                    </Link>
                  </div>
                ) : videoUrl ? (
                  <video controls className="w-full h-full" src={videoUrl}>
                    Your browser does not support the video tag.
                  </video>
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
          <div className="w-full max-w-4xl mt-12 relative flex items-center justify-between">
            {/* Download button aligned to left edge of video */}
            <div className="relative inline-flex">
              <div className="absolute inset-0 bg-secondary/30 rounded-full blur-xl group-hover:blur-2xl transition-all" />
              <Button
                size="lg"
                onClick={handleDownload}
                disabled={isProcessing || !videoUrl}
                className="relative bg-secondary hover:bg-secondary/90 text-primary-foreground px-10 py-4 text-lg rounded-full shadow-card hover:shadow-xl transition-all duration-300 hover:scale-105 overflow-hidden group disabled:opacity-50"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-foreground/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                <Download className="mr-2 h-5 w-5 relative z-10 group-hover:animate-bounce" />
                <span className="relative z-10">Download</span>
              </Button>
            </div>

            {/* Center text */}
            <p className="whitespace-nowrap text-sm md:text-base text-primary-foreground/80">
              <span className="italic">Confused?</span>{" "}
              Ask{" "}
              <span className="font-semibold">Confucius</span>
            </p>
          </div>

          {/* Upload another video (left under the row) */}
          <Link
            to="/"
            className="mt-6 text-accent hover:text-accent/80 flex items-center gap-2 transition-all duration-300 hover:gap-3 relative group"
          >
            <ArrowLeft className="h-14 w-8 group-hover:-translate-x-1 transition-transform" />
            <span className="relative">
              Upload another video
              <span className="absolute inset-x-0 -bottom-1 h-0.5 bg-accent scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </span>
          </Link>
        </div>

        {/* Confucius Avatar + Mic button */}
        <div className="fixed bottom-12 right-24 flex flex-col items-center gap-2 animate-fade-in animation-delay-500 group">
          <span className="text-accent font-semibold text-lg group-hover:scale-110 transition-transform">
            Confucius
          </span>
          <div className="relative">
            <img
              src={confuciusAvatar}
              alt="Confucius Avatar"
              className="w-64 h-auto rounded-2xl shadow-card group-hover:shadow-xl transition-all duration-300 group-hover:scale-105 relative z-10"
            />
            <div className="absolute inset-0 bg-accent/20 rounded-2xl blur-xl group-hover:bg-accent/40 transition-all duration-500" />
          </div>
          <div className="text-xs text-accent/60 italic">孔子</div>

          {/* Mic button centered under card */}
          <Button
            className="mt-4 w-20 h-20 rounded-full bg-accent text-primary-foreground shadow-card hover:shadow-xl hover:scale-110 transition-all duration-300 flex items-center justify-center"
          >
            <Mic
              className="text-primary-foreground"
              style={{ width: 30, height: 30 }}
            />
          </Button>
        </div>

        {/* Chinese Decorations */}
        <div className="absolute top-1/2 left-8 -translate-y-1/2 text-8xl font-bold text-accent/5 pointer-events-none select-none rotate-90 hidden lg:block">
          学习
        </div>
      </div>
    </div>
  );
};

export default Results;
