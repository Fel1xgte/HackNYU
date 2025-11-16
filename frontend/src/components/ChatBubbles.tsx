import { useEffect, useState, useRef } from "react";
import { X, Mic, Loader2, Volume2, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import confuciusLogo from "@/assets/confucius-logo.png";

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: number;
}

interface ChatBubblesProps {
  messages: ChatMessage[];
  onDismiss?: (id: string) => void;
  widgetState?: "idle" | "listening" | "processing" | "answering";
  isVideoPlaying?: boolean;
  liveTranscript?: string;
  onChatStateChange?: (isOpen: boolean) => void; // Notify parent when chat opens/closes
}

export function ChatBubbles({
  messages,
  onDismiss,
  widgetState = "idle",
  isVideoPlaying = false,
  liveTranscript = "",
  onChatStateChange,
}: ChatBubblesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const isUserScrollingRef = useRef(false); // Track if user is actively scrolling
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-expand chat bubbles when user is speaking or AI is interacting
  useEffect(() => {
    if (
      widgetState === "listening" ||
      widgetState === "processing" ||
      widgetState === "answering"
    ) {
      setIsCollapsed(false);
    }
  }, [widgetState]);

  // Notify parent when chat open/closed state changes
  useEffect(() => {
    if (onChatStateChange) {
      // Chat window is "open" (full window visible, not collapsed badge) when:
      // - Not collapsed AND chat is visible (has messages OR active interaction)
      // When collapsed (showing badge), chat is "closed" - video can play
      // When expanded (full window), chat is "open" - video must pause
      const isChatVisible = widgetState !== "idle" || messages.length > 0;
      const isOpen = !isCollapsed && isChatVisible;
      onChatStateChange(isOpen);
    }
  }, [isCollapsed, messages.length, widgetState, onChatStateChange]);

  // Auto-scroll to bottom when new messages arrive (only if auto-scroll is enabled)
  useEffect(() => {
    // Don't auto-scroll if user is actively scrolling
    if (!shouldAutoScroll || isUserScrollingRef.current) {
      return;
    }

    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      ) as HTMLElement;
      if (scrollContainer) {
        // Use instant scroll for new messages (smooth can fight with user input)
        // Only use smooth when agent starts speaking/thinking
        const isNewMessage = messages.length > 0;
        scrollContainer.scrollTo({
          top: scrollContainer.scrollHeight,
          behavior: isNewMessage ? "instant" : "smooth",
        });
      }
    }
  }, [messages.length, shouldAutoScroll]); // Only depend on message count, not full messages array

  // Auto-scroll to user's live transcript when they're speaking
  useEffect(() => {
    // When user is speaking (listening state), always scroll to show their words
    if (widgetState === "listening" && liveTranscript) {
      // Small delay to ensure DOM is updated
      const timeoutId = setTimeout(() => {
        if (scrollRef.current) {
          const scrollContainer = scrollRef.current.querySelector(
            "[data-radix-scroll-area-viewport]"
          ) as HTMLElement;
          if (scrollContainer) {
            // Smooth scroll to bottom to show user's live transcript
            scrollContainer.scrollTo({
              top: scrollContainer.scrollHeight,
              behavior: "smooth",
            });
            // Re-enable auto-scroll when user is speaking (they want to see their words)
            setShouldAutoScroll(true);
          }
        }
      }, 50);

      return () => clearTimeout(timeoutId);
    }
  }, [liveTranscript, widgetState]); // Scroll when live transcript updates

  // Re-enable auto-scroll when agent starts speaking/thinking (but respect user scroll)
  useEffect(() => {
    // When agent starts processing or answering, check if user is near bottom
    // If yes, enable auto-scroll; if no, keep it disabled
    if (widgetState === "processing" || widgetState === "answering") {
      // Small delay to ensure DOM is ready
      const checkScroll = setTimeout(() => {
        if (scrollRef.current) {
          const scrollContainer = scrollRef.current.querySelector(
            "[data-radix-scroll-area-viewport]"
          ) as HTMLElement;
          if (scrollContainer) {
            const isNearBottom =
              scrollContainer.scrollHeight -
                scrollContainer.scrollTop -
                scrollContainer.clientHeight <=
              100; // 100px threshold
            if (isNearBottom) {
              setShouldAutoScroll(true);
              // Smooth scroll to bottom when agent starts responding
              scrollContainer.scrollTo({
                top: scrollContainer.scrollHeight,
                behavior: "smooth",
              });
            }
          }
        }
      }, 50);

      return () => clearTimeout(checkScroll);
    }
  }, [widgetState]);

  // Click outside to collapse (but NOT during active interactions)
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Don't collapse during active interactions
      if (
        widgetState === "listening" ||
        widgetState === "processing" ||
        widgetState === "answering"
      ) {
        return;
      }

      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node) &&
        messages.length > 0 &&
        !isCollapsed
      ) {
        setIsCollapsed(true);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [messages.length, isCollapsed, widgetState]);

  // Attach scroll listener to detect user manual scrolling (single source of truth)
  useEffect(() => {
    if (!scrollRef.current) return;

    const scrollContainer = scrollRef.current.querySelector(
      "[data-radix-scroll-area-viewport]"
    ) as HTMLElement;

    if (!scrollContainer) {
      // Retry after a short delay if container not ready
      const timeoutId = setTimeout(() => {
        // Re-run effect by checking again
        if (scrollRef.current) {
          const retryContainer = scrollRef.current.querySelector(
            "[data-radix-scroll-area-viewport]"
          ) as HTMLElement;
          if (retryContainer) {
            // Container is now available, but we'll let the effect re-run naturally
            // This is a fallback - the main logic handles it
          }
        }
      }, 100);
      return () => clearTimeout(timeoutId);
    }

    const handleScrollEvent = () => {
      // Mark that user is actively scrolling
      isUserScrollingRef.current = true;

      // Clear any existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // After user stops scrolling for 150ms, check position
      scrollTimeoutRef.current = setTimeout(() => {
        isUserScrollingRef.current = false;

        const isAtBottom =
          scrollContainer.scrollHeight -
            scrollContainer.scrollTop -
            scrollContainer.clientHeight <=
          50; // 50px threshold for "at bottom"

        // Update auto-scroll state based on scroll position
        // If user scrolls up, disable auto-scroll
        // If user scrolls back to bottom, re-enable auto-scroll
        setShouldAutoScroll(isAtBottom);
      }, 150);
    };

    scrollContainer.addEventListener("scroll", handleScrollEvent, {
      passive: true,
    });
    scrollContainer.addEventListener("wheel", handleScrollEvent, {
      passive: true,
    });

    return () => {
      scrollContainer.removeEventListener("scroll", handleScrollEvent);
      scrollContainer.removeEventListener("wheel", handleScrollEvent);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [messages.length]); // Re-attach when messages change (container might re-render)

  // Initial scroll to bottom when chat opens with messages or expands from collapsed
  useEffect(() => {
    if (messages.length > 0 && !isCollapsed && scrollRef.current) {
      // Small delay to ensure DOM is ready
      const timeoutId = setTimeout(() => {
        const scrollContainer = scrollRef.current?.querySelector(
          "[data-radix-scroll-area-viewport]"
        ) as HTMLElement;
        if (scrollContainer) {
          // Instant scroll to bottom on initial load or when expanding
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
          setShouldAutoScroll(true); // Re-enable auto-scroll when expanding
        }
      }, 50);

      return () => clearTimeout(timeoutId);
    }
  }, [isCollapsed, messages.length]); // Run when collapsed state changes or messages load

  // Handle scroll capture (fallback for React synthetic events)
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    // This is handled by the useEffect scroll listener above
    // Keeping as fallback but it should rarely be needed
  };

  // Keep chat visible during ALL interactions (listening, processing, answering)
  // Only hide when idle AND video playing AND no messages
  const shouldShowChat =
    widgetState !== "idle" || messages.length > 0 || !isVideoPlaying;

  if (!shouldShowChat) {
    return null;
  }

  // Show collapsed badge when messages exist and collapsed (but NOT during interactions)
  if (
    isCollapsed &&
    messages.length > 0 &&
    widgetState === "idle" // Only show collapsed badge when idle
  ) {
    return (
      <div
        className="fixed bottom-24 md:bottom-28 right-4 md:right-6 z-40 animate-fade-in"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <button
          onClick={() => setIsCollapsed(false)}
          className="bg-gradient-to-br from-gray-900/98 via-gray-800/98 to-gray-900/98 backdrop-blur-xl rounded-full shadow-2xl border-2 border-accent/40 px-3 py-2 flex items-center gap-1.5 hover:scale-105 transition-all duration-200 hover:border-accent/60"
          aria-label={`Open chat with ${messages.length} messages`}
        >
          <MessageCircle className="w-4 h-4 text-accent" />
          <span className="text-sm font-semibold text-white tabular-nums">
            {messages.length}
          </span>
        </button>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="fixed bottom-24 md:bottom-32 left-1/2 -translate-x-1/2 w-[90%] max-w-3xl z-40 animate-fade-in"
    >
      <div className="bg-gradient-to-br from-gray-900/98 via-gray-800/98 to-gray-900/98 backdrop-blur-xl rounded-3xl shadow-2xl border-2 border-accent/40 overflow-hidden transition-all duration-300">
        {/* Header with state indicator */}
        <div className="px-6 py-3 border-b border-accent/30 bg-gray-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8 border-2 border-accent/50">
              <AvatarImage src={confuciusLogo} alt="Confucius" />
              <AvatarFallback className="bg-accent/20 text-accent text-xs font-bold">
                C
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-bold font-body-elegant text-white">
                Confucius
              </p>
              <StateIndicator state={widgetState} />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <Badge
                variant="secondary"
                className="text-xs bg-gray-700/80 text-gray-200 border-gray-600"
              >
                {messages.length}{" "}
                {messages.length === 1 ? "message" : "messages"}
              </Badge>
            )}
            {messages.length > 0 && (
              <button
                onClick={() => setIsCollapsed(true)}
                className="text-gray-400 hover:text-white transition-colors p-1 rounded-full hover:bg-gray-700/50"
                aria-label="Minimize chat"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Messages area */}
        <ScrollArea
          ref={scrollRef}
          className="h-[300px] md:h-[350px]"
          onScrollCapture={handleScroll}
        >
          <div className="p-4 md:p-6 space-y-4">
            {messages.length === 0 && widgetState === "idle" && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <Mic className="w-12 h-12 text-accent/60 mb-4" />
                <p className="text-gray-200 text-sm font-medium">
                  Ask Confucius anything about the lecture
                </p>
                <p className="text-gray-400 text-xs mt-2">
                  Click the microphone to start speaking
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <ChatBubble
                key={message.id}
                message={message}
                onDismiss={onDismiss}
                isLatest={index === messages.length - 1}
              />
            ))}

            {/* Live transcript while listening */}
            {widgetState === "listening" && liveTranscript && (
              <LiveTranscriptBubble transcript={liveTranscript} />
            )}

            {/* Typing indicator */}
            {widgetState === "processing" && <TypingIndicator />}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

