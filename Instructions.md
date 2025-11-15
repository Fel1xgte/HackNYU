Application Flow:-

User uploads video 
    ↓
Extract audio → Whisper API (transcription)
    ↓
GPT-4: Generate summary + slide content + timestamps
    ↓
Create visual slides (programmatically)
    ↓
ElevenLabs: Generate narration audio for each slide
    ↓
VIDEO GENERATION: Combine slides + audio into MP4
    ↓
User watches video
    ↓
[INTERRUPT MODE] User speaks question
    ↓
ElevenLabs Speech-to-Text → GPT-4 (answer) → ElevenLabs TTS
    ↓
Pause video → Answer plays → Resume video


TechStack:-
Frontend: React + Tailwind CSS
Backend: Python Flask/FastAPI (better for video processing)
Video Processing: FFmpeg + Moviepy
AI: OpenAI (Whisper + GPT-4)
Voice: ElevenLabs (STT + TTS)
Storage: AWS S3 / Cloudinary / Uploadthing
Hosting: Railway (backend) + Vercel (frontend)


Implementation Strategy: "Pause & Answer" System
Architecture:
Video playing → User says "pause" or clicks mic
    ↓
Video pauses + Recording starts
    ↓
ElevenLabs Speech-to-Text (audio → text)
    ↓
Question analysis:
  - What are they asking?
  - Is it about current slide or general?
  - Can we answer from transcript?
    ↓
GPT-4 generates answer (context: full transcript + current slide)
    ↓
ElevenLabs Text-to-Speech (answer → audio)
    ↓
Play answer audio
    ↓
Options:
  - Resume video
  - Jump to relevant timestamp
  - Rewatch current section

🎨 USER EXPERIENCE FLOW
Let me paint the picture of what judges will see:
Act 1: Upload (20 seconds)
👤 User uploads 10-minute lecture video
🖥️ "Analyzing your lecture... extracting key insights..."
⏳ Progress bar (transcription → summarization → slide generation)
Act 2: Video Generation (30 seconds)
🎬 "Generating your personalized video summary..."
⚡ Shows: "Creating slide 1 of 6... Synthesizing narration..."
✅ "Your 90-second summary is ready!"
Act 3: Video Playback (90 seconds)
▶️ Professional video plays:

Slide 1 appears with smooth transition
ElevenLabs voice narrates naturally
Visual: Title + 3 bullet points
Auto-advances to next slide

Act 4: Interactive Q&A (30 seconds) ⭐
👤 User clicks mic: "Wait, what's entropy again?"
⏸️ Video pauses
🎤 "I heard: 'What's entropy again?'"
🤖 GPT-4 analyzes context (current slide + full transcript)
🔊 ElevenLabs responds: "Great question! Entropy is..."
📍 Offers: "Want to jump to 6:32 where this was explained in detail?"
Act 5: Continue or Explore

User can resume video
Jump to specific timestamps
Ask follow-up questions
Download video/slides

# AI Video Lecture Summarizer - System Documentation

## Project Overview
Transform 10-minute educational videos into interactive 90-second summaries with AI-generated slides, natural voice narration, and voice-based Q&A. Students can pause and ask questions, receiving contextually-aware spoken answers.

---

## Core Pipeline

```
User uploads video → Extract audio → Whisper transcription → GPT-4 summarization 
→ Generate 6 slides (15 sec each) → ElevenLabs narration → Render video 
→ Interactive playback with voice Q&A
```

**Processing Time**: ~12-15 minutes for 10-minute video
**Cost**: $0.30-0.80 per video

---

## Key Components

### 1. Transcription (OpenAI Whisper)
- Extract audio with FFmpeg
- API: `POST /v1/audio/transcriptions`
- Cost: $0.006/minute
- Output: Timestamped transcript with segments

### 2. Summarization (GPT-4)
**Prompt Structure**:
```
Analyze this transcript and create a 90-second summary with:
- 6 slides (15 seconds each)
- Engaging narration scripts
- 2-3 bullet points per slide
- Original video timestamps
- Simple, conversational language

Output as JSON with: title, bullet_points, narration_script, timestamp
```

**Requirements**:
- Total script = exactly 90 seconds
- Include concrete examples
- Connect slides logically
- Focus on key concepts only

### 3. Audio Narration (ElevenLabs TTS)
- Convert each slide's script to speech
- Voice settings: stability 0.5, similarity_boost 0.75
- Use professional voices ("Adam", "Antoni")
- Add SSML for emphasis on key terms
- Generate 6 audio clips (~15 seconds each)

### 4. Video Generation (Choose One)

**OPTION A: Puppeteer + HTML** (RECOMMENDED)
- Create HTML slides with reveal.js
- Use headless Chrome to record screen
- Sync audio with slide transitions
- Rendering: 30-60 seconds
- **Pros**: Beautiful, animated, easy to debug
- **Cons**: Requires 500MB-1GB RAM

**OPTION B: FFmpeg Image Stitching** (FASTEST)
- Generate slides as PNG images
- Stitch with FFmpeg + audio overlay
- Rendering: 5-10 seconds
- **Pros**: Very fast, lightweight
- **Cons**: Static slides only

**OPTION C: Remotion** (React-Based)
- Build video with React components
- Programmatic animations
- **Pros**: Modern, flexible
- **Cons**: Learning curve, slower (2-3 min)

### 5. Interactive Voice Q&A

