"""OpenAI/vLLM client setup and JSON-schema call helper."""

from __future__ import annotations

import os

from openai import OpenAI
from pydantic import BaseModel, ValidationError


DEFAULT_BASE_URL = os.getenv("VLLM_URL", "http://llm-proxy:8000/v1")
DEFAULT_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")


DEFAULT_STOP_STRINGS = ["<tool_call>", "</tool_call>"]


def make_client(base_url: str = DEFAULT_BASE_URL) -> OpenAI:
    return OpenAI(base_url=base_url, api_key="EMPTY")


def json_schema_for(model_cls: type[BaseModel], name: str) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": model_cls.model_json_schema(),
        },
    }


def _compact_error_message(exc: ValidationError, max_chars: int = 1200) -> str:
    """Return a compact validation error for retry prompts."""
    text = str(exc)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + chr(10) + "... [validation error truncated]"


def _raw_output_diagnostic(raw: str, max_chars: int = 1000) -> str:
    """Return a bounded diagnostic snippet without echoing huge malformed JSON."""
    if len(raw) <= max_chars:
        return repr(raw)
    half = max_chars // 2
    prefix = raw[:half]
    suffix = raw[-half:]
    return repr(prefix + chr(10) + "... [invalid response truncated] ..." + chr(10) + suffix)


def _retry_instruction(exc: ValidationError, raw: str) -> str:
    """Construct a compact retry instruction without reinforcing bad output."""
    lines = [
        "Your previous response was invalid JSON or did not match the schema.",
        "Return the answer again from scratch as valid JSON matching the schema exactly.",
        "Do not continue, repair, or imitate the invalid response.",
        "Do not include markdown fences.",
        "Do not include comments.",
        "All strings must be closed.",
        "Do not put raw newlines inside string values.",
        "Do not create empty headings.",
        "Do not output extra keys not present in the schema.",
        "Do not output line_span, line_spans, line_sources, line_soures, evidence, or recursive children fields.",
        "Represent every span only as an object with present, start_line, and end_line.",
        "Never output a list of many individual line numbers; use only start_line and end_line.",
        "Use confidence values only from: high, medium, low.",
        "",
        "Compact parser error:",
        _compact_error_message(exc),
        "",
        "Brief invalid response diagnostic:",
        _raw_output_diagnostic(raw),
    ]
    return chr(10).join(lines)


def call_json_schema(
    *,
    client: OpenAI,
    model: str,
    messages: list[dict],
    schema_model: type[BaseModel],
    schema_name: str,
    max_tokens: int,
    retries: int = 1,
    debug: bool = False,
    temperature: float = 0.0,
    top_p: float = 1.0,
    seed: int | None = 0,
    stop: list[str] | None = None,
) -> BaseModel:
    """Call a vLLM/OpenAI-compatible chat endpoint with JSON-schema output.

    Defaults are intentionally deterministic. The helper also sets tool_choice="none"
    and stop strings for tool-call sentinels, since some chat templates may emit
    tool-call markers even when no tools are supplied.
    """
    last_raw: str | None = None
    last_error: Exception | None = None
    current_messages = list(messages)
    stop_strings = DEFAULT_STOP_STRINGS if stop is None else stop

    for _attempt in range(retries + 1):
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            stop=stop_strings,
            tool_choice="none",
            max_tokens=max_tokens,
            messages=current_messages,
            response_format=json_schema_for(schema_model, schema_name),
        )

        raw = response.choices[0].message.content or ""
        last_raw = raw

        try:
            return schema_model.model_validate_json(raw)
        except ValidationError as exc:
            last_error = exc
            if debug:
                print(chr(10) + "--- INVALID RAW MODEL OUTPUT repr ---")
                print(repr(raw))
                print(chr(10) + "--- VALIDATION ERROR ---")
                print(str(exc))

            current_messages = current_messages + [
                {
                    "role": "user",
                    "content": _retry_instruction(exc, raw),
                }
            ]

    if debug:
        print(chr(10) + "--- LAST RAW MODEL OUTPUT repr ---")
        print(repr(last_raw))
    raise RuntimeError(f"Model failed to produce valid {schema_name}: {last_error}")