// State indicator component
function StateIndicator({ state }: { state: string }) {
  if (state === "listening") {
    return (
      <div className="flex items-center gap-1.5">
        <Mic className="w-3 h-3 text-red-500 animate-pulse" />
        <span className="text-xs text-red-500 font-medium">Listening...</span>
      </div>
    );
  }

  if (state === "processing") {
    return (
      <div className="flex items-center gap-1.5">
        <Loader2 className="w-3 h-3 text-accent animate-spin" />
        <span className="text-xs text-accent font-medium">Thinking...</span>
      </div>
    );
  }

  if (state === "answering") {
    return (
      <div className="flex items-center gap-1.5">
        <Volume2 className="w-3 h-3 text-accent animate-pulse" />
        <span className="text-xs text-accent font-medium">Speaking...</span>
      </div>
    );
  }

  return (
    <span className="text-xs font-medium text-white/40">Ready to help</span>
  );
}

// Typing indicator component
function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <Avatar className="h-9 w-9 border-2 border-accent/50 flex-shrink-0">
        <AvatarImage src={confuciusLogo} alt="Confucius" />
        <AvatarFallback className="bg-accent/20 text-accent text-xs font-bold">
          C
        </AvatarFallback>
      </Avatar>
      <div className="bg-gray-700/90 rounded-2xl rounded-tl-sm px-6 py-4 border border-accent/30 shadow-md">
        <div className="flex gap-1.5">
          <div
            className="w-2 h-2 bg-accent rounded-full animate-bounce"
            style={{ animationDelay: "0s" }}
          />
          <div
            className="w-2 h-2 bg-accent rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          />
          <div
            className="w-2 h-2 bg-accent rounded-full animate-bounce"
            style={{ animationDelay: "0.4s" }}
          />
        </div>
      </div>
    </div>
  );
}

