"""Smart TTS — adaptive speech speed, natural pauses, and contextual tone.

Improvements over basic TTS:
- Short replies → faster speech (220 wpm)
- Long explanations → slower, clearer (180 wpm)
- Code/technical → even slower with pauses (160 wpm)
- Adds natural pauses at commas and periods
- Excited tone for success, calm for errors
- Skips code blocks (doesn't read raw code aloud)

Usage:
    from smart_tts import SmartTTS
    tts = SmartTTS()
    tts.speak("Hello!")                           # Fast, cheerful
    tts.speak("Here's a long explanation...")      # Slower, clear
    tts.speak("Error: file not found")            # Calm, measured
    tts.speak_async("Working on it...")           # Non-blocking
"""

import threading
import queue
import time
import re
import sys
from typing import Optional


_tts_queue = queue.Queue()
_voice_id = None
_initialized = False


def _find_voice():
    """Find and cache preferred voice ID."""
    global _voice_id
    if _voice_id is not None:
        return
    import pyttsx3
    engine = pyttsx3.init()
    for v in engine.getProperty("voices"):
        if "zira" in v.name.lower() or "female" in v.name.lower():
            _voice_id = v.id
            break
    if not _voice_id:
        voices = engine.getProperty("voices")
        if voices:
            _voice_id = voices[0].id
    engine.stop()
    del engine


def _classify_text(text: str) -> dict:
    """Analyze text to determine best speech parameters.

    Returns dict with: rate, volume, pause_ms
    """
    text_lower = text.lower()
    word_count = len(text.split())

    # Default
    rate = 200
    volume = 1.0

    # Short responses (1-10 words) → fast and snappy
    if word_count <= 10:
        rate = 220

    # Medium (10-30 words) → normal
    elif word_count <= 30:
        rate = 200

    # Long explanations (30+ words) → slower for clarity
    elif word_count > 30:
        rate = 180

    # Technical/code content → slowest
    if any(w in text_lower for w in ["function", "error", "variable", "syntax",
                                      "import", "class", "method", "parameter"]):
        rate = 170

    # Error messages → calm, slightly slower
    if any(w in text_lower for w in ["error", "failed", "couldn't", "problem",
                                      "issue", "wrong", "broken"]):
        rate = 175
        volume = 0.9

    # Success/positive → slightly faster, cheerful
    if any(w in text_lower for w in ["done", "created", "success", "perfect",
                                      "great", "opened", "saved"]):
        rate = 215

    # Questions → normal pace
    if text.strip().endswith("?"):
        rate = 195

    return {"rate": rate, "volume": volume}


def _clean_for_speech(text: str) -> str:
    """Clean text for natural speech output.

    - Removes code blocks (don't read raw code)
    - Converts symbols to words
    - Adds micro-pauses (commas → brief pause)
    """
    # Remove code blocks entirely
    text = re.sub(r"```\w*\n.*?```", "I've generated the code for you.", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove markdown formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Convert symbols to speakable words
    text = text.replace("→", "leads to")
    text = text.replace("←", "from")
    text = text.replace("✓", "done")
    text = text.replace("✗", "failed")
    text = text.replace("/", " slash ")
    text = text.replace("\\", " backslash ")

    # Remove file paths (just say the filename)
    text = re.sub(r"[A-Z]:\\[\w\\]+\\(\w+\.\w+)", r"\1", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate very long responses for voice (max ~150 words spoken)
    words = text.split()
    if len(words) > 150:
        text = " ".join(words[:150]) + ". That's the summary."

    return text


def _tts_worker():
    """Background TTS worker with adaptive rate and natural pauses."""
    _find_voice()

    while True:
        item = _tts_queue.get()
        if item is None:
            break

        text, params = item
        if not text.strip():
            _tts_queue.task_done()
            continue

        try:
            import pyttsx3
            engine = pyttsx3.init()
            if _voice_id:
                engine.setProperty("voice", _voice_id)
            engine.setProperty("rate", params["rate"])
            engine.setProperty("volume", params.get("volume", 1.0))

            # Split into sentences for natural pauses
            sentences = re.split(r"(?<=[.!?])\s+", text)

            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    engine.say(sentence.strip())
                    # Add micro-pause between sentences
                    if i < len(sentences) - 1:
                        engine.say(" ")  # Brief pause

            engine.runAndWait()
            engine.stop()
            del engine

        except Exception as e:
            print(f"⚠️ TTS error: {e}", file=sys.stderr)
        finally:
            _tts_queue.task_done()


# Start worker thread
_worker_thread = threading.Thread(target=_tts_worker, daemon=True)
_worker_thread.start()


class SmartTTS:
    """Adaptive text-to-speech with context-aware speed and natural pauses."""

    def speak(self, text: str) -> None:
        """Speak text with adaptive rate (blocks until done).

        Automatically:
        - Adjusts speed based on content length and type
        - Removes code blocks (doesn't read raw code)
        - Adds natural pauses between sentences
        - Truncates very long responses
        """
        if not text or not text.strip():
            return

        start = time.perf_counter()

        # Clean and classify
        clean_text = _clean_for_speech(text)
        if not clean_text.strip():
            return

        params = _classify_text(clean_text)

        # Queue and wait
        _tts_queue.put((clean_text, params))
        _tts_queue.join()

        ms = (time.perf_counter() - start) * 1000
        rate_label = "fast" if params["rate"] >= 210 else "normal" if params["rate"] >= 190 else "slow"
        print(f"🔊 ({ms:.0f}ms, {rate_label})")
        sys.stdout.flush()

    def speak_async(self, text: str) -> None:
        """Speak without blocking (fire-and-forget)."""
        if not text or not text.strip():
            return
        clean_text = _clean_for_speech(text)
        params = _classify_text(clean_text)
        _tts_queue.put((clean_text, params))

    def shutdown(self) -> None:
        """Stop the TTS worker."""
        _tts_queue.put(None)


# Global instance for easy import
_smart_tts = SmartTTS()

def speak(text: str) -> None:
    """Drop-in replacement for the basic speak() function."""
    _smart_tts.speak(text)

def speak_async(text: str) -> None:
    """Non-blocking speech."""
    _smart_tts.speak_async(text)
