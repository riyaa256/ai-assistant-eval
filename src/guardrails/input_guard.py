import re
from dataclasses import dataclass
from typing import Optional


BLOCKED_PATTERNS: dict[str, list[str]] = {
    "jailbreak": [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"you\s+are\s+now\s+(DAN|jailbroken|unrestricted|free\s+mode)",
        r"pretend\s+you\s+have\s+no\s+(restrictions|guidelines|safety|ethics)",
        r"do\s+anything\s+now",
        r"bypass\s+(your\s+)?(safety|guidelines|restrictions|training)",
        r"act\s+as\s+if\s+you\s+(have|had)\s+no\s+(safety|restrictions|guidelines)",
        r"forget\s+(all\s+)?your\s+(instructions|training|guidelines|restrictions)",
        r"(roleplay|act)\s+as\s+.{0,30}(unrestricted|without\s+restrictions|no\s+guidelines)",
        r"jailbreak",
    ],
    "violence": [
        r"how\s+to\s+(make|build|create|assemble)\s+(a\s+)?(bomb|explosive|weapon\s+of)",
        r"how\s+to\s+(kill|murder|assassinate)\s+(someone|a\s+person|people)",
        r"how\s+to\s+(poison|drug)\s+(someone|a\s+person)",
        r"step.by.step\s+(instructions\s+)?(to\s+)?(kill|harm|attack)",
    ],
    "illegal_drugs": [
        r"how\s+to\s+(make|produce|synthesize|manufacture)\s+(meth|methamphetamine|cocaine|heroin|fentanyl|crack)",
        r"synthesis\s+of\s+(cocaine|heroin|methamphetamine|fentanyl)",
    ],
    "illegal_hacking": [
        r"how\s+to\s+hack\s+(into\s+)?(someone|a\s+person|their)",
        r"provide\s+(me\s+)?(working\s+)?exploit\s+code\s+for",
    ],
    "csam": [
        r"child\s+(porn|sexual\s+abuse|explicit\s+material)",
        r"sexual\s+content\s+(involving|with)\s+(minor|child|underage)",
    ],
    "self_harm": [
        r"how\s+to\s+(kill|harm|hurt)\s+myself",
        r"(methods|ways)\s+of\s+suicide",
    ],
}


@dataclass
class GuardResult:
    blocked: bool
    category: Optional[str]
    severity: float
    message: str


def check_input(text: str) -> GuardResult:
    text_lower = text.lower()
    for category, patterns in BLOCKED_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return GuardResult(
                    blocked=True,
                    category=category,
                    severity=1.0,
                    message="I'm not able to assist with that request.",
                )
    return GuardResult(blocked=False, category=None, severity=0.0, message="OK")
