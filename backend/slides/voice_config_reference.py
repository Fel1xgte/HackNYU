# ElevenLabs Voice Configuration for Confucius Theme
# =================================================

# RECOMMENDED VOICES FOR ANCIENT PHILOSOPHER THEME
# These voices work well for wise, authoritative narration

VOICE_OPTIONS = {
    # PRIMARY RECOMMENDATION
    "adam": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "description": "Deep, authoritative male voice - sounds wise and commanding",
        "best_for": "Philosophical content, lectures, serious topics",
        "age_impression": "Middle-aged to elder",
        "tone": "Calm, steady, thoughtful"
    },
    
    # ALTERNATIVE OPTIONS
    "antoni": {
        "voice_id": "ErXwobaYiN019PkySvjV",
        "description": "Well-rounded, warm male voice",
        "best_for": "Educational content, storytelling",
        "age_impression": "Adult male",
        "tone": "Clear, engaging, friendly"
    },
    
    "arnold": {
        "voice_id": "VR6AewLTigWG4xSOukaG",
        "description": "Mature, resonant male voice",
        "best_for": "Historical narratives, documentaries",
        "age_impression": "Older male",
        "tone": "Deep, steady, authoritative"
    },
    
    "callum": {
        "voice_id": "N2lVS1w4EtoT3dr4eOWO",
        "description": "Masculine, hoarse voice with character",
        "best_for": "Dramatic readings, character narration",
        "age_impression": "Mature male",
        "tone": "Distinctive, textured"
    },
    
    "james": {
        "voice_id": "ZQe5CZNOzWyzPSCn5a3c",
        "description": "Calm, mature male voice",
        "best_for": "Meditation, wisdom teachings",
        "age_impression": "Older male",
        "tone": "Peaceful, grounding"
    }
}

# VOICE SETTINGS EXPLAINED
# ========================

VOICE_SETTINGS_GUIDE = {
    "stability": {
        "range": "0.0 - 1.0",
        "description": "Controls consistency vs expressiveness",
        "low_value": "0.0-0.3: More expressive, varying, emotional",
        "medium_value": "0.4-0.7: Balanced - RECOMMENDED for lectures",
        "high_value": "0.8-1.0: Very stable, monotone, consistent",
        "recommended_for_confucius": 0.7
    },
    
    "similarity_boost": {
        "range": "0.0 - 1.0",
        "description": "How closely to match the original voice",
        "low_value": "0.0-0.4: More creative interpretation",
        "medium_value": "0.5-0.7: Balanced",
        "high_value": "0.8-1.0: Very close to original - RECOMMENDED",
        "recommended_for_confucius": 0.8
    },
    
    "style": {
        "range": "0.0 - 1.0",
        "description": "Exaggeration of the style (only in v2 models)",
        "low_value": "0.0-0.3: Subtle, natural",
        "medium_value": "0.4-0.6: Moderate emphasis - RECOMMENDED",
        "high_value": "0.7-1.0: Dramatic, exaggerated",
        "recommended_for_confucius": 0.4
    },
    
    "use_speaker_boost": {
        "type": "boolean",
        "description": "Enhances similarity to original speaker",
        "recommended_for_confucius": True
    }
}

# MODEL OPTIONS
# =============

MODELS = {
    "eleven_multilingual_v2": {
        "description": "Latest model with best quality and 29 languages",
        "languages": "English, Spanish, French, German, Polish, Italian, Portuguese, Hindi, Arabic, and more",
        "recommended": True,
        "features": ["High quality", "Multilingual", "Style control"]
    },
    
    "eleven_monolingual_v1": {
        "description": "Original English-only model",
        "languages": "English only",
        "recommended": False,
        "features": ["English optimized", "Stable"]
    },
    
    "eleven_turbo_v2": {
        "description": "Fastest model with good quality",
        "languages": "English + some multilingual support",
        "recommended": False,
        "features": ["Very fast", "Lower latency", "Good for real-time"]
    }
}

# IMPLEMENTATION EXAMPLE
# ======================

EXAMPLE_CONFIG = """
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="your-api-key")

# Confucius-style voice configuration
voice_config = {
    "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam voice
    "model_id": "eleven_multilingual_v2",
    "voice_settings": VoiceSettings(
        stability=0.7,              # Calm and steady
        similarity_boost=0.8,       # Stay true to voice
        style=0.4,                  # Moderate emphasis
        use_speaker_boost=True      # Enhanced clarity
    )
}

# Generate audio
audio = client.text_to_speech.convert(
    voice_id=voice_config["voice_id"],
    text="The journey of a thousand miles begins with a single step.",
    model_id=voice_config["model_id"],
    voice_settings=voice_config["voice_settings"],
    output_format="mp3_44100_128"
)
"""

# CUSTOMIZATION TIPS
# ==================

TIPS = """
1. TEST MULTIPLE VOICES
   - Use get_available_voices() in audio_generator.py
   - Generate a sample with each voice
   - Choose the one that best fits your content

2. ADJUST SETTINGS FOR CONTENT TYPE
   - Philosophical/Wisdom: stability=0.7, style=0.3-0.4
   - Emotional/Storytelling: stability=0.4-0.5, style=0.6-0.7
   - Technical/Factual: stability=0.8, style=0.2

3. OPTIMIZE AUDIO QUALITY
   - Use output_format="mp3_44100_128" for good quality
   - For premium quality: "mp3_44100_192"
   - For smaller files: "mp3_44100_96"

4. SCRIPT PREPARATION
   - Use clear punctuation for natural pauses
   - Add commas for breath points
   - Use periods for longer pauses
   - Keep sentences under 20 words for better pacing

5. CONFUCIUS-SPECIFIC TIPS
   - Use formal, measured language
   - Include rhetorical pauses
   - Emphasize key wisdom with short sentences
   - Example: "The wise man seeks truth. He finds it within."
"""

# HOW TO CHANGE VOICE IN YOUR PROJECT
# ===================================

CHANGE_VOICE_INSTRUCTIONS = """
To change the voice in audio_generator.py:

1. Find the VOICE_CONFIG section (around line 17)

2. Replace the voice_id with your chosen voice:
   VOICE_CONFIG = {
       "voice_id": "pNInz6obpgDQGcFmaJgB",  # Change this
       ...
   }

3. Adjust voice settings if needed:
   "voice_settings": VoiceSettings(
       stability=0.7,        # Adjust these
       similarity_boost=0.8,  # values to
       style=0.4,             # fine-tune
       use_speaker_boost=True
   )

4. Test with a single slide first:
   python3 audio_generator.py

5. Listen to the output in generated_audio/audio_01.mp3

6. Adjust settings and regenerate if needed
"""

if __name__ == "__main__":
    print("=" * 70)
    print("ELEVENLABS VOICE CONFIGURATION GUIDE")
    print("=" * 70)
    print("\nThis file contains reference information for configuring")
    print("ElevenLabs voices for the Confucius Lecture Summarizer.")
    print("\nRecommended voice: Adam (pNInz6obpgDQGcFmaJgB)")
    print("Recommended model: eleven_multilingual_v2")
    print("\nFor detailed instructions, see the comments in this file.")
    print("\nTo change the voice, edit VOICE_CONFIG in audio_generator.py")
    print("=" * 70)
