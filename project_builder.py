"""Project Scaffolder — generate multi-file projects by voice.

Say: "create a Flask todo app", "scaffold a calculator project"
Generates proper project structure with working boilerplate files.

Usage:
    from project_builder import handle_project
    result = handle_project("create a Flask hello world app")
    if result: speak(result)
"""

import os
import sys
import re
import json
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
PROJECTS_DIR = "projects"

_TRIGGERS = [
    "create a project", "scaffold a project", "build a project",
    "create a ", "scaffold a ", "build a ",
    "make a project", "start a project", "new project",
]


def handle_project(text: str) -> Optional[str]:
    """Scaffold a multi-file project from voice description.

    Returns summary string or None if not a project request.
    """
    text_lower = text.lower().strip()

    # Check if this is a project request
    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Skip if it's just "create a function" (handled by coder.py)
    if any(w in text_lower for w in ["function", "script", "class", "code for"]):
        return None

    print("🏗️ Building project...", end=" ")
    sys.stdout.flush()

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": (
                        "You are a project generator. Output a JSON object with:\n"
                        '{"name": "project-name", "files": {"filename": "content", ...}}\n'
                        "Include 2-4 files max. Make code working and complete.\n"
                        "Output ONLY the JSON, no explanation."
                    )},
                    {"role": "user", "content": f"Create project: {text}"},
                ],
                "stream": False,
                "options": {"num_predict": 1000, "temperature": 0.2},
            },
            timeout=90,
        )

        if r.status_code != 200:
            return "Project generation failed."

        response = r.json().get("message", {}).get("content", "")

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            print("(no valid JSON)")
            return "Couldn't generate project structure. Try simpler description."

        project_data = json.loads(json_match.group())
        name = project_data.get("name", "my_project")
        files = project_data.get("files", {})

        if not files:
            return "No files generated."

        # Create project directory
        project_path = os.path.join(PROJECTS_DIR, name)
        os.makedirs(project_path, exist_ok=True)

        # Write files
        for filepath, content in files.items():
            full_path = os.path.join(project_path, filepath)
            os.makedirs(os.path.dirname(full_path) if os.path.dirname(full_path) else project_path, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        print(f"Done!")
        print(f"  📁 Created: {project_path}/")
        for f in files:
            print(f"     └── {f}")
        sys.stdout.flush()

        return f"Created project '{name}' with {len(files)} files in the projects folder."

    except json.JSONDecodeError:
        return "Couldn't parse project structure. Try a simpler description."
    except Exception as e:
        return f"Project creation failed: {e}"
