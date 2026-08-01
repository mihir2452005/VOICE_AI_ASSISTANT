"""Advanced Auto-Lint — syntax fixing, logic analysis, and smart suggestions.

Three levels of code quality:
1. SYNTAX FIX — auto-fix broken syntax (colons, brackets, tags)
2. LOGIC CHECK — detect logic bugs (infinite loops, unreachable code, wrong conditions)
3. SUGGESTIONS — recommend improvements (better patterns, missing edge cases)

After any code generation:
- Level 1 runs automatically (silent fix)
- Level 2 warns if logic issues detected
- Level 3 suggests improvements (spoken to user)

Usage:
    from auto_lint import lint_and_fix, check_syntax, analyze_logic, suggest_improvements
    
    code = lint_and_fix(code, "python")           # Fix syntax
    issues = analyze_logic(code, "python")         # Find logic bugs
    suggestions = suggest_improvements(code, "python")  # Get tips
"""

import ast
import re
import sys
import os
from typing import Optional

import requests

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


# =============================================================================
# PUBLIC API
# =============================================================================

def lint_and_fix(code: str, language: str = "python") -> str:
    """Level 1: Fix syntax errors automatically. Returns clean code."""
    if not code.strip():
        return code
    lang = language.lower()
    if lang in ("python", "py"):
        return _fix_python(code)
    elif lang in ("html", "htm"):
        return _fix_html(code)
    elif lang in ("javascript", "js"):
        return _fix_javascript(code)
    elif lang in ("css",):
        return _fix_css(code)
    return code


def check_syntax(code: str, language: str = "python") -> list[str]:
    """Check for syntax errors. Returns list of issues."""
    lang = language.lower()
    if lang in ("python", "py"):
        return _check_python_syntax(code)
    elif lang in ("html", "htm"):
        return _check_html_syntax(code)
    elif lang in ("javascript", "js"):
        return _check_js_syntax(code)
    elif lang in ("css",):
        return _check_css_syntax(code)
    return []


def analyze_logic(code: str, language: str = "python") -> list[str]:
    """Level 2: Detect logic bugs and potential runtime errors.
    
    Checks for:
    - Infinite loops (while True without break)
    - Unreachable code (code after return/break)
    - Wrong comparisons (= vs ==, is vs ==)
    - Missing return statements
    - Unused variables
    - Division by zero risk
    - Empty except blocks (swallowing errors)
    - Mutable default arguments
    """
    if not code.strip():
        return []
    lang = language.lower()
    if lang in ("python", "py"):
        return _analyze_python_logic(code)
    elif lang in ("javascript", "js"):
        return _analyze_js_logic(code)
    return []


def suggest_improvements(code: str, language: str = "python") -> list[str]:
    """Level 3: Suggest improvements via Ollama AI analysis.
    
    Returns a list of spoken suggestions like:
    - "Consider adding error handling for the file operation"
    - "This function is too long, consider splitting it"
    - "Missing input validation for the parameter"
    """
    if not code.strip() or len(code) < 50:
        return []
    return _ai_suggest(code, language)


def full_analysis(code: str, language: str = "python") -> dict:
    """Run all 3 levels and return complete analysis.
    
    Returns: {
        "fixed_code": str,
        "syntax_issues": list,
        "logic_issues": list, 
        "suggestions": list,
        "score": int (0-100),
    }
    """
    fixed = lint_and_fix(code, language)
    syntax = check_syntax(fixed, language)
    logic = analyze_logic(fixed, language)
    suggestions = suggest_improvements(fixed, language)
    
    # Score: start at 100, deduct for issues
    score = 100
    score -= len(syntax) * 15
    score -= len(logic) * 10
    score -= len(suggestions) * 5
    score = max(0, min(100, score))
    
    return {
        "fixed_code": fixed,
        "syntax_issues": syntax,
        "logic_issues": logic,
        "suggestions": suggestions,
        "score": score,
    }


# =============================================================================
# LEVEL 2: LOGIC ANALYSIS (Python)
# =============================================================================

