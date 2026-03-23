"""
utils/prompt_builder.py
-----------------------
Builds COSTAR-framework prompts for QA requirement generation.
"""

from typing import List

_SECTION_RULES = {
    "Functional Requirements": (
        "## Functional Requirements\n"
        "- Generate at least {n} per page\n"
        "- Each MUST start with: \"System shall\"\n"
        "- Focus on user actions and system responses, not visual display\n"
        "- Format: bulleted list"
    ),
    "User Stories": (
        "## User Stories\n"
        "- Generate at least {n} per page\n"
        "- Format: \"As a [role], I want [action] so that [benefit]\"\n"
        "- Base only on UI elements provided"
    ),
    "Acceptance Criteria": (
        "## Acceptance Criteria\n"
        "- Generate {n} scenarios per page\n"
        "- Strict Given / When / Then — one clause per line\n"
        "- Reference EXACT button/input names from the UI\n"
        "- Each scenario independently testable"
    ),
    "Edge Cases": (
        "## Edge Cases\n"
        "- Generate at least {n} per page\n"
        "- Each MUST start with: \"System should handle\"\n"
        "- Cover: empty inputs, invalid formats, boundary values, timeouts\n"
        "- Statements only — never questions"
    ),
    "Test Cases": (
        "## Test Cases\n"
        "- Generate at least {n} per page\n"
        "- Format: | Test ID | Description | Steps | Expected Result |\n"
        "- Cover happy path AND negative scenarios"
    ),
}


def build_prompt(
    page_content: str,
    sections: List[str],
    max_scenarios: int = 4,
    strict_mode: bool = True,
) -> str:
    section_blocks = "\n\n".join(
        _SECTION_RULES[s].format(n=max_scenarios)
        for s in sections if s in _SECTION_RULES
    )
    section_headers = "\n".join(f"## {s}" for s in sections)

    strict = ""
    if strict_mode:
        strict = (
            "\n---\n"
            "## STRICT MODE\n"
            "NEVER: invent UI elements · write questions · add commentary outside markdown\n"
            "ALWAYS: use exact UI names · start FRs with 'System shall' · use Given/When/Then\n"
        )

    return f"""## CONTEXT
You are a Senior QA Engineer generating production-ready QA documentation.

## OBJECTIVE
Analyse every page in the Website Content below and generate QA documentation.
Cover EVERY page — do not skip any.

## SECTIONS TO GENERATE
{section_blocks}

## STYLE & TONE
Technical, precise, zero ambiguity. Every statement must be independently testable.

## AUDIENCE
QA Engineers writing automated tests · Manual testers · Product Managers
{strict}
## REQUIRED OUTPUT FORMAT (for each page)

# Feature: <Page Name>

{section_headers}

---

## WEBSITE CONTENT

{page_content}

---
Output ONLY markdown. Cover ALL pages above.
""".strip()
