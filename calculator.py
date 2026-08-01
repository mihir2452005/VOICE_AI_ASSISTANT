"""Quick Math Calculator — instant math without calling Ollama.

Handles spoken math like:
- "Calculate 15% of 2500"
- "What's 145 divided by 7"
- "12 times 8"
- "Square root of 144"
- "Convert 100 fahrenheit to celsius"

Usage from main.py:
    from calculator import handle_math
    result = handle_math("what's 25 times 4")
    if result:
        speak(result)  # "25 × 4 = 100"
"""

import re
import math
from typing import Optional


# =============================================================================
# WORD-TO-NUMBER CONVERSION
# =============================================================================

_WORD_NUMS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
    "million": 1000000, "billion": 1000000000,
}


def _words_to_number(text: str) -> Optional[float]:
    """Try to convert a word-based number to float."""
    text = text.strip().lower()

    # Already a number?
    try:
        return float(text.replace(",", ""))
    except ValueError:
        pass

    # Simple word numbers
    if text in _WORD_NUMS:
        return float(_WORD_NUMS[text])

    # Compound: "twenty five" → 25
    parts = text.split()
    if len(parts) == 2 and parts[0] in _WORD_NUMS and parts[1] in _WORD_NUMS:
        return float(_WORD_NUMS[parts[0]] + _WORD_NUMS[parts[1]])

    return None


# =============================================================================
# MATH OPERATIONS
# =============================================================================

def _extract_numbers(text: str) -> list[float]:
    """Extract all numbers (digits or words) from text."""
    numbers = []

    # Find digit-based numbers first
    for match in re.finditer(r"[\d,]+\.?\d*", text):
        try:
            numbers.append(float(match.group().replace(",", "")))
        except ValueError:
            pass

    # If no digit numbers found, try word numbers
    if not numbers:
        for word in text.split():
            n = _words_to_number(word)
            if n is not None:
                numbers.append(n)

    return numbers


def _format_result(value: float) -> str:
    """Format a number nicely for speech."""
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


# =============================================================================
# PATTERN MATCHING
# =============================================================================

_MATH_PATTERNS = [
    # Percentage: "15% of 2500", "what's 20 percent of 500"
    (r"(\d+\.?\d*)\s*(%|percent)\s*(of)\s*(\d+\.?\d*)",
     lambda m: (float(m.group(1)) / 100) * float(m.group(4)),
     lambda m: f"{m.group(1)}% of {m.group(4)}"),

    # Basic ops with words: "12 plus 8", "100 minus 30"
    (r"(\d+\.?\d*)\s*(plus|and|\+)\s*(\d+\.?\d*)",
     lambda m: float(m.group(1)) + float(m.group(3)),
     lambda m: f"{m.group(1)} + {m.group(3)}"),

    (r"(\d+\.?\d*)\s*(minus|subtract|\-)\s*(\d+\.?\d*)",
     lambda m: float(m.group(1)) - float(m.group(3)),
     lambda m: f"{m.group(1)} - {m.group(3)}"),

    (r"(\d+\.?\d*)\s*(times|multiplied by|x|×|\*)\s*(\d+\.?\d*)",
     lambda m: float(m.group(1)) * float(m.group(3)),
     lambda m: f"{m.group(1)} × {m.group(3)}"),

    (r"(\d+\.?\d*)\s*(divided by|over|÷|/)\s*(\d+\.?\d*)",
     lambda m: float(m.group(1)) / float(m.group(3)) if float(m.group(3)) != 0 else float('inf'),
     lambda m: f"{m.group(1)} ÷ {m.group(3)}"),

    # Power: "2 to the power of 10", "3 squared", "5 cubed"
    (r"(\d+\.?\d*)\s*(to the power of|power|raised to)\s*(\d+\.?\d*)",
     lambda m: float(m.group(1)) ** float(m.group(3)),
     lambda m: f"{m.group(1)}^{m.group(3)}"),

    (r"(\d+\.?\d*)\s*squared",
     lambda m: float(m.group(1)) ** 2,
     lambda m: f"{m.group(1)}²"),

    (r"(\d+\.?\d*)\s*cubed",
     lambda m: float(m.group(1)) ** 3,
     lambda m: f"{m.group(1)}³"),

    # Square root
    (r"square root of\s*(\d+\.?\d*)",
     lambda m: math.sqrt(float(m.group(1))),
     lambda m: f"√{m.group(1)}"),

    # Temperature conversion
    (r"(\d+\.?\d*)\s*(fahrenheit|f)\s*(to|in)\s*(celsius|c)",
     lambda m: (float(m.group(1)) - 32) * 5/9,
     lambda m: f"{m.group(1)}°F to °C"),

    (r"(\d+\.?\d*)\s*(celsius|c)\s*(to|in)\s*(fahrenheit|f)",
     lambda m: float(m.group(1)) * 9/5 + 32,
     lambda m: f"{m.group(1)}°C to °F"),

    # Distance: km to miles, miles to km
    (r"(\d+\.?\d*)\s*(km|kilometers?)\s*(to|in)\s*(miles?)",
     lambda m: float(m.group(1)) * 0.621371,
     lambda m: f"{m.group(1)} km to miles"),

    (r"(\d+\.?\d*)\s*(miles?)\s*(to|in)\s*(km|kilometers?)",
     lambda m: float(m.group(1)) * 1.60934,
     lambda m: f"{m.group(1)} miles to km"),
]

# Trigger words that indicate math intent
_MATH_TRIGGERS = [
    "calculate", "what's", "what is", "how much is",
    "plus", "minus", "times", "divided", "multiply",
    "percent", "square root", "power", "squared", "cubed",
    "convert", "fahrenheit", "celsius", "km to", "miles to",
]


def handle_math(text: str) -> Optional[str]:
    """Try to solve a math problem from spoken text.

    Returns:
        Answer string if math detected, None if not a math query.
    """
    text_lower = text.lower().strip()

    # Quick check: does it look like math?
    if not any(trigger in text_lower for trigger in _MATH_TRIGGERS):
        # Also check for bare number patterns like "12 times 8"
        if not re.search(r"\d+\s*(plus|minus|times|divided|x|/|\+|\-|\*)", text_lower):
            return None

    # Try each pattern
    for pattern, calc_fn, expr_fn in _MATH_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            try:
                result = calc_fn(match)
                expr = expr_fn(match)
                formatted = _format_result(result)
                return f"{expr} = {formatted}"
            except (ValueError, ZeroDivisionError):
                return "Can't divide by zero!"
            except Exception:
                continue

    return None