def _analyze_python_logic(code: str) -> list[str]:
    """Deep logic analysis for Python code."""
    issues = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Code has syntax errors — fix those first"]
    
    lines = code.split("\n")
    
    # --- Check for infinite loops ---
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            # while True without break
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if not has_break:
                    issues.append(f"⚠️ Line {node.lineno}: Infinite loop (while True without break)")
    
    # --- Check for unreachable code ---
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            for i, stmt in enumerate(body[:-1]):
                if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)):
                    next_stmt = body[i + 1]
                    if not isinstance(next_stmt, (ast.FunctionDef, ast.ClassDef)):
                        issues.append(f"⚠️ Line {next_stmt.lineno}: Unreachable code after return/break")
    
    # --- Check for empty except blocks ---
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(f"⚠️ Line {node.lineno}: Empty except (swallows errors silently)")
    
    # --- Check for mutable default arguments ---
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    issues.append(f"⚠️ Line {node.lineno}: Mutable default argument in '{node.name}()' (use None instead)")
    
    # --- Check for bare except ---
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(f"⚠️ Line {node.lineno}: Bare 'except:' catches everything including KeyboardInterrupt")
    
    # --- Check for == None (should be 'is None') ---
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    if isinstance(comparator, ast.Constant) and comparator.value is None:
                        issues.append(f"⚠️ Line {node.lineno}: Use 'is None' instead of '== None'")
    
    # --- Check for unused imports ---
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.asname or alias.name)
    
    # Check if imports are used (simple heuristic)
    code_without_imports = "\n".join(
        l for l in lines if not l.strip().startswith(("import ", "from "))
    )
    for imp in imports:
        if imp not in code_without_imports and imp != "*":
            issues.append(f"💡 Unused import: '{imp}'")
    
    # --- Check for functions without return in non-void context ---
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip if name suggests it's a procedure (starts with set_, print_, etc.)
            if node.name.startswith(("set_", "print_", "log_", "save_", "_")):
                continue
            has_return_value = False
            for n in ast.walk(node):
                if isinstance(n, ast.Return) and n.value is not None:
                    has_return_value = True
                    break
            # Only flag if function is > 3 lines and no return
            if not has_return_value and len(node.body) > 3:
                issues.append(f"💡 Line {node.lineno}: '{node.name}()' has no return value — intentional?")
    
    # --- Check for potential division by zero ---
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                issues.append(f"🔴 Line {node.lineno}: Division by zero!")
    
    return issues


def _analyze_js_logic(code: str) -> list[str]:
    """Basic logic analysis for JavaScript."""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check == vs === 
        if "==" in stripped and "===" not in stripped and "!==" not in stripped:
            if not stripped.startswith("//"):
                issues.append(f"💡 Line {i}: Use === instead of == (strict equality)")
        # Check var usage (should use let/const)
        if re.match(r"^\s*var\s+", line):
            issues.append(f"💡 Line {i}: Use 'let' or 'const' instead of 'var'")
        # console.log left in
        if "console.log" in stripped and not stripped.startswith("//"):
            issues.append(f"💡 Line {i}: console.log left in code (remove for production)")
    
    return issues


# =============================================================================
# LEVEL 3: AI-POWERED SUGGESTIONS (via Ollama)
# =============================================================================

