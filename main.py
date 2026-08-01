"""Basic Voice AI Assistant — Fast, Local, Simple.

Uses only:
- Faster-Whisper (tiny model) for STT
- Ollama (local LLM) for AI responses
- pyttsx3 (SAPI5) for TTS
- Auto-headset detection

No cloud APIs. No rate limits. Works 100% offline.

Run: python main.py
Requirements: pip install faster-whisper sounddevice soundfile numpy pyttsx3 requests
Also: ollama serve (in another terminal) + ollama pull llama3.2:3b
"""

import sys
import os
import time
import threading
import queue
import numpy as np

os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)


# =============================================================================
# CONFIG
# =============================================================================

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")  # ~1GB RAM, already installed

# Import modules
from memory import Memory
from logger import ConversationLogger
from personality import PersonalityManager
from adaptive import Adaptive

_memory = Memory()
_logger = ConversationLogger()
_persona = PersonalityManager()
_adaptive = Adaptive()

# Proactive helper
from proactive import ProactiveHelper
_proactive = ProactiveHelper()

# Auto-learn from conversations
from memory import AutoLearn
_auto_learn = AutoLearn(_memory)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
SILENCE_THRESHOLD = 300      # RMS threshold for int16 audio
SILENCE_DURATION = 0.6       # Seconds of silence to stop recording
MAX_RECORD_SECONDS = 15      # Max recording length
SPEECH_WAIT_TIMEOUT = 8      # Seconds to wait for speech before giving up

WHISPER_MODEL = "tiny"       # Fastest model — 'base' was too slow on 8GB RAM
TTS_RATE = 200               # Words per minute (fast but clear)

# Headset detection keywords
HEADSET_KEYWORDS = [
    "headset", "headphone", "usb", "bluetooth", "bt",
    "airpod", "buds", "jabra", "hyperx", "steelseries",
    "corsair", "razer", "logitech", "bose", "sony",
    "jbl", "sennheiser", "rode", "blue yeti", "fifine",
]


# =============================================================================
# AUTO MIC DETECTION
# =============================================================================

def find_best_mic():
    """Auto-detect best microphone (prefers headsets/USB)."""
    import sounddevice as sd

    devices = sd.query_devices()
    inputs = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]

    if not inputs:
        return None

    best_idx, best_score = None, -999

    for idx, dev in inputs:
        name = dev["name"].lower()
        score = 0
        for kw in HEADSET_KEYWORDS:
            if kw in name:
                score += 100
                break
        if "usb" in name: score += 50
        if "bluetooth" in name: score += 40
        if "realtek" in name: score -= 20
        if "stereo mix" in name or "loopback" in name: score -= 100
        if idx == sd.default.device[0]: score += 10

        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is not None:
        name = devices[best_idx]["name"].strip()
        if best_score >= 50:
            print(f"🎧 Headset: [{best_idx}] {name}")
        else:
            print(f"🎤 Mic: [{best_idx}] {name}")
    return best_idx


# =============================================================================
# SPEECH-TO-TEXT (Faster-Whisper, local, CPU)
# =============================================================================

_whisper_model = None

