import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Upload, ImageIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import confuciusLogo from "@/assets/confucius-logo.png";
import heroBackground from "@/assets/hero-background.jpg";

const Index = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type === "video/mp4") {
        setSelectedFile(file);
        toast({
          title: "Video selected",
          description: "Ready to process your lecture",
        });
      } else {
        toast({
          title: "Invalid file type",
          description: "Please upload an MP4 video file.",
          variant: "destructive",
        });
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === "video/mp4") {
        setSelectedFile(file);
        toast({
          title: "Video selected",
          description: "Ready to process your lecture",
        });
      } else {
        toast({
          title: "Invalid file type",
          description: "Please upload an MP4 video file.",
          variant: "destructive",
        });
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("http://127.0.0.1:8000/process-video/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload video");
      }

      const data = await response.json();

      toast({
        title: "Upload successful",
        description: "Your video is being processed...",
      });

      navigate("/results");
    } catch (error) {
      toast({
        title: "Upload failed",
        description:
          error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
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
      <div className="relative z-10 min-h-screen flex flex-col pt-8 pb-28">
        {/* Logo */}
        <div className="p-8 animate-fade-in">
          <img
            src={confuciusLogo}
            alt="Confucius"
            className="h-20 w-auto hover:scale-110 transition-transform duration-300 cursor-pointer animate-glow"
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col lg:flex-row items-center justify-between px-8 md:px-16 lg:px-24 gap-12">
          {/* Left Side - Text */}
          <div className="flex-1 max-w-xl animate-slide-in-left">
            <div className="relative">
              <h1 className="text-5xl md:text-7xl font-bold text-primary-foreground mb-6 leading-tight">
                Clear Confusions
                <br />
                with{" "}
                <span className="relative inline-block">
                  <span className="text-accent relative z-10">Confucius</span>
                  <span className="absolute inset-0 blur-xl bg-accent/30 animate-glow" />
                </span>
              </h1>
              <p className="text-xl md:text-2xl text-primary-foreground/90 leading-relaxed">
                An AI tutor that turns your lecture videos
                <br />
                into simple and clear summaries.
              </p>
              <div className="mt-8 flex gap-4">
                <div
                  className="h-1 w-24 bg-accent rounded-full animate-shimmer"
                  style={{
                    background:
                      "linear-gradient(90deg, transparent, hsl(var(--accent)), transparent)",
                    backgroundSize: "200% 100%",
                  }}
                />
                <div className="h-1 w-16 bg-accent/60 rounded-full" />
                <div className="h-1 w-8 bg-accent/30 rounded-full" />
              </div>
            </div>
          </div>

          {/* Right Side - Upload Card */}
          <div className="flex-1 flex justify-center items-center animate-slide-in-right">
            <div className="relative group">
              {/* Glow effect */}
              <div className="absolute inset-0 bg-accent/20 rounded-3xl blur-2xl group-hover:bg-accent/30 transition-all duration-500" />

              <div className="relative bg-card/95 backdrop-blur-sm rounded-3xl p-12 shadow-card w-full max-w-md border-2 border-accent/20 hover:border-accent/40 transition-all duration-300">
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-4 border-dashed rounded-2xl p-12 transition-all duration-300 ${
                    isDragging
                      ? "border-primary bg-primary/10 scale-105"
                      : "border-[var(--upload-border)] bg-transparent hover:border-primary/50 hover:scale-102"
                  }`}
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="relative mb-4">
                      <ImageIcon className="w-16 h-16 text-primary relative z-10 hover:scale-110 transition-transform duration-300" />
                      <div className="absolute inset-0 blur-xl bg-primary/30 animate-pulse" />
                    </div>
                    <h2 className="text-xl font-semibold mb-2">
                      Drag & Drop{" "}
                      <span className="text-primary">MP4 Video</span>
                    </h2>
                    <p className="text-sm text-muted-foreground mb-4">
                      or{" "}
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-primary underline hover:text-primary/80 transition-colors relative group/btn"
                      >
                        browse file
                        <span className="absolute inset-x-0 -bottom-1 h-0.5 bg-primary scale-x-0 group-hover/btn:scale-x-100 transition-transform origin-left" />
                      </button>{" "}
                      on your computer
                    </p>
                    {selectedFile && (
                      <div className="text-sm text-primary font-medium mb-4 px-4 py-2 bg-primary/10 rounded-full animate-scale-in border border-primary/20">
                        ✓ {selectedFile.name}
                      </div>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/mp4"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>

                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile}
                  size="lg"
                  className="w-full mt-8 bg-secondary hover:bg-secondary/90 text-primary-foreground text-lg py-6 rounded-full shadow-lg disabled:opacity-50 relative overflow-hidden group/upload transition-all duration-300 hover:scale-105 hover:shadow-xl"
                >
                  <span className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-foreground/10 to-transparent translate-x-[-100%] group-hover/upload:translate-x-[100%] transition-transform duration-1000" />
                  <Upload className="mr-2 h-5 w-5 relative z-10" />
                  <span className="relative z-10">Upload</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