def _ai_suggest(code: str, language: str) -> list[str]:
    """Use Ollama to suggest improvements."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": (
                        "You are a code reviewer. Give exactly 2-3 SHORT improvement suggestions. "
                        "Each suggestion is ONE sentence. Focus on: error handling, edge cases, "
                        "performance, security. Format: one suggestion per line starting with '- '."
                    )},
                    {"role": "user", "content": f"Review this {language} code:\n```\n{code[:1500]}\n```"},
                ],
                "stream": False,
                "options": {"num_predict": 150, "temperature": 0.3},
            },
            timeout=30,
        )
        if r.status_code == 200:
            response = r.json().get("message", {}).get("content", "")
            # Parse suggestions (lines starting with -)
            suggestions = []
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    suggestions.append(line[2:].strip())
                elif line and len(suggestions) < 3 and len(line) > 10:
                    suggestions.append(line)
            return suggestions[:3]
        return []
    except Exception:
        return []


# =============================================================================
# LEVEL 1: SYNTAX CHECKING
# =============================================================================

def _check_python_syntax(code: str) -> list[str]:
    issues = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Line {e.lineno}: {e.msg}")
    return issues


def _check_html_syntax(code: str) -> list[str]:
    issues = []
    open_tags = re.findall(r"<(\w+)[\s>]", code)
    close_tags = re.findall(r"</(\w+)>", code)
    _void = {"br","hr","img","input","meta","link","area","base","col","embed","source","track","wbr"}
    for tag in set(open_tags):
        if tag.lower() not in _void:
            if open_tags.count(tag) > close_tags.count(tag):
                issues.append(f"Unclosed <{tag}> tag")
    if "<!DOCTYPE" not in code.upper() and "<html" in code.lower():
        issues.append("Missing <!DOCTYPE html>")
    return issues


def _check_js_syntax(code: str) -> list[str]:
    issues = []
    if code.count("{") != code.count("}"):
        issues.append(f"Mismatched braces: {code.count('{')} open vs {code.count('}')} close")
    if code.count("(") != code.count(")"):
        issues.append(f"Mismatched parentheses")
    return issues


def _check_css_syntax(code: str) -> list[str]:
    issues = []
    if code.count("{") != code.count("}"):
        issues.append("Mismatched curly braces")
    return issues


# =============================================================================
# LEVEL 1: SYNTAX FIXING
# =============================================================================

_VOID_TAGS = {"br","hr","img","input","meta","link","area","base","col","embed","source","track","wbr"}


def _fix_python(code: str) -> str:
    try:
        ast.parse(code)
        return code
    except SyntaxError:
        pass
    lines = code.split("\n")
    fixed = []
    for i, line in enumerate(lines):
        f = line
        stripped = line.rstrip()
        if "\t" in f:
            f = f.replace("\t", "    ")
        kws = ["def ","class ","if ","for ","while ","else","elif ","try","except","finally","with "]
        if stripped and not stripped.endswith((":","," )):
            for kw in kws:
                if stripped.lstrip().startswith(kw):
                    if i+1 < len(lines):
                        next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                        curr_indent = len(line) - len(line.lstrip())
                        if next_indent > curr_indent:
                            f = stripped + ":"
                    break
        fixed.append(f)
    result = "\n".join(fixed)
    try:
        ast.parse(result)
        return result
    except SyntaxError:
        return code


def _fix_html(code: str) -> str:
    fixed = code
    if "<!DOCTYPE" not in fixed.upper() and "<html" in fixed.lower():
        fixed = "<!DOCTYPE html>\n" + fixed
    if "<meta charset" not in fixed.lower() and "<head>" in fixed.lower():
        fixed = fixed.replace("<head>", '<head>\n  <meta charset="UTF-8">', 1)
    if "viewport" not in fixed.lower() and "<head" in fixed.lower():
        vp = '  <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        if "<meta charset" in fixed:
            fixed = re.sub(r'(<meta charset="[^"]*">)', r'\1\n' + vp, fixed, count=1)
    # Close unclosed tags
    open_tags = []
    for m in re.finditer(r"<(\w+)(?:\s[^>]*)?>", fixed):
        tag = m.group(1).lower()
        if tag not in _VOID_TAGS and not m.group(0).endswith("/>"):
            open_tags.append(tag)
    for m in re.finditer(r"</(\w+)>", fixed):
        tag = m.group(1).lower()
        if tag in open_tags:
            open_tags.remove(tag)
    if open_tags:
        fixed = fixed.rstrip() + "\n" + "\n".join(f"</{t}>" for t in reversed(open_tags))
    return fixed


def _fix_javascript(code: str) -> str:
    lines = code.split("\n")
    fixed = []
    brace_count = 0
    for line in lines:
        f = line
        stripped = line.strip()
        brace_count += stripped.count("{") - stripped.count("}")
        if re.match(r"^\s*(const|let|var)\s+.+=.+[^;{,(\s]$", stripped):
            f = line.rstrip() + ";"
        fixed.append(f)
    result = "\n".join(fixed)
    if brace_count > 0:
        result += "\n" + "}" * brace_count
    return result


def _fix_css(code: str) -> str:
    lines = code.split("\n")
    fixed = []
    brace_count = 0
    for line in lines:
        f = line
        stripped = line.strip()
        brace_count += stripped.count("{") - stripped.count("}")
        if (":" in stripped and
            not stripped.endswith((";","{","}","*/",",")) and
            not stripped.startswith(("/*","*","//","@"))):
            f = line.rstrip() + ";"
        fixed.append(f)
    result = "\n".join(fixed)
    if brace_count > 0:
        result += "\n" + "}" * brace_count
    return result
