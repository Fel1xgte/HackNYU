import { useState, useEffect } from "react";
import { useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Download, ArrowLeft, Sparkles } from "lucide-react";
import confuciusAvatar from "@/assets/confucius-avatar.jpg";
import confuciusLogo from "@/assets/confucius-logo.png";
import heroBackground from "@/assets/hero-background-2.png";

const Results = () => {
  const location = useLocation();
  const videoUrl = location.state?.videoUrl;
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsProcessing(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleDownload = () => {
    if (!videoUrl) return;
    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = "lecture.mp4";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <div className="mb-12 animate-fade-in">
            <div className="relative inline-block">
              <h1 className="text-5xl md:text-6xl font-bold text-accent mb-4 relative z-10">
                Clarity for Your Lecture
              </h1>
              <div className="absolute inset-0 blur-2xl bg-accent/20 animate-pulse" />
            </div>
            <p className="text-xl text-primary-foreground mt-4 animate-slide-in-left animation-delay-200">
              <span className="font-semibold">Confucius</span> is here to explain, clarify, and help you learn.
            </p>
          </div>

          {/* Video Player */}
          <div className="w-full max-w-4xl mb-8 animate-scale-in">
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
                    <p className="text-primary-foreground text-lg">Processing your lecture...</p>
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

          {/* ⭐ CENTERED BUTTONS UNDER VIDEO ⭐ */}
          <div className="w-full flex flex-col items-center mt-4 gap-6">

            {/* Download Button */}
            <div className="relative animate-slide-in-right">
              <div className="absolute inset-0 bg-secondary/30 rounded-full blur-xl group-hover:blur-2xl transition-all" />
              <Button
                size="lg"
                onClick={handleDownload}
                disabled={isProcessing || !videoUrl}
                className="relative bg-secondary hover:bg-secondary/90 text-primary-foreground px-12 py-6 text-lg rounded-full shadow-card hover:shadow-xl transition-all duration-300 hover:scale-105 overflow-hidden group disabled:opacity-50"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-foreground/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                <Download className="mr-2 h-5 w-5 relative z-10 group-hover:animate-bounce" />
                <span className="relative z-10">Download</span>
              </Button>
            </div>

            {/* Back Link */}
            <Link
              to="/"
              className="text-accent hover:text-accent/80 flex items-center gap-2 transition-all duration-300 hover:gap-3 relative group"
            >
              <ArrowLeft className="h-4 w-4 group-hover:-translate-x-1 transition-transform" />
              <span className="relative">
                Upload another video
                <span className="absolute inset-x-0 -bottom-1 h-0.5 bg-accent scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
              </span>
            </Link>
          </div>
        </div>

        {/* Confucius Avatar */}
        <div className="fixed bottom-8 right-24 flex flex-col items-center gap-2 animate-fade-in animation-delay-500 group cursor-pointer">
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
