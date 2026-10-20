"""Claude calls. Every step asks for JSON matching a pydantic model."""
from __future__ import annotations

import json
import os
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

MODEL = os.environ.get("CONTENT_ENGINE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("CONTENT_ENGINE_EFFORT", "medium")

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    pass


def json_schema(model: type[BaseModel]) -> dict:
    """Pydantic schema tightened for structured outputs: no extra keys, every field required."""
    schema = model.model_json_schema()

    def tighten(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for v in node.values():
                tighten(v)
        elif isinstance(node, list):
            for v in node:
                tighten(v)

    tighten(schema)
    return schema


class Claude:
    def __init__(self, client: anthropic.Anthropic | None = None, model: str = MODEL, effort: str = EFFORT):
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.usage = {"input_tokens": 0, "output_tokens": 0}

    def ask(self, system: str, prompt: str, out: type[T]) -> T:
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=64000,
            # The brand context is identical across every step of a run, so cache it.
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": json_schema(out)}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()

        self.usage["input_tokens"] += msg.usage.input_tokens
        self.usage["output_tokens"] += msg.usage.output_tokens
        if msg.stop_reason == "refusal":
            detail = getattr(msg.stop_details, "explanation", None) if msg.stop_details else None
            raise LLMError(f"Claude declined this step: {detail or 'no detail'}")
        if msg.stop_reason == "max_tokens":
            raise LLMError("Claude hit max_tokens before finishing this step")

        text = "".join(b.text for b in msg.content if b.type == "text")
        try:
            return out.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            raise LLMError(f"Claude returned output that does not match {out.__name__}: {e}") from e
