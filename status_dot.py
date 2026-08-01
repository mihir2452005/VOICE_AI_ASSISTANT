"""Status Dot — minimal floating indicator showing Nova's state.

A tiny 60x60px always-on-top circle that changes color:
- 🟢 Green = Idle (ready for input)
- 🟡 Yellow = Listening (mic active)
- 🔵 Blue = Thinking (Ollama processing)
- 🟣 Purple = Speaking (TTS active)
- 🔴 Red = Error

Uses tkinter (built-in, no install needed). Near-zero CPU/RAM impact.
Runs in a separate thread so it doesn't block the voice loop.

Usage:
    from status_dot import StatusDot
    dot = StatusDot()
    dot.start()
    dot.set_state("listening")  # Changes color
    dot.set_state("thinking")
    dot.set_state("speaking")
    dot.set_state("idle")
    dot.stop()
"""

import threading
import sys
from typing import Optional


# State → color mapping
COLORS = {
    "idle": "#22c55e",       # Green
    "listening": "#eab308",  # Yellow
    "thinking": "#3b82f6",   # Blue
    "speaking": "#a855f7",   # Purple
    "error": "#ef4444",      # Red
}

DOT_SIZE = 50
POSITION_X = 20  # pixels from right edge
POSITION_Y = 20  # pixels from top


class StatusDot:
    """Minimal floating status dot using tkinter."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._root = None
        self._canvas = None
        self._dot = None
        self._current_state = "idle"
        self._running = False

    def start(self):
        """Start the status dot in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_gui, daemon=True)
        self._thread.start()

    def stop(self):
        """Close the status dot."""
        self._running = False
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass

    def set_state(self, state: str):
        """Change the dot's color based on state.
        
        Args:
            state: One of "idle", "listening", "thinking", "speaking", "error"
        """
        if state == self._current_state:
            return
        self._current_state = state
        if self._root and self._canvas and self._dot:
            try:
                color = COLORS.get(state, COLORS["idle"])
                self._root.after(0, self._update_color, color)
            except Exception:
                pass

    def _update_color(self, color: str):
        """Update dot color on the GUI thread."""
        try:
            self._canvas.itemconfig(self._dot, fill=color, outline=color)
        except Exception:
            pass

    def _run_gui(self):
        """Create and run the tkinter window."""
        try:
            import tkinter as tk

            self._root = tk.Tk()
            self._root.title("")
            self._root.overrideredirect(True)  # No title bar
            self._root.attributes("-topmost", True)  # Always on top
            self._root.attributes("-transparentcolor", "black")  # Transparent bg

            # Position: top-right corner
            screen_w = self._root.winfo_screenwidth()
            x = screen_w - DOT_SIZE - POSITION_X
            y = POSITION_Y
            self._root.geometry(f"{DOT_SIZE}x{DOT_SIZE}+{x}+{y}")

            # Canvas with transparent background
            self._canvas = tk.Canvas(
                self._root, width=DOT_SIZE, height=DOT_SIZE,
                bg="black", highlightthickness=0
            )
            self._canvas.pack()

            # Draw the dot (circle)
            padding = 5
            color = COLORS["idle"]
            self._dot = self._canvas.create_oval(
                padding, padding,
                DOT_SIZE - padding, DOT_SIZE - padding,
                fill=color, outline=color
            )

            # Allow dragging
            self._canvas.bind("<B1-Motion>", self._on_drag)

            self._root.mainloop()

        except Exception as e:
            print(f"  ⚠️ Status dot failed: {e}", file=sys.stderr)

    def _on_drag(self, event):
        """Allow user to drag the dot around."""
        try:
            x = self._root.winfo_x() + event.x - DOT_SIZE // 2
            y = self._root.winfo_y() + event.y - DOT_SIZE // 2
            self._root.geometry(f"+{x}+{y}")
        except Exception:
            pass


# Global instance
_dot: Optional[StatusDot] = None


def get_dot() -> StatusDot:
    """Get or create the global status dot."""
    global _dot
    if _dot is None:
        _dot = StatusDot()
        _dot.start()
    return _dot


def set_state(state: str):
    """Quick function to set state from anywhere."""
    try:
        get_dot().set_state(state)
    except Exception:
        pass
