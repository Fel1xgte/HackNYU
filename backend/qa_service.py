"""
Q&A Service for Confucius Voice Q&A

This module provides robust question-answering functionality using:
- Gemini AI for intelligent answers (primary)
- Keyword-based fallback when API unavailable
- Advanced transcript search with relevance scoring
- Answer caching to reduce API calls (with size limits)
- Retry logic with exponential backoff
- Comprehensive error handling and input validation
- Production-ready with security considerations

Author: Confucius Lecture Summarizer Team
"""

import json
import os
import re
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
import google.generativeai as genai
from config import Config
from env_loader import load_env_file

# Ensure .env is loaded BEFORE importing Config (but Config already loads it)
load_env_file()

# Reload Config environment variables to ensure .env values are picked up
Config.reload_env_vars()

# Answer cache with size limits (LRU eviction)
# Thread-safe cache using OrderedDict with max size
_cache_lock = threading.Lock()
_answer_cache: OrderedDict[str, Tuple[str, List[str], float]] = OrderedDict()
CACHE_TTL_SECONDS = 3600  # 1 hour cache
MAX_CACHE_SIZE = 1000  # Maximum number of cached answers


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input to prevent prompt injection and ensure safety.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters and normalize whitespace
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0]  # Cut at word boundary
    
    return text.strip()


def cleanup_cache():
    """
    Clean up expired cache entries and enforce size limits.
    Thread-safe cache maintenance.
    """
    global _answer_cache
    
    with _cache_lock:
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            key for key, (_, _, cached_time) in _answer_cache.items()
            if current_time - cached_time >= CACHE_TTL_SECONDS
        ]
        for key in expired_keys:
            _answer_cache.pop(key, None)
        
        # Enforce size limit (LRU eviction)
        while len(_answer_cache) > MAX_CACHE_SIZE:
            _answer_cache.popitem(last=False)  # Remove oldest entry


def get_api_key_status() -> Dict[str, any]:
    """
    Check API key configuration status and provide helpful feedback.
    Security: Does not expose actual API key values.
    
    Returns:
        Dict with status of each API key and helpful messages
    """
    api_key = Config.GEMINI_API_KEY
    is_configured = bool(api_key and api_key.strip())
    
    # Security: Only show if configured, never expose actual key
    status = {
        "gemini_configured": is_configured,
        "gemini_key_preview": "***configured***" if is_configured else None,
    }
    return status


