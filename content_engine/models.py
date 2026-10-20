"""Structured shapes Claude returns at each step."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Format = Literal["reel", "carousel", "post", "blog"]


class Brief(BaseModel):
    topic: str
    format: Format
    channel: str
    angle: str
    audience: str
    primary_keyword: str
    secondary_keywords: list[str]
    key_points: list[str] = Field(description="3-6 points the piece must make, in order")
    call_to_action: str
    claims_to_avoid: list[str] = Field(description="Claims the brand cannot make on this topic")


class Draft(BaseModel):
    title: str = Field(description="Title, or the on-screen text for short video")
    body: str = Field(description="The full piece: script, slides, caption or article in markdown")
    caption: str = Field(description="Social caption to post with it; empty for blog")
    hashtags: list[str]
    meta_description: str = Field(description="140-160 characters for blog; empty otherwise")


class Hook(BaseModel):
    pattern: str = Field(description="The hook-bank pattern used")
    hook: str = Field(description="The opening line, first 2 seconds or first sentence")
    alternatives: list[str] = Field(description="Two other hooks in the voice")


class VoiceVerdict(BaseModel):
    on_brand: bool
    score: int = Field(description="0-100, how much this sounds like the brand")
    reads_like_a_promise: bool = Field(description="True if it states prices, guarantees, results or availability")
    issues: list[str]
    fixes: list[str]