// Live transcript bubble component
function LiveTranscriptBubble({ transcript }: { transcript: string }) {
  return (
    <div className="flex items-start gap-3 animate-fade-in flex-row-reverse">
      <Avatar className="h-9 w-9 border-2 border-secondary/50 bg-secondary/20 flex-shrink-0">
        <AvatarFallback className="bg-secondary text-primary-foreground text-sm font-bold">
          You
        </AvatarFallback>
      </Avatar>
      <div className="flex flex-col gap-1.5 max-w-[75%] items-end">
        <div className="rounded-2xl px-4 py-3 shadow-lg border-2 backdrop-blur-sm bg-gradient-to-br from-secondary/95 to-secondary/85 text-white border-secondary/70 rounded-tr-sm animate-pulse">
          <p className="text-sm leading-relaxed font-body">
            {transcript || "Listening..."}
          </p>
        </div>
        <Badge
          variant="outline"
          className="text-[10px] px-2 py-0 h-5 bg-gray-800/60 border-gray-600/40 text-gray-300"
        >
          Speaking...
        </Badge>
      </div>
    </div>
  );
}

interface ChatBubbleProps {
  message: ChatMessage;
  onDismiss?: (id: string) => void;
  isLatest?: boolean;
}

function ChatBubble({ message, onDismiss, isLatest }: ChatBubbleProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Fade in animation
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  const getRelativeTime = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 10) return "just now";
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 transition-all duration-500",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        message.isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <Avatar
        className={cn(
          "h-9 w-9 flex-shrink-0 border-2",
          message.isUser
            ? "border-secondary/50 bg-secondary/20"
            : "border-accent/50"
        )}
      >
        {message.isUser ? (
          <AvatarFallback className="bg-secondary text-primary-foreground text-sm font-bold">
            You
          </AvatarFallback>
        ) : (
          <>
            <AvatarImage src={confuciusLogo} alt="Confucius" />
            <AvatarFallback className="bg-accent/20 text-accent text-xs font-bold">
              C
            </AvatarFallback>
          </>
        )}
      </Avatar>

      {/* Message content */}
      <div
        className={cn(
          "flex flex-col gap-1.5 max-w-[75%]",
          message.isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-lg border-2 backdrop-blur-sm transition-all duration-300",
            message.isUser
              ? "bg-gradient-to-br from-secondary/95 to-secondary/85 text-white border-secondary/70 rounded-tr-sm"
              : "bg-gradient-to-br from-gray-700/95 to-gray-800/95 text-gray-100 border-accent/40 rounded-tl-sm",
            isLatest &&
              "ring-2 ring-accent/40 ring-offset-2 ring-offset-transparent"
          )}
        >
          <p className="text-sm leading-relaxed font-body">{message.text}</p>
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            "flex items-center gap-2",
            message.isUser ? "flex-row-reverse" : "flex-row"
          )}
        >
          <Badge
            variant="outline"
            className="text-[10px] px-2 py-0 h-5 bg-gray-800/60 border-gray-600/40 text-gray-300"
          >
            {getRelativeTime(message.timestamp)}
          </Badge>
        </div>
      </div>
    </div>
  );
}
