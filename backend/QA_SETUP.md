# QA Service Setup Guide

## Overview

The QA (Question & Answer) service is the highlight feature of Confucius. It allows users to ask questions about the lecture and get intelligent answers.

## Features

✅ **AI-Powered Answers** - Uses Google Gemini for intelligent, contextual responses  
✅ **Fallback Mode** - Works even without API keys using keyword matching  
✅ **Smart Search** - Advanced relevance scoring to find the best transcript segments  
✅ **Answer Caching** - Reduces API calls by caching answers for 1 hour  
✅ **Retry Logic** - Automatic retries with exponential backoff for reliability  
✅ **Robust Error Handling** - Graceful degradation when services are unavailable

## Setup

### Option 1: With Gemini API (Recommended)

1. Get a free Gemini API key:

   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Create a new API key

2. Create a `.env` file in the `backend/` directory:

   ```bash
   cd backend
   touch .env
   ```

3. Add your API key to `.env`:

   ```
   GEMINI_API_KEY=your-api-key-here
   ```

4. Restart the server:
   ```bash
   python server.py
   ```

### Option 2: Without API Key (Fallback Mode)

The service will automatically use keyword-based fallback answers when the API key is not configured. While not as intelligent as AI-powered answers, it still provides useful responses based on transcript matching.

## Verification

Check your setup status:

```bash
curl http://127.0.0.1:8000/api/qa/status
```

Or visit: http://127.0.0.1:8000/api/qa/status

## How It Works

1. **Question Processing**: User asks a question via voice or text
2. **Transcript Search**: Advanced algorithm finds relevant segments using:
   - Keyword matching
   - Time proximity scoring
   - Phrase matching
3. **Answer Generation**:
   - **Primary**: Gemini AI generates intelligent answer from context
   - **Fallback**: Keyword-based answer if API unavailable
4. **Caching**: Answers are cached to reduce API calls
5. **Response**: Returns answer with evidence segments

## Improvements Made

### 1. Better API Key Handling

- Helpful error messages when API key is missing
- Automatic fallback to keyword matching
- Status endpoint to check configuration

### 2. Improved Search Algorithm

- Relevance scoring based on:
  - Keyword matches (60% weight)
  - Time proximity (30% weight)
  - Phrase matches (10% weight)
- Expanded search window (60 seconds)
- Better segment ranking

### 3. Fallback Answer Generation

- Works without API keys
- Keyword-based matching
- Provides relevant transcript segments
- Helpful guidance messages

### 4. Answer Caching

- In-memory cache (1 hour TTL)
- Reduces API calls for repeated questions
- Faster response times

### 5. Retry Logic

- 3 retry attempts with exponential backoff
- Handles temporary API failures
- Graceful degradation

### 6. Better Error Handling

- User-friendly error messages
- Detailed logging for debugging
- Never fails completely - always provides some answer

## Troubleshooting

### "AI service is not configured"

- **Solution**: Set `GEMINI_API_KEY` in your `.env` file
- **Alternative**: Service will use fallback mode automatically

### "Empty response from Gemini"

- **Cause**: API quota exceeded or invalid key
- **Solution**: Check your API key and quota at https://makersuite.google.com/app/apikey
- **Fallback**: Service automatically uses keyword matching

### Answers not relevant

- **Cause**: Transcript might not contain the information
- **Solution**: The service will indicate when using general knowledge vs transcript-based answers

## API Endpoints

- `POST /api/qa` - Ask a question
- `GET /api/qa/status` - Check service status and configuration
- `GET /api/transcript` - Get the lecture transcript

## Example Usage

```python
import requests

# Ask a question
response = requests.post("http://127.0.0.1:8000/api/qa", json={
    "question": "What is flip flops?",
    "currentTime": 45.0
})

answer = response.json()
print(answer["answerText"])
```

## Performance

- **With API**: ~1-2 seconds per question
- **Fallback Mode**: <100ms per question
- **Cached Answers**: <10ms response time

## Future Enhancements

- [ ] Redis caching for distributed systems
- [ ] Multiple AI provider support (OpenAI, Anthropic)
- [ ] Semantic search using embeddings
- [ ] Answer quality scoring
- [ ] User feedback integration
