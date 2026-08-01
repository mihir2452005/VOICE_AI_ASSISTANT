"""Command Router — priority-based voice command dispatcher.

Routes user speech to the correct handler module based on priority.
Higher priority handlers are checked first. If a handler returns a result,
it's used. If None, the next handler is tried.

This replaces the 200+ lines of if/elif chains in main.py.

Usage:
    from command_router import CommandRouter
    router = CommandRouter(speak_fn, listen_fn, logger, adaptive, proactive)
    result = router.route("open youtube")
    # result = {"response": "Opening YouTube", "action": "browser", "handled": True}
"""

import sys
import re
from typing import Optional, Callable


class CommandRouter:
    """Routes voice commands to handler modules by priority.
    
    Priority order (first match wins):
    1. Exit commands (stop, quit)
    2. Memory commands (remember, forget, recall)
    3. Task manager (add task, show tasks)
    4. Personality switch (be casual, professional mode)
    5. Smart builder (create a website — interactive)
    6. Browser control (open chrome, scroll, click)
    7. Bookmarks (show bookmarks, open X from bookmarks)
    8. Workflows (multi-step: open whatsapp and send...)
    9. System commands (volume, open app, time)
    10. Calculator (math expressions)
    11. Code generation (write a function, improve it)
    12. Auto-preview (show me, run it)
    13. Terminal (run command)
    14. Code explainer (explain file)
    15. Code fixer (fix clipboard)
    16. Project builder (scaffold project)
    17. Git (git status, commit)
    18. Code checker (lint files)
    19. File explorer (list files)
    20. Screen reader (read my screen)
    21. Web search (search for...)
    22. Ollama chat (everything else)
    """

    def __init__(self, speak_fn, listen_fn, logger, adaptive, proactive, memory, persona):
        self._speak = speak_fn
        self._listen = listen_fn
        self._logger = logger
        self._adaptive = adaptive
        self._proactive = proactive
        self._memory = memory
        self._persona = persona

    def route(self, text: str) -> dict:
        """Route a voice command to the appropriate handler.
        
        Returns: {
            "response": str (what to speak),
            "action": str (action type for tracking),
            "handled": bool,
            "exit": bool (True if user wants to quit),
        }
        """
        text_lower = text.lower().strip()

        # 1. Exit
        if text_lower in ("stop", "quit", "exit", "goodbye", "bye"):
            return {"response": "Goodbye!", "action": "exit", "handled": True, "exit": True}

        # 2. Memory
        result = self._handle_memory(text, text_lower)
        if result:
            return result

        # 3. Tasks
        result = self._try_handler("tasks", "handle_task_command", text, "task")
        if result:
            return result

        # 3b. Timers & reminders
        result = self._try_handler("timers", "handle_timer_command", text, "timer")
        if result:
            return result

        # 3c. Voice notes
        result = self._try_handler("notes", "handle_note_command", text, "note")
        if result:
            return result

        # 4. Personality
        result = self._handle_personality(text, text_lower)
        if result:
            return result

        # 5. Smart builder (interactive)
        result = self._handle_smart_builder(text, text_lower)
        if result:
            return result

        # 6. Browser
        result = self._try_handler("browser_control", "handle_browser", text, "browser")
        if result:
            return result

        # 6b. Smart click (find and click elements on screen)
        result = self._try_handler("smart_click", "handle_smart_click", text, "click")
        if result:
            return result

        # 7. Bookmarks
        result = self._try_handler("bookmarks", "handle_bookmark_command", text, "bookmark")
        if result:
            return result

        # 8. Workflows
        result = self._try_handler("workflows", "handle_workflow", text, "workflow")
        if result:
            return result

        # 8b. Custom workflows (record/play)
        result = self._try_handler("workflows", "handle_custom_workflow", text, "custom_workflow")
        if result:
            return result

        # 9. System commands
        result = self._try_handler("system_commands", "handle_command", text, "system_cmd")
        if result:
            return result

        # 9b. Version history (undo, rollback)
        result = self._try_handler("version_history", "handle_version_command", text, "version")
        if result:
            return result

        # 10. Calculator
        result = self._try_handler("calculator", "handle_math", text, "math")
        if result:
            return result

        # 11. Code generation
        result = self._handle_coder(text)
        if result:
            return result

        # 12. Preview
        result = self._try_handler("auto_preview", "handle_preview_command", text, "preview")
        if result:
            return result

        # 13. Terminal
        result = self._try_handler("terminal", "handle_terminal", text, "terminal")
        if result:
            return result

        # 14. Code explainer
        result = self._try_handler("code_explainer", "handle_explain", text, "explain")
        if result:
            return result

        # 15. Code fixer
        result = self._try_handler("code_fixer", "handle_clipboard_fix", text, "fix")
        if result:
            return result

        # 16. Project builder
        result = self._try_handler("project_builder", "handle_project", text, "project")
        if result:
            return result

        # 17. Git
        result = self._try_handler("git_helper", "handle_git", text, "git")
        if result:
            return result

        # 18. Code checker
        result = self._try_handler("code_checker", "handle_check", text, "lint")
        if result:
            return result

        # 19. File explorer
        result = self._try_handler("file_explorer", "handle_explore", text, "explore")
        if result:
            return result

        # 20. Screen reader
        result = self._try_handler("screen_reader", "handle_screen_command", text, "screen")
        if result:
            return result

        # 21. Web search (check before Ollama)
        result = self._handle_search(text, text_lower)
        if result:
            return result

        # 22. Default: Ollama chat
        return {"response": None, "action": "chat", "handled": False, "exit": False}


    # --- Private handler helpers ---

    def _try_handler(self, module_name: str, func_name: str, text: str, action: str) -> Optional[dict]:
        """Try to call a handler function from a module. Returns result or None."""
        try:
            import importlib
            mod = importlib.import_module(module_name)
            handler = getattr(mod, func_name, None)
            if handler:
                result = handler(text)
                if result:
                    return {"response": result, "action": action, "handled": True, "exit": False}
        except Exception as e:
            print(f"  ⚠️ {module_name} error: {e}", file=sys.stderr)
        return None

    def _handle_memory(self, text: str, text_lower: str) -> Optional[dict]:
        """Handle memory commands (remember, forget, recall)."""
        # Clear all
        if "clear memory" in text_lower or "forget everything" in text_lower:
            self._memory.forget_all()
            return {"response": "Memory cleared. I've forgotten everything.", "action": "memory", "handled": True, "exit": False}

        # Remember
        if "remember that" in text_lower or "remember my" in text_lower:
            for trigger in ["remember that ", "remember my "]:
                if trigger in text_lower:
                    fact = text[text_lower.find(trigger) + len(trigger):]
                    break
            else:
                fact = text
            category = "personal" if "my " in text_lower else "general"
            self._memory.remember(category, fact.strip())
            print(f"   💾 Stored: [{category}] {fact.strip()}")
            sys.stdout.flush()
            return {"response": "Got it, I'll remember that.", "action": "memory", "handled": True, "exit": False}

        # Recall
        if "what do you remember" in text_lower or "what do you know about" in text_lower:
            if self._memory.count == 0:
                return {"response": "I don't have any memories stored yet.", "action": "memory", "handled": True, "exit": False}
            return {"response": f"I remember {self._memory.count} things about you.", "action": "memory", "handled": True, "exit": False}

        # Forget specific
        if "forget about" in text_lower or "forget my" in text_lower:
            for trigger in ["forget about ", "forget my "]:
                if trigger in text_lower:
                    query = text[text_lower.find(trigger) + len(trigger):].strip()
                    break
            else:
                query = ""
            if query:
                removed = self._memory.forget(query)
                return {"response": f"Done. Forgot {removed} things about {query}.", "action": "memory", "handled": True, "exit": False}

        return None

    def _handle_personality(self, text: str, text_lower: str) -> Optional[dict]:
        """Handle personality switch commands."""
        new_mode = self._persona.detect_switch(text)
        if new_mode:
            self._persona.switch(new_mode)
            return {"response": f"Switched to {self._persona.mode_display} mode. {self._persona.current_emoji}", "action": "personality", "handled": True, "exit": False}

        if "list modes" in text_lower or "what modes" in text_lower:
            return {"response": self._persona.list_modes(), "action": "personality", "handled": True, "exit": False}

        return None

    def _handle_smart_builder(self, text: str, text_lower: str) -> Optional[dict]:
        """Handle smart builder (interactive project creation)."""
        from smart_builder import _TRIGGERS as build_triggers
        if any(t in text_lower for t in build_triggers):
            from smart_builder import SmartBuilder
            builder = SmartBuilder(speak_fn=self._speak, listen_fn=self._listen)
            result = builder.handle(text)
            if result:
                return {"response": result, "action": "project", "handled": True, "exit": False}
        return None

    def _handle_coder(self, text: str) -> Optional[dict]:
        """Handle code generation with auto-preview."""
        from coder import handle_code_request
        code_result = handle_code_request(text)
        if code_result:
            # Auto-preview HTML
            if code_result.get("file") and code_result.get("language", "").lower() in ("html", "htm", "py"):
                try:
                    from auto_preview import auto_preview
                    auto_preview(code_result["file"])
                except Exception:
                    pass
            return {"response": code_result["summary"], "action": "code_gen", "handled": True, "exit": False}
        return None

    def _handle_search(self, text: str, text_lower: str) -> Optional[dict]:
        """Handle web search."""
        search_triggers = [
            "search for", "search", "google", "look up", "find",
            "what is the latest", "news about", "weather",
            "who is", "what happened", "price of",
        ]
        query = None
        for trigger in search_triggers:
            if trigger in text_lower:
                idx = text_lower.find(trigger)
                query = text[idx + len(trigger):].strip()
                if len(query) < 3:
                    query = text
                break

        if not query:
            return None

        from web_search import web_search
        print(f"🔍 Searching: \"{query}\"")
        sys.stdout.flush()
        results = web_search(query)
        if results:
            return {"response": None, "action": "search", "handled": False, "exit": False,
                    "search_context": f"Search results for '{query}':\n{results}"}
        return None