**Flow**:
```
User clicks mic → Record audio → Whisper STT → Extract question text
→ GPT-4 analyzes (with full transcript context) → Generate answer
→ ElevenLabs TTS → Play answer → Offer actions (resume/jump/rewatch)
```

**Question Types Handled**:
- **Clarification**: "Explain that again" → Rephrase current slide
- **Definition**: "What's entropy?" → Simple definition + example
- **Deep Dive**: "Why does this work?" → Detailed explanation
- **Navigation**: "Where was X discussed?" → Jump to timestamp
- **Connection**: "How does this relate to Y?" → Link concepts

**GPT-4 Q&A Prompt**:
```
You're a tutor helping a student. They paused at slide 3 and asked: "{question}"

Context:
- Current slide: {slide_content}
- Full transcript: {transcript}
- Timestamp: 0:45 / 1:30

Provide:
1. Answer (under 100 words, 15-20 seconds spoken)
2. Related timestamp from original lecture
3. Suggested action (resume/jump/rewatch)
4. Follow-up questions

Be conversational, encouraging, and clear.
```

---

## Technical Stack

**Frontend**: React, Tailwind CSS, Web Audio API, MediaRecorder API
**Backend**: Node.js/Express or Python/Flask
**Database**: PostgreSQL, Redis (queue)
**APIs**: OpenAI Whisper, GPT-4, ElevenLabs
**Processing**: FFmpeg, Puppeteer (or chosen method)
**Deployment**: Vercel (frontend), Railway/Render (backend), S3/Cloudinary (storage)

---

## API Endpoints

```
POST /videos/upload → Returns video_id, processing_estimate
GET /videos/{id}/status → Returns progress, current_step
GET /videos/{id}/result → Returns video_url, slides, transcript
POST /videos/{id}/ask → Send audio question → Returns answer + audio
```

---

## Database Schema (Minimal)

**videos**: id, filename, duration, status, transcript_json, summary_json, output_url, expires_at
**slides**: id, video_id, slide_number, title, content, narration_text, audio_url, timestamp
**qa_interactions**: id, video_id, timestamp, question, answer, audio_urls, user_action

---

## 24-Hour Hackathon Timeline

**Hours 0-6**: Setup, upload, Whisper integration, basic GPT-4 summarization
**Hours 6-12**: ElevenLabs TTS, slide generation, video rendering (choose method)
**Hours 12-18**: Voice Q&A implementation, video controls, UI polish
**Hours 18-22**: Integration, testing, error handling
**Hours 22-24**: Demo prep, practice pitch (10+ times!)

---

## Team Roles (3-4 People)

1. **Backend Lead**: Upload, APIs (Whisper, GPT-4), database, deployment
2. **AI Specialist**: Prompt engineering, ElevenLabs, Q&A logic, testing
3. **Frontend Lead**: React UI, video player, voice input, responsive design
4. **Integrator**: Connect pieces, video generation pipeline, debugging

---

## Error Handling

- Upload fails → Retry with progress indicator
- Transcription poor → Add disclaimer, continue
- Video generation fails → Return slides + audio as fallback
- Voice Q&A fails → Offer text input alternative
- Always: Try 3 times, then graceful error message

---

## Demo Strategy

**3-Minute Pitch**:
1. **Problem** (30s): "Students waste hours on lectures"
2. **Upload** (30s): Show 10-min video uploading
3. **Magic** (60s): Play generated 90-sec summary with professional slides
4. **Innovation** (45s): Pause, ask voice question, get spoken answer, jump to timestamp
5. **Close** (15s): "Learn faster. Powered by ElevenLabs."

**Demo Tips**:
- Use compelling sample (quantum physics, AI)
- Show time saved (10min → 90sec)
- Demonstrate voice Q&A LIVE (wow factor!)
- Have pre-recorded backup
- Emphasize ElevenLabs integration for prize

---

## Winning Features Priority

**MUST HAVE**:
1. Video transcription & summarization
2. Generated video with slides + narration
3. Voice Q&A (at least one question answered)

**SHOULD HAVE**:
4. Timestamp jumping
5. Multiple question types handled
6. Polished UI

**NICE TO HAVE**:
7. Multiple voice personalities
8. Download video
9. Custom durations

---

## Risk Mitigation

**High-risk** (must work): Transcription, basic summarization, audio generation
**Medium-risk** (have backup): Video generation (pre-render example), voice Q&A (text fallback)
**Low-priority** (skip if needed): Custom features, advanced animations

**Key Strategy**: Get basic pipeline working by Hour 12. Everything after is polish.

---

## Success Criteria

**Minimum**: Upload → 90-sec video → Play → Ask 1 question → Get answer
**Competitive**: + Multiple Q&A types + Timestamp jump + Polished UI
**Winning**: + Live demo + Technical depth + Clear market potential

---

## ElevenLabs Prize Optimization

- Use for narration AND Q&A responses
- Show voice quality vs generic TTS
- Demonstrate emotional variation
- Mention prominently in pitch
- Display API usage in technical explanation

---

## Quick Reference

**Video Generation Decision**:
- **Limited time?** → FFmpeg (fastest)
- **Want quality?** → Puppeteer (recommended)
- **React experts?** → Remotion

**Start with FFmpeg, upgrade to Puppeteer if time permits.**

---

This condensed version contains everything essential to build and demo successfully in 24 hours. Focus on the core pipeline first, add features incrementally, and practice your demo extensively. Good luck! 🚀