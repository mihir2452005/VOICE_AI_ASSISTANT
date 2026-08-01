# 🎙️ Nova Basic — Local Voice AI Assistant

A fully-featured voice AI assistant running **100% locally** on your PC. No cloud APIs, no rate limits, no internet required. Built with Python, Ollama, Whisper, and 33 custom modules.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Modules](https://img.shields.io/badge/modules-33-purple)
![Offline](https://img.shields.io/badge/mode-100%25%20offline-green)
![RAM](https://img.shields.io/badge/RAM-8GB%20minimum-orange)

---

## 🎯 What It Does

Nova is a voice-controlled desktop assistant that can:

- **Talk to you** using local AI (Ollama) with streaming responses
- **Write code** by voice, iterate on it, auto-lint, and preview in browser
- **Control your browser** — open sites, click buttons, manage bookmarks
- **Remember things** about you and auto-learn from conversations
- **Manage tasks, timers, and notes** — all by voice
- **Read your screen** using OCR and explain errors
- **Execute terminal commands** and manage git repos by voice
- **Build full websites** — interactively asks what you want, then generates

---

## ⚡ Quick Start

```bash
# 1. Start Ollama (in a separate terminal)
ollama serve
ollama pull qwen2.5:1.5b

# 2. Install dependencies
cd basic
pip install -r requirements.txt

# 3. Run
python main.py
```

---

## 🏗️ Architecture (33 Modules)

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (voice loop)                   │
│  Record → Transcribe → Route → Respond → Speak          │
├─────────────────────────────────────────────────────────┤
│                 command_router.py                         │
│  Priority-based dispatcher (22 handlers)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─── AI & Voice ───┐  ┌─── Coding ──────────────┐     │
│  │ smart_tts.py      │  │ coder.py (personalized) │     │
│  │ (adaptive speed)  │  │ auto_lint.py (3-level)  │     │
│  │                   │  │ auto_preview.py         │     │
│  │ Ollama streaming  │  │ version_history.py      │     │
│  │ (in main.py)      │  │ multi_file_gen.py       │     │
│  └───────────────────┘  │ smart_builder.py        │     │
│                          │ project_builder.py      │     │
│  ┌─── Browser ──────┐   │ code_explainer.py       │     │
│  │ browser_control   │   │ code_fixer.py           │     │
│  │ bookmarks.py      │   │ code_checker.py         │     │
│  │ workflows.py      │   └────────────────────────┘     │
│  │ smart_click.py    │                                   │
│  └───────────────────┘  ┌─── Intelligence ────────┐     │
│                          │ memory.py (auto-learn)  │     │
│  ┌─── Utilities ────┐   │ adaptive.py             │     │
│  │ calculator.py     │   │ proactive.py            │     │
│  │ terminal.py       │   │ personality.py          │     │
│  │ git_helper.py     │   │ daily_brief.py          │     │
│  │ file_explorer.py  │   └────────────────────────┘     │
│  │ screen_reader.py  │                                   │
│  │ web_search.py     │  ┌─── Productivity ────────┐     │
│  │ tasks.py          │  │ notes.py                 │     │
│  │ timers.py         │  │ logger.py                │     │
│  │ status_dot.py     │  │ (conversation logging)   │     │
│  └───────────────────┘  └────────────────────────-─┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 All 33 Modules

### Core
| Module | What it does |
|--------|-------------|
| `main.py` | Voice loop: record → transcribe → route → respond → speak |
| `command_router.py` | Priority-based command dispatcher (22 handlers) |
| `smart_tts.py` | Adaptive TTS: fast for short replies, slow for explanations |
| `status_dot.py` | Floating color dot showing current state |

### AI & Code Generation
| Module | What it does |
|--------|-------------|
| `coder.py` | Write code by voice, iterate, auto-personalize with your identity |
| `auto_lint.py` | 3-level analysis: syntax fix + logic bugs + AI suggestions |
| `auto_preview.py` | Auto-open HTML in browser, run Python scripts |
| `version_history.py` | Undo/rollback any generated file |
| `multi_file_gen.py` | Generate full websites (HTML+CSS+JS) |
| `smart_builder.py` | Interactive builder: asks questions before creating |
| `project_builder.py` | Scaffold project structures |
| `code_explainer.py` | Explain any file in plain English |
| `code_fixer.py` | Fix/refactor code from clipboard |
| `code_checker.py` | Lint Python files for syntax errors |

### Browser & Desktop
| Module | What it does |
|--------|-------------|
| `browser_control.py` | Full browser automation (tabs, scroll, type, navigate) |
| `bookmarks.py` | Read real Brave/Chrome bookmarks, open by voice |
| `workflows.py` | Multi-step automations + custom workflow recording |
| `smart_click.py` | OCR-based element finding and clicking |
| `screen_reader.py` | Read screen text (window titles + clipboard + OCR) |

### Intelligence & Memory
| Module | What it does |
|--------|-------------|
| `memory.py` | Persistent memory + auto-learn from conversations |
| `adaptive.py` | Tracks usage patterns, suggests next actions |
| `proactive.py` | Detects when you're stuck, offers help |
| `personality.py` | 6 modes: default, casual, professional, funny, brief, teacher |
| `daily_brief.py` | Morning greeting with tasks, quote, system status |

### Productivity & Utilities
| Module | What it does |
|--------|-------------|
| `tasks.py` | Voice todo list with priorities |
| `timers.py` | Background voice reminders and timers |
| `notes.py` | Voice note-taking, saved to dated files |
| `logger.py` | Full conversation logging with timestamps |
| `calculator.py` | Instant math, percentages, conversions |
| `terminal.py` | Run shell commands by voice |
| `git_helper.py` | Git status, commit, push, pull by voice |
| `file_explorer.py` | Browse folders by voice |
| `web_search.py` | DuckDuckGo search (no API key) |

---

## 🗣️ Voice Commands Reference

### General
| Say | Action |
|-----|--------|
| "Hello" / any question | Chat with AI |
| "Be casual" / "Professional mode" | Switch personality |
| "What are my stats" | Usage statistics |
| "Stop" / "Goodbye" | Exit |

### Memory
| Say | Action |
|-----|--------|
| "Remember that my name is Mihir" | Store a fact |
| "What do you remember" | List memories |
| "Forget about my birthday" | Delete specific |
| *(Automatic)* | Auto-learns name, profession, preferences from chat |

### Coding
| Say | Action |
|-----|--------|
| "Write a Python function to sort a list" | Generate code |
| "Write an HTML portfolio page" | Generate + auto-open in browser |
| "Improve it" / "Add dark mode" | Iterate on last generation |
| "Undo" / "Rollback to version 2" | Revert changes |
| "Explain main.py" | Explain any file |
| "Fix my clipboard code" | Fix code from clipboard |
| "Check errors in my project" | Lint all Python files |
| "Create a website with home and about pages" | Multi-file generation |
| "Show me" / "Preview it" | Open in browser |
| "Run pip install flask" | Execute terminal command |

### Browser
| Say | Action |
|-----|--------|
| "Open YouTube" / "Open my Gmail bookmark" | Open sites |
| "Scroll down" / "Go back" / "New tab" | Navigate |
| "Click on Submit" | OCR-based smart clicking |
| "Open WhatsApp and send hello to Mom" | Multi-step workflow |
| "Show my bookmarks" | List all browser bookmarks |
| "Start recording" → do steps → "Stop recording" | Create custom workflow |
| "Run morning routine" | Replay saved workflow |

### Productivity
| Say | Action |
|-----|--------|
| "Add task finish report" | Add to todo list |
| "What are my tasks" | Show tasks |
| "Mark task 1 done" | Complete task |
| "Set timer 5 minutes" | Background timer |
| "Remind me in 10 minutes to drink water" | Voice reminder |
| "Take a note: project idea" | Save voice note |
| "Read my notes" | Play back today's notes |

### System
| Say | Action |
|-----|--------|
| "What time is it" | Current time |
| "Open Chrome" / "Close Notepad" | App control |
| "Volume up" / "Mute" | Media control |
| "What files are here" | Browse folders |
| "Git status" / "Commit message fixed bug" | Git by voice |
| "Search for Python tutorials" | Web search |
| "Calculate 15% of 2500" | Instant math |
| "Read my screen" | OCR screen text |

---

## 🔧 Technical Details

### Tech Stack
| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| AI Model | Ollama (local, qwen2.5:1.5b) |
| Speech-to-Text | Faster-Whisper (tiny model, CPU) |
| Text-to-Speech | pyttsx3 (Windows SAPI5) |
| OCR | Tesseract (for smart clicking) |
| Browser Automation | PyAutoGUI + keyboard shortcuts |
| Web Search | DuckDuckGo (no API key) |
| GUI | Tkinter (status dot) |

### System Requirements
- **OS**: Windows 10/11
- **RAM**: 8 GB minimum (4 GB free for Ollama)
- **CPU**: Any modern CPU (no GPU needed)
- **Microphone**: Any (auto-detects headsets)
- **Storage**: ~500 MB (models + dependencies)

### Performance
| Operation | Time |
|-----------|------|
| Audio recording | Real-time (0.6s silence detection) |
| Speech-to-text | ~400-800ms (trimmed audio) |
| AI response (first word) | ~3-5s (streaming) |
| TTS output | ~200-400ms per sentence |
| OCR click | ~800ms |
| System commands | <50ms |

---

## 📁 Project Structure

```
basic/
├── main.py               # Voice loop + audio + Ollama (streaming)
├── command_router.py     # Priority command dispatcher
├── smart_tts.py          # Adaptive text-to-speech
├── status_dot.py         # Floating status indicator
├── memory.py             # Persistent memory + auto-learn
├── adaptive.py           # Usage pattern learning
├── proactive.py          # Smart suggestions
├── personality.py        # 6 personality modes
├── daily_brief.py        # Startup greeting
├── coder.py              # Code gen + iteration + personalization
├── auto_lint.py          # 3-level code analysis
├── auto_preview.py       # Browser/script preview
├── version_history.py    # File version management
├── smart_builder.py      # Interactive project builder
├── multi_file_gen.py     # Multi-page website generator
├── project_builder.py    # Project scaffolder
├── code_explainer.py     # File explanation
├── code_fixer.py         # Clipboard code fixer
├── code_checker.py       # Python linter
├── browser_control.py    # Full browser automation
├── bookmarks.py          # Real browser bookmarks
├── workflows.py          # Multi-step + custom workflows
├── smart_click.py        # OCR-based clicking
├── screen_reader.py      # Screen text extraction
├── calculator.py         # Math/conversions
├── terminal.py           # Voice terminal
├── git_helper.py         # Git by voice
├── file_explorer.py      # Folder browsing
├── web_search.py         # DuckDuckGo search
├── tasks.py              # Voice todo list
├── timers.py             # Background reminders
├── notes.py              # Voice note-taking
├── logger.py             # Conversation logging
├── requirements.txt      # Python dependencies
├── memory.json           # Stored memories
├── tasks.json            # Saved tasks
├── nova_learning.json    # Adaptive learning data
├── custom_workflows.json # User-created workflows
├── .version_history/     # File versions
├── notes/                # Voice notes (dated)
├── logs/                 # Conversation logs (dated)
├── generated_code/       # Generated code files
├── generated_projects/   # Multi-file projects
└── output/               # Audio recordings
```

---

## 🎓 About This Project

Built as a degree project demonstrating:
- **Voice AI architecture** — modular, extensible, offline-first
- **Local LLM integration** — Ollama for zero-cost AI inference
- **Real-time speech processing** — Whisper STT + streaming TTS
- **Desktop automation** — browser control, OCR, system commands
- **Adaptive systems** — memory, learning, proactive assistance
- **Software engineering** — 33 modules, clean architecture, separation of concerns

---

## 📄 License

MIT License — free to use, modify, and distribute.
