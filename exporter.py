"""
utils/exporter.py
-----------------
Export generated QA markdown to .md, .json, and .txt formats.
"""

import json
import re
from datetime import datetime, timezone
from typing import List


def export_markdown(content: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        "# QA Requirements Documentation\n\n"
        f"> **Generated:** {ts}  \n"
        "> **Engine:** GenAI QA Generator · Groq API  \n\n"
        "---\n\n"
        + content +
        "\n\n---\n*Auto-generated. Review before use in production.*"
    )


def export_json(content: str, urls: List[str]) -> str:
    features = _parse_to_features(content)
    doc = {
        "metadata": {
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "generator":     "GenAI QA Requirement Generator",
            "source_urls":   urls,
            "feature_count": len(features),
        },
        "features": features,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False)


def _parse_to_features(content: str) -> list:
    """Parse COSTAR markdown output into structured feature dicts."""
    features, feat, sect, scen = [], None, None, None

    _MAP = {
        "functional":  "functional_requirements",
        "user stor":   "user_stories",
        "acceptance":  "acceptance_criteria",
        "edge":        "edge_cases",
        "test case":   "test_cases",
    }

    def flush():
        nonlocal scen
        if feat and sect == "acceptance_criteria" and scen and scen.get("steps"):
            feat["acceptance_criteria"].append(dict(scen))
        scen = None

    for line in content.splitlines():
        s = line.strip()
        if not s:
            continue

        if re.match(r"^#\s", s):           # Feature header
            flush()
            if feat:
                features.append(feat)
            feat = {k: [] for k in ["name","functional_requirements","user_stories",
                                     "acceptance_criteria","edge_cases","test_cases"]}
            feat["name"] = re.sub(r"^#+\s*(Feature:)?\s*", "", s).strip()
            sect = None

        elif re.match(r"^##\s", s) and feat:   # Section header
            flush()
            h = s.lstrip("#").strip().lower()
            sect = next((v for k, v in _MAP.items() if k in h), None)

        elif re.match(r"^###\s", s) and feat and sect == "acceptance_criteria":
            flush()
            scen = {"title": s.lstrip("#").strip(), "steps": []}

        elif re.match(r"^(given|when|then|and)\s", s, re.I) and feat and sect == "acceptance_criteria":
            if scen is None:
                scen = {"title": "Scenario", "steps": []}
            scen["steps"].append(s)

        elif feat and sect and sect != "acceptance_criteria":
            t = re.sub(r"^[-*•]\s+", "", s)
            t = re.sub(r"^\d+[.)]\s+", "", t).strip()
            if t and t not in feat[sect]:
                feat[sect].append(t)

    flush()
    if feat:
        features.append(feat)
    return features
