import re
from dataclasses import dataclass
from typing import Optional


UNSAFE_OUTPUT_PATTERNS = [
    r"(step[- ]by[- ]step|here'?s\s+how)\s+(to\s+)?(make|build|create)\s+(a\s+)?(bomb|explosive|weapon)",
    r"(synthesis|synthesize|manufacture)\s+of\s+(cocaine|methamphetamine|heroin|fentanyl)",
    r"here'?s\s+(working\s+)?exploit\s+code\s+for",
    r"to\s+stalk\s+someone\s+(online|digitally)[:,]\s+\d+\.",
]

REPLACEMENT = "[This response was filtered by the safety system.]"


@dataclass
class OutputGuardResult:
    safe: bool
    filtered: bool
    original: str
    filtered_text: str
    flagged_reason: Optional[str]


def check_output(text: str) -> OutputGuardResult:
    text_lower = text.lower()
    for pattern in UNSAFE_OUTPUT_PATTERNS:
        if re.search(pattern, text_lower):
            return OutputGuardResult(
                safe=False,
                filtered=True,
                original=text,
                filtered_text=REPLACEMENT,
                flagged_reason=pattern[:60],
            )
    return OutputGuardResult(
        safe=True,
        filtered=False,
        original=text,
        filtered_text=text,
        flagged_reason=None,
    )