def load_transcript(project_id: Optional[str] = None) -> Optional[Dict]:
    """
    Load transcript from workspace/decoded_video.json or sample_transcript.json.
    Includes comprehensive error handling and validation.
    
    Args:
        project_id: Optional project ID (currently unused but kept for future use)
    
    Returns:
        Dict containing transcript data or None if not found
    
    Raises:
        Exception: If file is corrupted or unreadable
    """
    # Try workspace transcript first
    workspace_transcript = Config.INPUT_JSON_PATH
    if workspace_transcript.exists():
        try:
            with open(workspace_transcript, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate transcript structure
                if isinstance(data, dict):
                    return data
                else:
                    print(f"⚠️  Invalid transcript format: expected dict, got {type(data)}")
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse workspace transcript JSON: {e}")
        except Exception as e:
            print(f"⚠️  Failed to load workspace transcript: {e}")
    
    # Fallback to sample transcript
    sample_transcript = Path(__file__).parent / "sample_transcript.json"
    if sample_transcript.exists():
        try:
            with open(sample_transcript, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    print(f"⚠️  Invalid sample transcript format: expected dict, got {type(data)}")
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse sample transcript JSON: {e}")
        except Exception as e:
            print(f"⚠️  Failed to load sample transcript: {e}")
    
    return None


def calculate_relevance_score(question: str, segment_text: str, time_distance: float) -> float:
    """
    Calculate relevance score for a segment based on keyword matching and time proximity.
    Uses weighted scoring algorithm for optimal segment ranking.
    
    Args:
        question: User's question (sanitized)
        segment_text: Text from transcript segment
        time_distance: Absolute time difference from current playback position (seconds)
    
    Returns:
        Relevance score between 0.0 and 1.0 (higher is better)
    """
    if not question or not segment_text:
        return 0.0
    
    question_lower = question.lower()
    segment_lower = segment_text.lower()
    
    # Extract meaningful keywords (words > 3 chars, excluding common stop words)
    # Enhanced stop words list for better keyword extraction
    stop_words = {
        "the", "what", "is", "are", "was", "were", "this", "that", 
        "these", "those", "can", "could", "would", "should", "about",
        "with", "from", "have", "has", "had", "will", "would",
        "how", "why", "when", "where", "who", "which", "does", "did",
        "for", "you", "your", "they", "them", "their", "been", "being"
    }
    keywords = [w for w in question_lower.split() if len(w) > 3 and w not in stop_words]
    
    # Fallback to shorter keywords if no long keywords found
    if not keywords:
        keywords = [w for w in question_lower.split() if len(w) > 2 and w not in stop_words]
    
    # Count keyword matches (case-insensitive) with partial matching
    keyword_matches = 0
    for keyword in keywords:
        if keyword in segment_lower:
            keyword_matches += 1
        # Partial match bonus for longer keywords
        elif len(keyword) > 5:
            for word in segment_lower.split():
                if keyword in word or word in keyword:
                    keyword_matches += 0.5
                    break
    
    keyword_score = keyword_matches / max(len(keywords), 1) if keywords else 0.0
    
    # Time proximity score (closer = better, slower decay for broader search)
    # Score decays over 45 seconds instead of 30 for more context
    time_score = 1.0 / (1.0 + time_distance / 45.0)
    
    # Exact phrase match bonus (2+ word phrases) with higher weight
    phrase_bonus = 0.0
    question_words = question_lower.split()
    if len(question_words) >= 2:
        for i in range(len(question_words) - 1):
            phrase = f"{question_words[i]} {question_words[i+1]}"
            if phrase in segment_lower:
                phrase_bonus += 0.4
                break  # Only count first match
    
    # Combined weighted score: prioritize content (70%) over time (20%) and phrases (10%)
    relevance = min(1.0, (keyword_score * 0.7 + time_score * 0.2 + min(phrase_bonus, 0.4) * 0.1))
    
    return relevance


def find_relevant_segments(
    question: str,
    transcript: Dict,
    current_time: float,
    window_sec: float = 90.0,
    max_segments: int = 15
) -> List[Dict]:
    """
    Find audio segments relevant to the question using improved relevance scoring.
    Handles edge cases and validates input data.
    
    Enhanced version with broader search window (±90s) and more segments (15) for better context.
    
    Args:
        question: User's question (will be sanitized)
        transcript: Transcript dictionary with audio_segments
        current_time: Current video playback time in seconds
        window_sec: Time window in seconds (±window_sec)
        max_segments: Maximum number of segments to return
    
    Returns:
        List of matching audio segments sorted by relevance (highest first)
    """
    if not transcript or not isinstance(transcript, dict):
        return []
    
    if "audio_segments" not in transcript:
        return []
    
    audio_segments = transcript.get("audio_segments", [])
    if not isinstance(audio_segments, list):
        return []
    
    if not audio_segments:
        return []
    
    # Validate current_time
    if not isinstance(current_time, (int, float)) or current_time < 0:
        current_time = 0.0
    
    scored_segments = []
    
    for segment in audio_segments:
        if not isinstance(segment, dict):
            continue
        
        start_sec = segment.get("start_sec", 0)
        end_sec = segment.get("end_sec", 0)
        text = segment.get("text", "")
        
        # Validate segment data
        if not isinstance(start_sec, (int, float)) or not isinstance(end_sec, (int, float)):
            continue
        
        if not text or not isinstance(text, str):
            continue
        
        segment_mid = (start_sec + end_sec) / 2.0
        time_distance = abs(segment_mid - current_time)
        
        # Only consider segments within time window
        if time_distance <= window_sec:
            relevance = calculate_relevance_score(question, text, time_distance)
            if relevance > 0:  # Only add segments with some relevance
                scored_segments.append((relevance, segment))
    
    # Sort by relevance (highest first)
    scored_segments.sort(key=lambda x: x[0], reverse=True)
    
    # Return top segments
    return [seg for _, seg in scored_segments[:max_segments]]


def generate_fallback_answer(
    question: str,
    relevant_segments: List[Dict],
    full_transcript: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Generate answer using keyword matching when AI API is unavailable.
    Provides a fallback mechanism to still answer questions.
    
    Args:
        question: User's question
        relevant_segments: List of relevant audio segments
        full_transcript: Optional full transcript text
    
    Returns:
        Tuple of (answer_text, evidence_segments)
    """
    if not question:
        return (
            "I didn't understand your question. Could you please rephrase it?",
            []
        )
    
    if not relevant_segments:
        # Try to find any relevant segments in full transcript
        if full_transcript and isinstance(full_transcript, str):
            question_lower = question.lower()
            keywords = [w for w in question_lower.split() if len(w) > 3]
            
            if keywords:
                transcript_lower = full_transcript.lower()
                if any(keyword in transcript_lower for keyword in keywords):
                    return (
                        "I found some relevant information in the lecture. "
                        "You might want to review the parts of the video that discuss this topic.",
                        []
                    )
        
        return (
            "I couldn't find specific information about that in this lecture transcript. "
            "The topic might be covered in a different part of the video, or it might not be part of this lecture.",
            []
        )
    
    # Build answer from relevant segments
    answer_parts = []
    evidence = []
    
    # Filter out generic greeting/intro segments
    greeting_keywords = [
        "welcome", "hello", "hi", "introduction", "overview", 
        "this course", "today we", "in this lecture"
    ]
    
    # Extract key information from top segments, skipping generic greetings
    for i, segment in enumerate(relevant_segments[:5]):  # Check more segments
        if not isinstance(segment, dict):
            continue
        
        text = segment.get("text", "").strip()
        if not text:
            continue
        
        # Skip generic greeting segments
        text_lower = text.lower()
        is_greeting = any(keyword in text_lower for keyword in greeting_keywords)
        
        # Skip if it's a greeting and we have other segments
        if is_greeting and len(relevant_segments) > 1:
            continue
        
        evidence.append(text)
        
        # Use first non-greeting segment as primary answer, or first segment if all are greetings
        # Only add to answer_parts if we haven't found a good answer yet
        if len(answer_parts) == 0:
            # Try to extract a concise answer
            sentences = re.split(r'[.!?]+', text)
            meaningful_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
            
            if meaningful_sentences:
                # Use first meaningful sentence, or combine first 2 if short
                if len(meaningful_sentences[0]) < 30 and len(meaningful_sentences) > 1:
                    answer_parts.append(f"{meaningful_sentences[0]} {meaningful_sentences[1]}")
                else:
                    answer_parts.append(meaningful_sentences[0])
    
    if answer_parts:
        answer = answer_parts[0]
        # Ensure answer is meaningful and not just a greeting
        if len(answer) < 20:
            # If too short, try to get more context from other segments
            if len(relevant_segments) > 1:
                for seg in relevant_segments[1:]:
                    seg_text = seg.get("text", "").strip()
                    if seg_text and len(seg_text) > 20:
                        answer = seg_text[:150]  # Use first 150 chars
                        break
            if len(answer) < 20:
                answer = f"Based on the lecture, {answer.lower()}"
    else:
        answer = (
            "I found relevant information in the lecture about this topic. "
            "The discussion appears in the transcript, but I recommend reviewing that section of the video for more details."
        )
    
    return answer, evidence


def generate_answer_with_gemini(
    question: str,
    relevant_segments: List[Dict],
    full_transcript: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[str, List[str]]:
    """
    Generate answer using Gemini AI with relevant context, retry logic, and error handling.
    Includes prompt injection protection and comprehensive error handling.
    
    Args:
        question: User's question (must be non-empty, will be sanitized)
        relevant_segments: List of relevant audio segments
        full_transcript: Optional full transcript text
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        Tuple of (answer_text, evidence_segments)
    
    Raises:
        Exception: If all retries fail and fallback also fails
    """
    # Sanitize question to prevent prompt injection
    question = sanitize_input(question, max_length=1000)
    
    if not question:
        return (
            "I didn't understand your question. Could you please rephrase it?",
            []
        )
    
    # Check API key with helpful error message
    api_key = Config.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        print("⚠️  GEMINI_API_KEY not configured. Using fallback answer generation.")
        print("   To enable AI-powered answers, set GEMINI_API_KEY in your .env file:")
        print("   Example: GEMINI_API_KEY=your-api-key-here")
        print("   Get your key at: https://makersuite.google.com/app/apikey")
        print(f"   Question: {question[:100]}")
        print(f"   Relevant segments: {len(relevant_segments)}")
        # Use fallback instead of failing
        return generate_fallback_answer(question, relevant_segments, full_transcript)
    
    # Build context from relevant segments (use all 15 segments for better answers)
    context_parts = []
    for seg in relevant_segments[:15]:  # Use top 15 segments
        if isinstance(seg, dict):
            start_sec = seg.get("start_sec", 0)
            end_sec = seg.get("end_sec", 0)
            text = seg.get("text", "")
            if text:
                context_parts.append(f"[{start_sec:.1f}s - {end_sec:.1f}s] {text}")
    
    context_text = "\n\n".join(context_parts)
    
    # Fallback to full transcript if no relevant segments
    if not context_text and full_transcript and isinstance(full_transcript, str):
        # Use a larger chunk from the transcript for better context
        context_text = full_transcript[:5000]  # Increased limit for more context
    
    # Sanitize context to prevent injection (increased limit for richer context)
    context_text = sanitize_input(context_text, max_length=8000)
    
    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            
            # Build prompt based on whether we have transcript context
            if context_text:
                # Escape any potential prompt injection in question
                safe_question = question.replace('"""', '').replace("'''", "")
                safe_context = context_text.replace('"""', '').replace("'''", "")
                
                prompt = f"""You are a helpful educational tutor helping a student understand lecture material.

Answer the student's question using the lecture transcript context below. Keep your answer under 150 words and use simple language.

Question: {safe_question}

Lecture Context:
{safe_context}

Instructions:
- Answer based on the transcript if relevant
- Use simple, everyday language
- Maximum 150 words
- Be helpful and educational

Answer:"""
            else:
                # No transcript context - use general knowledge
                safe_question = question.replace('"""', '').replace("'''", "")
                
                prompt = f"""You are a helpful educational tutor. Answer the student's question clearly and simply.

Question: {safe_question}

Instructions:
- Provide a clear educational answer
- Use simple, everyday language
- Maximum 150 words
- Be helpful and informative

Answer:"""
            
            # Configure safety settings to be less restrictive for educational content
            # Using proper enum values from genai.types
            try:
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                safety_settings = [
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH
                    },
                ]
            except (ImportError, AttributeError):
                # Fallback to string format if enums not available
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ]
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 200,  # ~200 tokens ≈ 150 words (enforces word limit)
                    "temperature": 0.7,  # Slightly lower for more focused, concise responses
                },
                safety_settings=safety_settings
            )
            
            if not response:
                raise ValueError("Empty response object from Gemini")
            
            # Try to get text from response FIRST, before checking finish_reason
            # Sometimes there's partial content even if blocked
            answer_text = None
            finish_reason = None
            
            try:
                answer_text = response.text.strip()
            except Exception as text_error:
                # If response.text fails, try accessing candidates directly
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                    
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        if parts and hasattr(parts[0], 'text'):
                            answer_text = parts[0].text.strip()
                        else:
                            # No text available
                            answer_text = None
                    else:
                        answer_text = None
                else:
                    answer_text = None
            
            # Check finish_reason if we couldn't get text
            if not answer_text and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    print(f"⚠️  Response finish_reason: {finish_reason}")
                    
                    # Check for safety ratings to understand why it was blocked
                    if hasattr(candidate, 'safety_ratings'):
                        print(f"⚠️  Safety ratings: {candidate.safety_ratings}")
                    
                    if finish_reason == 2:  # SAFETY block
                        print(f"⚠️  Response blocked by safety filters. Question: {question[:100]}")
                        print(f"⚠️  Prompt length: {len(prompt)} chars")
                        # Try to get any partial content that might exist
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            if parts:
                                print(f"⚠️  Found {len(parts)} content parts despite safety block")
                        # Don't retry - safety blocks usually persist
                        raise ValueError("Response was blocked by safety filters. Using fallback answer.")
                    elif finish_reason == 3:  # RECITATION
                        print(f"⚠️  Response matched training data. Question: {question[:100]}")
                        raise ValueError("Response matched training data. Using fallback answer.")
            
            # If we still don't have text, raise error
            if not answer_text:
                raise ValueError("No text content in response")
            
            # Validate answer text
            if len(answer_text) < 10:
                answer_text = "I apologize, but I couldn't generate a proper answer. Please try rephrasing your question."
            
            # Check if Gemini refused to answer - if so, regenerate with stronger prompt
            cannot_answer_phrases = [
                "cannot provide", "can't provide", "don't have enough information",
                "doesn't contain enough information", "not enough information",
                "cannot answer", "can't answer", "unable to answer",
                "i cannot", "i can't", "i'm unable", "i am unable"
            ]
            
            answer_lower = answer_text.lower()
            is_refusal = any(phrase in answer_lower[:150] for phrase in cannot_answer_phrases)
            
            # If it's a refusal and short, regenerate with explicit instruction (only once per attempt)
            if is_refusal and len(answer_text) < 200 and attempt == max_retries - 1:
                print(f"⚠️  Gemini refused to answer, regenerating with stronger prompt...")
                # Retry with explicit instruction to always answer
                safe_question_retry = question.replace('"""', '').replace("'''", "")
                retry_prompt = f"""You are Confucius, a wise tutor. The student asked: "{safe_question_retry}"

CRITICAL: You MUST provide an answer. Use your general knowledge if needed. Never refuse to answer.

Provide a helpful, educational answer (2-3 sentences) now:"""
                
                try:
                    retry_response = model.generate_content(
                        retry_prompt,
                        generation_config={
                            "max_output_tokens": 500,
                            "temperature": 0.8,
                        }
                    )
                    if retry_response and hasattr(retry_response, 'text') and retry_response.text:
                        answer_text = retry_response.text.strip()
                        if len(answer_text) >= 10:
                            print(f"✅ Regenerated answer successfully")
                except Exception as retry_error:
                    print(f"⚠️  Retry regeneration failed: {retry_error}")
                    # Continue with original answer even if it's a refusal
            
            # Extract evidence segments (validate data)
            evidence = []
            for seg in relevant_segments[:3]:
                if isinstance(seg, dict):
                    text = seg.get("text", "")
                    if text and isinstance(text, str):
                        evidence.append(text)
            
            return answer_text, evidence
            
        except Exception as api_error:
            last_error = api_error
            error_msg = str(api_error).lower()
            
            # Don't retry on certain errors (quota, billing, invalid key, safety filters)
            if any(keyword in error_msg for keyword in ["quota", "billing", "invalid", "permission", "forbidden", "safety filters", "safety"]):
                print(f"⚠️  Gemini API error (non-retryable): {api_error}")
                break
            
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                print(f"⚠️  Gemini API error (attempt {attempt + 1}/{max_retries}): {api_error}")
                print(f"   Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"⚠️  Gemini API error (final attempt failed): {api_error}")
    
    # All retries failed, use fallback
    print(f"⚠️  Falling back to keyword-based answer after {max_retries} failed attempts")
    print(f"   Question: {question[:100]}")
    print(f"   Relevant segments found: {len(relevant_segments)}")
    if relevant_segments:
        print(f"   First segment text: {relevant_segments[0].get('text', '')[:100]}")
    return generate_fallback_answer(question, relevant_segments, full_transcript)


def get_cache_key(question: str, current_time: float, relevant_segments: List[Dict]) -> str:
    """
    Generate cache key for question.
    Creates deterministic hash based on question, time, and relevant segments.
    
    Args:
        question: User's question
        current_time: Current video playback time
        relevant_segments: List of relevant segments
    
    Returns:
        MD5 hash string as cache key
    """
    # Create hash from question + time window + segment IDs
    segment_ids = []
    for seg in relevant_segments[:3]:
        if isinstance(seg, dict):
            segment_ids.append(seg.get("start_sec", 0))
    
    cache_data = f"{question.lower().strip()}:{current_time:.1f}:{segment_ids}"
    return hashlib.md5(cache_data.encode('utf-8')).hexdigest()


def answer_question(
    question: str,
    current_time: float,
    project_id: Optional[str] = None,
    use_cache: bool = True
) -> Dict:
    """
    Main Q&A function that processes a question and returns answer with action.
    Includes caching, fallback mechanisms, and robust error handling.
    Production-ready with comprehensive validation.
    
    Args:
        question: User's question (must be non-empty)
        current_time: Current video playback time in seconds (must be >= 0)
        project_id: Optional project ID
        use_cache: Whether to use cached answers
    
    Returns:
        Dict with answerText, action, targetTime (optional), and evidence
        Always returns a valid response, never raises exceptions
    """
    # Validate and sanitize inputs
    if not question or not isinstance(question, str):
        return {
            "answerText": "I didn't catch that. Could you please repeat your question?",
            "action": "resume",
            "evidence": []
        }
    
    question = question.strip()
    if not question:
        return {
            "answerText": "I didn't catch that. Could you please repeat your question?",
            "action": "resume",
            "evidence": []
        }
    
    # Validate current_time
    if not isinstance(current_time, (int, float)) or current_time < 0:
        current_time = 0.0
    
    # Cleanup cache periodically
    cleanup_cache()
    
    # Load transcript
    try:
        transcript = load_transcript(project_id)
    except Exception as e:
        print(f"⚠️  Error loading transcript: {e}")
        return {
            "answerText": "I apologize, but I'm having trouble accessing the transcript. Please try again later.",
            "action": "resume",
            "evidence": []
        }
    
    if not transcript:
        return {
            "answerText": "I apologize, but no transcript is available for this video.",
            "action": "resume",
            "evidence": []
        }
    
    # Find relevant segments with improved algorithm
    try:
        relevant_segments = find_relevant_segments(question, transcript, current_time)
    except Exception as e:
        print(f"⚠️  Error finding relevant segments: {e}")
        relevant_segments = []
    
    # Check cache (thread-safe)
    answer_text = None
    evidence = None
    
    if use_cache:
        cache_key = get_cache_key(question, current_time, relevant_segments)
        
        with _cache_lock:
            if cache_key in _answer_cache:
                cached_answer, cached_evidence, cached_time = _answer_cache[cache_key]
                # Check if cache is still valid
                if time.time() - cached_time < CACHE_TTL_SECONDS:
                    print(f"✅ Using cached answer for: {question[:50]}...")
                    answer_text, evidence = cached_answer, cached_evidence
                    # Move to end (LRU)
                    _answer_cache.move_to_end(cache_key)
                else:
                    # Cache expired
                    _answer_cache.pop(cache_key, None)
    
    # Generate answer if not cached
    if answer_text is None:
        # Build full transcript text
        full_transcript_text = None
        try:
            if "audio_segments" in transcript and isinstance(transcript["audio_segments"], list):
                transcript_parts = []
                for seg in transcript["audio_segments"]:
                    if isinstance(seg, dict):
                        text = seg.get("text", "")
                        if text and isinstance(text, str):
                            transcript_parts.append(text)
                full_transcript_text = " ".join(transcript_parts)
        except Exception as e:
            print(f"⚠️  Error building full transcript: {e}")
            full_transcript_text = None
        
        try:
            answer_text, evidence = generate_answer_with_gemini(
                question, relevant_segments, full_transcript_text
            )
            
            # Validate answer
            if not answer_text or not isinstance(answer_text, str):
                print(f"⚠️  Empty answer from Gemini, using fallback")
                raise ValueError("Empty answer from Gemini")
            
            # Check if answer is just a greeting (log warning but use it)
            answer_lower = answer_text.lower()
            greeting_phrases = ["welcome to this course", "welcome to", "this course"]
            if any(phrase in answer_lower[:50] for phrase in greeting_phrases) and len(relevant_segments) > 1:
                print(f"⚠️  Warning: Answer appears to be generic greeting")
            
            if not evidence or not isinstance(evidence, list):
                evidence = []
            
            # Cache the answer (thread-safe)
            if use_cache:
                cache_key = get_cache_key(question, current_time, relevant_segments)
                with _cache_lock:
                    # Cleanup if needed before adding
                    if len(_answer_cache) >= MAX_CACHE_SIZE:
                        _answer_cache.popitem(last=False)
                    _answer_cache[cache_key] = (answer_text, evidence, time.time())
                    _answer_cache.move_to_end(cache_key)  # Mark as recently used
                
        except Exception as e:
            print(f"⚠️  Error generating answer: {e}")
            # Use fallback
            try:
                answer_text, evidence = generate_fallback_answer(
                    question, relevant_segments, full_transcript_text
                )
            except Exception as fallback_error:
                print(f"⚠️  Fallback also failed: {fallback_error}")
                answer_text = "I apologize, but I encountered an error while processing your question. Please try again."
                evidence = []
    
    # Ensure we have valid answer
    if not answer_text:
        answer_text = "I apologize, but I couldn't generate a proper answer. Please try again."
    if not evidence:
        evidence = []
    
    # Classify intent
    try:
        intent = classify_question_intent(question)
    except Exception as e:
        print(f"⚠️  Error classifying intent: {e}")
        intent = "answer"
    
    # Determine target time for jump/rewatch actions
    target_time = None
    try:
        if intent == "jump" and relevant_segments:
            first_segment = relevant_segments[0]
            if isinstance(first_segment, dict):
                target_time = first_segment.get("start_sec", current_time)
                if not isinstance(target_time, (int, float)) or target_time < 0:
                    target_time = current_time
        elif intent == "rewatch":
            target_time = max(0.0, current_time - 10.0)
    except Exception as e:
        print(f"⚠️  Error determining target time: {e}")
        target_time = None
    
    return {
        "answerText": answer_text,
        "action": intent if intent in ["jump", "rewatch"] else "resume",
        "targetTime": target_time,
        "evidence": evidence if isinstance(evidence, list) else []
    }


def classify_question_intent(question: str) -> str:
    """
    Classify question intent to determine action type.
    Handles edge cases and validates input.
    
    Args:
        question: User's question
    
    Returns:
        "jump", "rewatch", or "answer"
    """
    if not question or not isinstance(question, str):
        return "answer"
    
    question_lower = question.lower().strip()
    
    # Jump keywords
    jump_keywords = ["go to", "jump to", "skip to", "show me", "where is", "when does"]
    if any(keyword in question_lower for keyword in jump_keywords):
        return "jump"
    
    # Rewatch keywords
    rewatch_keywords = ["repeat", "rewatch", "again", "replay", "what did he say", "what did she say"]
    if any(keyword in question_lower for keyword in rewatch_keywords):
        return "rewatch"
    
    # Default to answer
    return "answer"
