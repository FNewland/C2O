"""FSW Generation — flight software code from ConOps and design data."""
from __future__ import annotations

import re
from typing import Any

from spacecdf_ai.capabilities.base import BaseCapability
from spacecdf_ai.context import build_study_context


class FSWCapability(BaseCapability):
    name = "fsw_generation"
    prompt_file = "fsw_generator.txt"
    model_tier = "heavy"

    def build_user_message(
        self,
        study: dict | None = None,
        elements: list[dict] | None = None,
        conops: dict | None = None,
        language: str = "c",
        **kwargs: Any,
    ) -> str:
        parts: list[str] = []

        parts.append(f"Generate flight software in {language.upper()} for this spacecraft.\n")

        if study:
            ctx = build_study_context(study, elements)
            parts.append(ctx)

        if conops:
            modes = conops.get("modes", [])
            if modes:
                parts.append(f"\n## Operational Modes ({len(modes)})")
                for mode in modes:
                    parts.append(
                        f"- {mode.get('name', '?')}: "
                        f"power={mode.get('power_w', '?')}W, "
                        f"data_rate={mode.get('data_rate_mbps', '?')}Mbps, "
                        f"pointing={mode.get('pointing_mode', '?')}"
                    )
            transitions = conops.get("transitions", [])
            if transitions:
                parts.append(f"\n## Mode Transitions ({len(transitions)})")
                for t in transitions:
                    parts.append(
                        f"- {t.get('from', '?')} -> {t.get('to', '?')}: "
                        f"{t.get('condition', '?')}"
                    )

        return "\n".join(parts)

    def parse_response(self, content: str) -> dict[str, Any]:
        # Parse ---FILE: xxx--- markers into a file dict
        files = _split_files(content)
        return {
            "content": content,
            "files": files,
            "file_count": len(files),
            "language": "c",
        }


def _split_files(content: str) -> dict[str, str]:
    """Split concatenated files by ---FILE: filename--- markers."""
    pattern = r"---FILE:\s*(.+?)\s*---"
    parts = re.split(pattern, content)

    files: dict[str, str] = {}
    # parts[0] is before first marker (preamble, skip)
    # then alternating: filename, content, filename, content, ...
    for i in range(1, len(parts) - 1, 2):
        filename = parts[i].strip()
        file_content = parts[i + 1].strip()
        # Strip markdown fences if present
        if file_content.startswith("```"):
            lines = file_content.split("\n")
            file_content = "\n".join(lines[1:])
        if file_content.endswith("```"):
            file_content = file_content[:-3].rstrip()
        files[filename] = file_content

    return files
