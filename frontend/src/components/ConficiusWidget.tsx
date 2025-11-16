import { useEffect, useRef } from "react";
import { Mic, Loader2 } from "lucide-react";
import confuciusAvatar from "@/assets/confucius-avatar.jpg";
import { cn } from "@/lib/utils";

type WidgetState = "idle" | "listening" | "processing" | "answering";

interface ConficiusWidgetProps {
  state: WidgetState;
  recordingDuration?: number;
  onMicClick: () => void;
}

export function ConficiusWidget({
  state,
  recordingDuration = 0,
  onMicClick,
}: ConficiusWidgetProps) {
  const avatarRef = useRef<HTMLImageElement>(null);

  // Format recording duration as MM:SS
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed bottom-12 right-24 flex flex-col items-center gap-2 z-50">
      {/* Name label */}
      <span
        className={cn(
          "text-accent font-semibold text-lg transition-transform duration-300",
          state === "listening" && "scale-110"
        )}
      >
        Confucius
      </span>

      {/* Avatar with state-based animations */}
      <div className="relative">
        <img
          ref={avatarRef}
          src={confuciusAvatar}
          alt="Confucius Avatar"
          className={cn(
            "w-64 h-auto rounded-2xl shadow-card transition-all duration-300 relative z-10",
            state === "listening" && "scale-105 animate-pulse",
            state === "answering" && "scale-105"
          )}
        />

        {/* Glow effect */}
        <div
          className={cn(
            "absolute inset-0 rounded-2xl blur-xl transition-all duration-500",
            state === "idle" && "bg-accent/20",
            state === "listening" && "bg-accent/40 animate-pulse",
            state === "processing" && "bg-accent/30",
            state === "answering" && "bg-accent/40"
          )}
        />

        {/* Pulsing ring for listening state */}
        {state === "listening" && (
          <>
            <div className="absolute inset-0 rounded-2xl border-4 border-accent animate-ping opacity-75" />
            <div className="absolute inset-0 rounded-2xl border-2 border-accent animate-pulse" />
          </>
        )}

        {/* Waveform visualization overlay for listening/answering */}
        {(state === "listening" || state === "answering") && (
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-accent/30 to-transparent rounded-b-2xl flex items-end justify-center gap-1 p-2">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-1 bg-accent rounded-full animate-pulse"
                style={{
                  height: `${20 + Math.random() * 30}%`,
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: "0.5s",
                }}
              />
            ))}
          </div>
        )}

        {/* Processing spinner overlay */}
        {state === "processing" && (
          <div className="absolute inset-0 bg-black/30 rounded-2xl flex items-center justify-center">
            <Loader2 className="w-12 h-12 text-accent animate-spin" />
          </div>
        )}
      </div>

      {/* Chinese text */}
      <div className="text-xs text-accent/60 italic">孔子</div>

      {/* Mic button */}
      <button
        onClick={onMicClick}
        className={cn(
          "mt-4 w-20 h-20 rounded-full bg-accent text-primary-foreground shadow-card hover:shadow-xl transition-all duration-300 flex items-center justify-center",
          state === "listening" && "animate-pulse scale-110",
          state === "processing" && "opacity-50 cursor-not-allowed",
          state === "answering" && "opacity-50 cursor-not-allowed"
        )}
        disabled={state === "processing" || state === "answering"}
      >
        {state === "processing" ? (
          <Loader2 className="w-8 h-8 animate-spin" />
        ) : (
          <Mic className="w-8 h-8" />
        )}
      </button>

      {/* Recording duration display */}
      {state === "listening" && recordingDuration > 0 && (
        <div className="mt-2 text-sm text-accent font-semibold">
          {formatDuration(recordingDuration)}
        </div>
      )}

      {/* State text */}
      {state === "processing" && (
        <div className="mt-2 text-sm text-accent font-semibold animate-pulse">
          Thinking...
        </div>
      )}
      {state === "answering" && (
        <div className="mt-2 text-sm text-accent font-semibold">
          Speaking...
        </div>
      )}
    </div>
  );
}
