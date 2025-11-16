import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: number;
}

interface ChatBubblesProps {
  messages: ChatMessage[];
  onDismiss?: (id: string) => void;
}

export function ChatBubbles({ messages, onDismiss }: ChatBubblesProps) {
  return (
    <div className="fixed top-24 right-24 flex flex-col gap-3 z-40 max-w-md">
      {messages.map(message => (
        <ChatBubble key={message.id} message={message} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

interface ChatBubbleProps {
  message: ChatMessage;
  onDismiss?: (id: string) => void;
}

function ChatBubble({ message, onDismiss }: ChatBubbleProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isPinned, setIsPinned] = useState(false);

  useEffect(() => {
    // Fade in animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto-dismiss user messages after 5 seconds if not pinned
    if (message.isUser && !isPinned) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => {
          onDismiss?.(message.id);
        }, 300); // Wait for fade-out animation
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [message.id, message.isUser, isPinned, onDismiss]);

  const handlePinToggle = () => {
    setIsPinned(!isPinned);
  };

  return (
    <div
      className={cn(
        "relative transition-all duration-300",
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
      )}
    >
      <div
        className={cn(
          "rounded-2xl shadow-card p-4 max-w-sm",
          message.isUser
            ? "bg-secondary text-primary-foreground ml-auto"
            : "bg-card text-card-foreground"
        )}
      >
        <div className="flex items-start gap-2">
          <p className="flex-1 text-sm leading-relaxed">{message.text}</p>
          {!message.isUser && (
            <button
              onClick={handlePinToggle}
              className={cn(
                "p-1 rounded-full hover:bg-accent/20 transition-colors",
                isPinned && "bg-accent/30"
              )}
              title={isPinned ? "Unpin" : "Pin"}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Tail for user messages */}
      {message.isUser && (
        <div className="absolute right-0 top-4 w-0 h-0 border-l-[12px] border-l-secondary border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent" />
      )}

      {/* Tail for Conficius messages */}
      {!message.isUser && (
        <div className="absolute left-0 top-4 w-0 h-0 border-r-[12px] border-r-card border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent" />
      )}
    </div>
  );
}
