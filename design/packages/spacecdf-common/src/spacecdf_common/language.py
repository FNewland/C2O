"""UI / output language helpers shared by the AI layers (i18n packet C0).

SpaceCDF's user interface runs in English or French. The browser sends its
UI language with AI requests; the AI layers then ask the model to write in
that language. Everything else on the server (error strings, stored data,
deterministic agent output) stays English.

Only two languages are supported. Anything unrecognised falls back to
English, so existing callers and tests that expect English are unaffected.
"""
from __future__ import annotations

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "fr")
DEFAULT_LANGUAGE = "en"

# Appended to the system prompt when the UI language is French. The prompt
# files themselves stay English (one source of truth); the model is told to
# answer in French while leaving engineering identifiers untouched.
FRENCH_OUTPUT_INSTRUCTION = (
    "\n\n--- OUTPUT LANGUAGE ---\n"
    "Respond in French (international/European French, as used by ESA and "
    "CNES). Write all prose, headings, explanations and rationale in French. "
    "Keep the following exactly as given, untranslated: identifiers "
    "(element, requirement, interface and parameter IDs), standard numbers "
    "(e.g. ECSS-E-ST-10C, ECSS-Q-ST-30C, NASA SP-2016-6105), mnemonics, part "
    "numbers and product names, code, JSON keys and enum values, units and "
    "unit symbols (kg, W, dB, km, bit/s). In prose use the French decimal "
    "comma and a space before ; : ! ? but keep the decimal point inside "
    "code, JSON and tables of engineering values. If the requested output "
    "format is JSON, translate only free-text string values, never keys."
)


def normalize_language(value: str | None, default: str = DEFAULT_LANGUAGE) -> str:
    """Return 'en' or 'fr' for a language tag such as 'fr', 'fr-FR', 'FR_ca'.

    Also accepts an Accept-Language style list ("fr-FR,fr;q=0.9,en;q=0.8"),
    in which case the first entry wins. ``None``/empty/unknown → ``default``
    (itself normalised, so a bad default still yields 'en').
    """
    if default not in SUPPORTED_LANGUAGES:
        default = DEFAULT_LANGUAGE
    if not value:
        return default
    first = value.split(",")[0].split(";")[0].strip().lower()
    primary = first.replace("_", "-").split("-")[0]
    return primary if primary in SUPPORTED_LANGUAGES else default


def language_instruction(language: str | None) -> str:
    """System-prompt suffix for ``language`` ('' for English)."""
    return FRENCH_OUTPUT_INSTRUCTION if normalize_language(language) == "fr" else ""


def apply_language(system_prompt: str, language: str | None) -> str:
    """Return ``system_prompt`` with the output-language instruction appended.

    English returns the prompt unchanged (byte-identical).
    """
    return system_prompt + language_instruction(language)
