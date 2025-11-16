import { useState, useRef, useCallback, useEffect } from "react";

interface UseVoiceRecordingReturn {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  isRecording: boolean;
  audioBlob: Blob | null;
  error: string | null;
}

/**
 * Hook for voice recording with Voice Activity Detection (VAD)
 * 
 * Features:
 * - Uses MediaRecorder API to capture audio
 * - Auto-stop on silence detection (750ms threshold)
 * - Proper cleanup of audio contexts and streams
 * - Comprehensive error handling
 * - Prevents race conditions and memory leaks
 * 
 * @returns Object containing recording functions and state
 */
export function useVoiceRecording(): UseVoiceRecordingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const vadCheckRef = useRef<number | null>(null);
  const lastSoundTimeRef = useRef<number>(Date.now());
  const vadActiveRef = useRef<boolean>(false);
  const recordingStartTimeRef = useRef<number>(0);
  const mimeTypeRef = useRef<string>("audio/webm");

  // VAD configuration
  const SILENCE_THRESHOLD_MS = 2000; // 2 seconds of silence to auto-stop (increased to prevent premature stops)
  const ANALYZE_INTERVAL_MS = 100; // Check audio level every 100ms
  const MAX_RECORDING_DURATION_MS = 60000; // 60 seconds max recording
  const MIN_RECORDING_DURATION_MS = 500; // Minimum 500ms to ensure audio is collected

  /**
   * Cleanup function to stop all recording resources
   */
  const cleanup = useCallback(() => {
    // Stop VAD check
    if (vadCheckRef.current !== null) {
      cancelAnimationFrame(vadCheckRef.current);
      vadCheckRef.current = null;
    }

    // Stop media recorder
    if (mediaRecorderRef.current) {
      try {
        if (mediaRecorderRef.current.state !== "inactive") {
          mediaRecorderRef.current.stop();
        }
      } catch (e) {
        console.warn("Error stopping media recorder:", e);
      }
      mediaRecorderRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {
        console.warn("Error closing audio context:", e);
      }
      audioContextRef.current = null;
      analyserRef.current = null;
    }

    // Stop media stream tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });
      streamRef.current = null;
    }

    vadActiveRef.current = false;
  }, []);

  /**
   * Start recording audio with VAD
   * 
   * @throws Error if microphone access is denied or recording fails
   */
  const startRecording = useCallback(async () => {
    // Prevent multiple simultaneous recordings
    if (isRecording || mediaRecorderRef.current) {
      console.warn("Recording already in progress");
      return;
    }

    try {
      setError(null);
      setAudioBlob(null);
      audioChunksRef.current = [];
      vadActiveRef.current = true;
      lastSoundTimeRef.current = Date.now();

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // Create MediaRecorder with fallback MIME types
      let mimeType = "audio/webm;codecs=opus";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/webm";
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = ""; // Use default
        }
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType as any,
      });

      mediaRecorderRef.current = mediaRecorder;
      mimeTypeRef.current = mimeType || "audio/webm";

      // Handle data availability
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording errors
      mediaRecorder.onerror = (event) => {
        console.error("MediaRecorder error:", event);
        setError("Recording error occurred");
        cleanup();
        setIsRecording(false);
      };

      // Handle recording stop
      const handleStop = () => {
        // Small delay to ensure all chunks are collected
        setTimeout(() => {
          const blob = new Blob(audioChunksRef.current, {
            type: mimeType || "audio/webm",
          });
          setAudioBlob(blob);
          setIsRecording(false);
          // Don't cleanup here if manually stopped - let stopRecording handle it
          if (!vadActiveRef.current) {
            cleanup();
          }
        }, 100);
      };

      mediaRecorder.onstop = handleStop;

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      const recordingStartTime = Date.now();
      recordingStartTimeRef.current = recordingStartTime;

      // Create audio context for VAD
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const analyser = audioContext.createAnalyser();
      analyserRef.current = analyser;
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;

      const microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      // VAD check function using requestAnimationFrame for better performance
      const checkAudioLevel = () => {
        if (!vadActiveRef.current || !mediaRecorderRef.current) {
          return;
        }

        // Check max recording duration
        if (Date.now() - recordingStartTime > MAX_RECORDING_DURATION_MS) {
          console.log("Max recording duration reached");
          vadActiveRef.current = false;
          if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
          }
          return;
        }

        try {
          analyser.getByteFrequencyData(dataArray);
          const average =
            dataArray.reduce((a, b) => a + b, 0) / dataArray.length;

          // If audio level is above threshold, reset silence timer
          if (average > 10) {
            // Threshold for detecting sound
            lastSoundTimeRef.current = Date.now();
          } else {
            // Check if silence duration exceeded threshold
            const silenceDuration = Date.now() - lastSoundTimeRef.current;
            if (silenceDuration > SILENCE_THRESHOLD_MS) {
              // Auto-stop on silence
              vadActiveRef.current = false;
              if (mediaRecorderRef.current) {
                mediaRecorderRef.current.stop();
              }
              return;
            }
          }

          vadCheckRef.current = requestAnimationFrame(checkAudioLevel);
        } catch (e) {
          console.error("VAD check error:", e);
          vadActiveRef.current = false;
        }
      };

      vadCheckRef.current = requestAnimationFrame(checkAudioLevel);
    } catch (err) {
      cleanup();
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to start recording. Please check microphone permissions.";
      setError(errorMessage);
      setIsRecording(false);
    }
  }, [cleanup]);

  /**
   * Internal function to stop recording and create blob
   */
  const stopRecordingInternal = useCallback((resolve: (blob: Blob | null) => void) => {
    // Stop VAD check first
    vadActiveRef.current = false;
    if (vadCheckRef.current !== null) {
      cancelAnimationFrame(vadCheckRef.current);
      vadCheckRef.current = null;
    }

    if (!mediaRecorderRef.current) {
      // Recording already stopped, try to create blob from existing chunks
      const blob = new Blob(audioChunksRef.current, {
        type: mimeTypeRef.current,
      });
      if (blob.size === 0) {
        console.warn("No media recorder and empty chunks");
        resolve(null);
      } else {
        resolve(blob);
      }
      return;
    }

    // Set up stop handler with timeout
    let stopTimeout: NodeJS.Timeout | null = null;
    let stopHandlerFired = false;
    
    const stopHandler = () => {
      if (stopHandlerFired) {
        return; // Prevent double execution
      }
      stopHandlerFired = true;
      
      if (stopTimeout) {
        clearTimeout(stopTimeout);
        stopTimeout = null;
      }

      // Wait a bit for all chunks to be collected
      setTimeout(() => {
        // Use the MIME type that was set during recording
        const blob = new Blob(audioChunksRef.current, {
          type: mimeTypeRef.current,
        });

        // Validate blob has content
        if (blob.size === 0) {
          console.warn("Recording produced empty blob, chunks:", audioChunksRef.current.length, "chunk sizes:", audioChunksRef.current.map(c => c.size));
          setAudioBlob(null);
          setIsRecording(false);
          cleanup();
          resolve(null);
          return;
        }

        console.log("Recording stopped successfully, blob size:", blob.size, "chunks:", audioChunksRef.current.length);
        setAudioBlob(blob);
        setIsRecording(false);
        cleanup();
        resolve(blob);
      }, 200); // Give time for final chunks to arrive
    };

    // Set up stop handler
    mediaRecorderRef.current.onstop = stopHandler;

    // Set timeout in case onstop doesn't fire
    stopTimeout = setTimeout(() => {
      console.warn("MediaRecorder stop timeout, creating blob from available chunks");
      stopHandler();
    }, 1000); // Increased timeout

    try {
      if (mediaRecorderRef.current.state !== "inactive") {
        // Request final data before stopping
        mediaRecorderRef.current.requestData();
        mediaRecorderRef.current.stop();
      } else {
        // Already stopped, try to get blob from chunks
        if (stopTimeout) {
          clearTimeout(stopTimeout);
        }
        stopHandler();
      }
    } catch (e) {
      if (stopTimeout) {
        clearTimeout(stopTimeout);
      }
      console.error("Error stopping recording:", e);
      // Try to create blob anyway
      stopHandler();
    }
  }, [cleanup]);

  /**
   * Stop recording and return the audio blob
   * 
   * @returns Promise resolving to audio Blob or null if recording failed
   */
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      // Check minimum recording duration
      const recordingDuration = Date.now() - recordingStartTimeRef.current;
      
      if (recordingDuration < MIN_RECORDING_DURATION_MS) {
        console.warn(`Recording too short (${recordingDuration}ms), waiting for minimum duration...`);
        // Wait a bit more to ensure data is collected
        setTimeout(() => {
          stopRecordingInternal(resolve);
        }, MIN_RECORDING_DURATION_MS - recordingDuration + 200);
        return;
      }

      stopRecordingInternal(resolve);
    });
  }, [stopRecordingInternal]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    startRecording,
    stopRecording,
    isRecording,
    audioBlob,
    error,
  };
}