def load_whisper():
    """Load Whisper model once."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print(f"⚡ Loading Whisper '{WHISPER_MODEL}' model...")
        sys.stdout.flush()
        start = time.perf_counter()
        _whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        ms = (time.perf_counter() - start) * 1000
        print(f"⚡ Whisper ready ({ms:.0f}ms)")
        sys.stdout.flush()
    return _whisper_model


def _clean_audio(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
    """Clean audio with noise gate and voice bandpass filter.

    1. Noise gate: silence anything below threshold (kills constant background hum)
    2. Voice bandpass: keep only 200Hz-3500Hz (human voice range, removes fans/typing)
    """
    from scipy.signal import butter, filtfilt

    audio = audio_data.astype(np.float32)

    # Noise gate: compute RMS and silence frames below 20% of peak
    frame_size = 512
    peak_rms = 0
    for i in range(0, len(audio) - frame_size, frame_size):
        frame_rms = np.sqrt(np.mean(audio[i:i+frame_size] ** 2))
        peak_rms = max(peak_rms, frame_rms)

    gate_threshold = peak_rms * 0.15  # 15% of peak = noise floor
    for i in range(0, len(audio) - frame_size, frame_size):
        frame_rms = np.sqrt(np.mean(audio[i:i+frame_size] ** 2))
        if frame_rms < gate_threshold:
            audio[i:i+frame_size] *= 0.05  # Reduce noise to near-zero

    # Bandpass filter: 200Hz - 3500Hz (human voice range)
    nyquist = sample_rate / 2
    low = 200 / nyquist
    high = 3500 / nyquist
    # Clamp to valid range
    low = max(0.01, min(low, 0.99))
    high = max(low + 0.01, min(high, 0.99))

    b, a = butter(4, [low, high], btype='band')
    audio = filtfilt(b, a, audio)

    # Normalize volume
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 30000  # Normalize to healthy int16 range

    return audio.astype(np.int16)


def transcribe(audio_file: str) -> str:
    """Transcribe audio — optimized for speed on trimmed audio."""
    print("🧠 Transcribing...", end=" ")
    sys.stdout.flush()
    start = time.perf_counter()

    model = load_whisper()
    segments, _ = model.transcribe(
        audio_file,
        beam_size=1,             # Fastest decoding (audio is already clean/trimmed)
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 150,   # Aggressive silence trimming
            "speech_pad_ms": 80,              # Minimal padding
            "threshold": 0.35,                # Sensitive voice detection
        },
        no_speech_threshold=0.5,
        log_prob_threshold=-0.8,
        compression_ratio_threshold=2.4,
        condition_on_previous_text=False,
        language="en",
        temperature=0.0,
    )
    text = " ".join(s.text for s in segments).strip()
    ms = (time.perf_counter() - start) * 1000
    if text:
        print(f"({ms:.0f}ms)")
        print(f"📝 You: \"{text}\"")
    else:
        print("(nothing detected)")
    sys.stdout.flush()
    return text


# =============================================================================
# TEXT-TO-SPEECH (now handled by smart_tts.py)
# =============================================================================

def speak(text: str):
    """Speak text using Smart TTS (adaptive speed, natural pauses)."""
    from smart_tts import speak as _smart_speak
    _smart_speak(text)


# =============================================================================
# OLLAMA LLM (local, unlimited, no API key)
# =============================================================================

_chat_history = []


def check_ollama() -> bool:
    """Check if Ollama is running."""
    import requests
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                print(f"🟢 Ollama online: {len(models)} models")
                print(f"   Using: {OLLAMA_MODEL}")
                return True
            else:
                print("⚠️ Ollama running but no models. Run: ollama pull llama3.2:3b")
                return False
        return False
    except Exception:
        print("❌ Ollama not running! Start it with: ollama serve")
        print("   Then pull a model: ollama pull llama3.2:3b")
        return False


def ask_ollama(text: str) -> str:
    """Send text to Ollama with STREAMING — speaks first sentence while rest generates."""
    import requests
    global OLLAMA_MODEL

    _chat_history.append({"role": "user", "content": text})

    # Build messages
    messages = _chat_history[-20:]
    if not any(m["role"] == "system" for m in messages):
        memories_text = _memory.recall_as_text()
        persona_prompt = _persona.get_system_prompt()
        messages.insert(0, {
            "role": "system",
            "content": f"{persona_prompt}\n\n**Memories:**\n{memories_text}"
        })

    # Detect complex requests
    text_lower = text.lower()
    is_complex = any(w in text_lower for w in [
        "write", "create", "build", "generate", "make", "code", "html",
        "script", "function", "app", "website", "project", "file",
        "portfolio", "animated", "design", "template",
    ])

    if is_complex:
        print("🧠 Creating...", end=" ")
    else:
        print("🧠 Thinking...", end=" ")
    sys.stdout.flush()

    start = time.perf_counter()

    try:
        # STREAMING MODE: get tokens as they arrive
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": True,  # ← KEY CHANGE: stream tokens
                "options": {
                    "num_predict": 1024 if is_complex else 300,
                    "temperature": 0.3 if is_complex else 0.7,
                },
            },
            stream=True,
            timeout=180,
        )

        if r.status_code == 500 and "memory" in r.text.lower():
            smaller = _find_smallest_model()
            if smaller and smaller != OLLAMA_MODEL:
                OLLAMA_MODEL = smaller
                return ask_ollama(text)  # Retry with smaller model
            return "Not enough RAM. Close some apps."

        if r.status_code != 200:
            return f"Ollama error: HTTP {r.status_code}"

        # Stream and collect response
        import json as json_mod
        full_response = ""
        first_sentence_spoken = False
        sentence_buffer = ""

        for line in r.iter_lines():
            if not line:
                continue
            try:
                chunk = json_mod.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if not token:
                    continue

                full_response += token
                sentence_buffer += token

                # Print token as it arrives (live typing effect)
                sys.stdout.write(token)
                sys.stdout.flush()

                # Speak first complete sentence immediately
                if not first_sentence_spoken and _has_sentence_end(sentence_buffer):
                    first_sentence = _extract_first_sentence(sentence_buffer)
                    if first_sentence and len(first_sentence) > 10:
                        ms = (time.perf_counter() - start) * 1000
                        sys.stdout.write(f" [{ms/1000:.1f}s]\n")
                        sys.stdout.flush()
                        # Speak in background while rest generates
                        from smart_tts import speak_async
                        speak_async(first_sentence)
                        first_sentence_spoken = True

                # Check if done
                if chunk.get("done"):
                    break

            except (json_mod.JSONDecodeError, KeyError):
                continue

        elapsed = time.perf_counter() - start
        if not first_sentence_spoken:
            sys.stdout.write(f" ({elapsed:.1f}s)\n")
            sys.stdout.flush()

        full_response = full_response.strip()
        _chat_history.append({"role": "assistant", "content": full_response})

        # Auto-save code if present
        if is_complex and "```" in full_response:
            _auto_save_code(full_response, text)

        return full_response

    except requests.exceptions.Timeout:
        return "Took too long. Try a simpler request."
    except requests.exceptions.ConnectionError:
        return "Lost connection to Ollama."
    except Exception as e:
        return f"Error: {e}"


def _has_sentence_end(text: str) -> bool:
    """Check if text contains at least one complete sentence."""
    # Look for sentence endings (. ! ? followed by space or end)
    import re
    return bool(re.search(r'[.!?][\s]', text)) or text.endswith(('.', '!', '?'))


def _extract_first_sentence(text: str) -> str:
    """Extract the first complete sentence from text."""
    import re
    match = re.match(r'^(.*?[.!?])[\s]', text)
    if match:
        return match.group(1).strip()
    if text.endswith(('.', '!', '?')):
        return text.strip()
    return ""


def _auto_save_code(response: str, original_request: str) -> None:
    """If Ollama generated code in its response, auto-save it to a file."""
    import re
    match = re.search(r"```(\w*)\n(.*?)```", response, re.DOTALL)
    if match:
        lang = match.group(1) or "txt"
        code = match.group(2).strip()

        ext_map = {"python": ".py", "py": ".py", "html": ".html",
                   "javascript": ".js", "js": ".js", "css": ".css",
                   "sql": ".sql", "bash": ".sh", "json": ".json"}
        ext = ext_map.get(lang.lower(), f".{lang}" if lang else ".txt")

        os.makedirs("generated_code", exist_ok=True)
        filename = f"generated_code/nova_{time.strftime('%H%M%S')}{ext}"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"  💾 Code saved: {filename}")
        sys.stdout.flush()

        # Copy to clipboard
        try:
            import subprocess
            process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            process.communicate(code.encode("utf-8"))
            print("  📋 Copied to clipboard!")
            sys.stdout.flush()
        except Exception:
            pass


def _find_smallest_model() -> str:
    """Find the smallest available Ollama model."""
    import requests
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            if models:
                # Sort by size (smallest first)
                models.sort(key=lambda m: m.get("size", float("inf")))
                return models[0]["name"]
    except Exception:
        pass
    return ""


# =============================================================================
# AUDIO RECORDING (with VAD)
# =============================================================================

_mic_device = None


def record() -> str:
    """Record audio — SMART: only saves the speech portion (trims silence)."""
    global _mic_device
    import sounddevice as sd
    import soundfile as sf

    if _mic_device is None:
        _mic_device = find_best_mic()

    print("\n🟡 Listening... (speak now)")
    sys.stdout.flush()

    frames = []
    silent_chunks = 0
    speaking = False
    speech_start_frame = 0  # Track where speech actually starts
    max_silent = int(SAMPLE_RATE / CHUNK_SIZE * SILENCE_DURATION)
    max_total = int(SAMPLE_RATE / CHUNK_SIZE * MAX_RECORD_SECONDS)
    wait_limit = int(SAMPLE_RATE / CHUNK_SIZE * SPEECH_WAIT_TIMEOUT)
    frame_count_total = 0

    def callback(indata, frame_count, time_info, status):
        nonlocal silent_chunks, speaking, speech_start_frame, frame_count_total
        frames.append(indata.copy())
        frame_count_total += 1
        rms = float(np.sqrt(np.mean(indata.astype(np.float64) ** 2)))
        if rms > SILENCE_THRESHOLD:
            if not speaking:
                speech_start_frame = max(0, frame_count_total - 3)  # Keep 3 frames before speech
                sys.stdout.write("🔴 Recording...\n")
                sys.stdout.flush()
            speaking = True
            silent_chunks = 0
        elif speaking:
            silent_chunks += 1

    try:
        with sd.InputStream(device=_mic_device, samplerate=SAMPLE_RATE,
                            channels=1, dtype="int16", blocksize=CHUNK_SIZE,
                            callback=callback):
            count = 0
            while count < max_total:
                sd.sleep(int(CHUNK_SIZE / SAMPLE_RATE * 1000))
                count += 1
                if not speaking and count > wait_limit:
                    break
                if speaking and silent_chunks > max_silent:
                    break
    except Exception as e:
        print(f"❌ Audio error: {e}")
        return ""

    if not frames or not speaking:
        print("   (no speech)")
        return ""

    # SMART TRIM: only keep frames from speech_start to speech_end
    # This is the key optimization — trims 12s recording to 2-3s of actual speech
    speech_end_frame = min(len(frames), frame_count_total - silent_chunks + 2)
    trimmed_frames = frames[speech_start_frame:speech_end_frame]
    
    if not trimmed_frames:
        trimmed_frames = frames  # Fallback to full recording

    audio = np.concatenate(trimmed_frames, axis=0)
    duration = len(audio) / SAMPLE_RATE

    # Clean audio (noise gate + bandpass)
    try:
        audio = _clean_audio(audio, SAMPLE_RATE)
    except Exception:
        pass

    os.makedirs("output", exist_ok=True)
    from datetime import datetime
    filename = f"output/rec_{datetime.now().strftime('%H%M%S')}.wav"
    sf.write(filename, audio, SAMPLE_RATE, subtype="PCM_16")

    print(f"✅ {duration:.1f}s captured")
    sys.stdout.flush()
    return filename


# =============================================================================
# MAIN LOOP
# =============================================================================

def _listen_for_answer() -> str:
    """Record + transcribe a short answer (used by SmartBuilder during Q&A)."""
    audio_file = record()
    if not audio_file:
        return ""
    text = transcribe(audio_file)
    try:
        os.remove(audio_file)
    except Exception:
        pass
    return text


def _get_remaining_to_speak(full_response: str) -> str:
    """Get text after the first sentence (which was already spoken during stream)."""
    import re
    match = re.match(r'^(.*?[.!?])[\s](.+)', full_response, re.DOTALL)
    if match:
        return match.group(2).strip()
    return ""


def main():
    print("=" * 50)
    print("  🎙️ Nova Basic — Local Voice AI Assistant")
    print("  100% offline • Ollama + Whisper + SAPI5")
    print("=" * 50)
    print()
    print(f"  Personality: {_persona.current_emoji} {_persona.mode_display}")
    print(f"  Memories: {_memory.count} facts stored")
    print(f"  Logs: {_logger.today_file}")
    print(f"  Learning: {_adaptive._data['total_interactions']} interactions tracked")
    print()
    sys.stdout.flush()

    # Check Ollama
    if not check_ollama():
        print("\n⚠️ Starting without LLM. Fix Ollama and restart.")
        print()
    sys.stdout.flush()

    # Pre-load Whisper
    load_whisper()
    print()

    # Daily briefing
    from daily_brief import get_daily_briefing, print_briefing_banner
    user_name = ""
    name_facts = _memory.recall("name")
    if name_facts:
        # Try to extract name from memory
        for fact in name_facts:
            if "name" in fact.get("fact", "").lower():
                import re
                match = re.search(r"(?:name is|i am|i'm)\s+(\w+)", fact["fact"], re.I)
                if match:
                    user_name = match.group(1)
                    break

    print_briefing_banner(user_name)
    briefing = get_daily_briefing(user_name)
    speak(briefing)

    # Remind about pending tasks
    from tasks import get_pending_summary
    task_summary = get_pending_summary()
    if task_summary:
        print(f"  📋 {task_summary}")

    # Wire timer speak function
    from timers import set_speak_function
    set_speak_function(speak)

    print("\nReady! Speak into your microphone.")
    print("Press Ctrl+C to quit.\n")
    sys.stdout.flush()

    # Start status dot (floating indicator)
    try:
        from status_dot import set_state
        from status_dot import get_dot
        get_dot()  # Initialize
        set_state("idle")
    except Exception:
        set_state = lambda s: None  # Fallback: no-op

    # Initialize command router
    from command_router import CommandRouter
    router = CommandRouter(
        speak_fn=speak,
        listen_fn=_listen_for_answer,
        logger=_logger,
        adaptive=_adaptive,
        proactive=_proactive,
        memory=_memory,
        persona=_persona,
    )

    while True:
        # 1. Record audio
        set_state("listening")
        audio_file = record()
        if not audio_file:
            set_state("idle")
            continue

        # 2. Transcribe
        set_state("thinking")
        text = transcribe(audio_file)
        if not text:
            set_state("idle")
            continue

        # 3. Route to handler
        result = router.route(text)

        # Auto-learn from user's speech (silent)
        learned = _auto_learn.analyze(text)
        if learned:
            for fact in learned:
                print(f"  🧠 Learned: {fact}")
            sys.stdout.flush()

        # Exit command
        if result.get("exit"):
            _logger.log_user(text)
            _logger.log_system("Session ended.")
            speak(result["response"])
            break

        # Handler returned a direct response
        if result["handled"] and result.get("response"):
            _logger.log_user(text)
            _logger.log_system(f"{result['action']}: {result['response'][:60]}")
            _adaptive.track(result["action"], {"text": text[:30]})
            set_state("speaking")
            speak(result["response"])
            set_state("idle")
            print("-" * 40)
            sys.stdout.flush()
            continue

        # Not handled by router (or search with context) → send to Ollama
        _logger.log_user(text)
        set_state("thinking")
        search_ctx = result.get("search_context", "")
        if search_ctx:
            prompt = (
                f"Based on these search results, answer: \"{text}\"\n\n"
                f"{search_ctx}\n\nGive a brief answer (2-3 sentences)."
            )
        else:
            prompt = text

        response = ask_ollama(prompt)
        print(f"\n{_persona.current_emoji} Nova: {response}")
        sys.stdout.flush()

        _logger.log_nova(response)
        _adaptive.track("chat", {"topic": text[:50]})

        # Speak remaining text (first sentence already spoken via streaming)
        set_state("speaking")
        from smart_tts import speak as _speak_full
        remaining = _get_remaining_to_speak(response)
        if remaining:
            _speak_full(remaining)
        elif not _has_sentence_end(response):
            speak(response)
        set_state("idle")

        # Proactive assistance
        had_error = "error" in response.lower()[:30] or "couldn't" in response.lower()[:30]
        _proactive.track_input(text, "chat", had_error=had_error)
        tip = _proactive.check_and_suggest("chat", text, response)
        if tip:
            print(f"  🤖 {tip}")
            sys.stdout.flush()

        followup = _proactive.get_contextual_followup(result["action"], response)
        if followup:
            print(f"  {followup}")
            sys.stdout.flush()

        print("-" * 40)
        sys.stdout.flush()

        # Clean up audio
        try:
            os.remove(audio_file)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
