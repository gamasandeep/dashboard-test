"""content-engine run --topic "is retinol worth it" --format reel --angle "purging vs breakout"."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .llm import LLMError
from .pipeline import ContentEngine, Request, result_json


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "brand-os").is_dir() and (p / "owner").is_dir():
            return p
    raise SystemExit("Run this inside the project (no brand-os/ and owner/ found above the current directory).")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="content-engine", description="03 · Content Engine: Brief → Draft → SEO pass → Hook.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Draft one piece from a brief")
    run.add_argument("--topic", required=True)
    run.add_argument("--format", default="reel", choices=["reel", "carousel", "post", "blog"])
    run.add_argument("--channel", default="instagram")
    run.add_argument("--angle", default="")
    run.add_argument("--keyword", action="append", default=[], help="Target keyword; repeat for more")
    run.add_argument("--root", type=Path, help="Project root (default: found from the current directory)")
    run.add_argument("--dry-run", action="store_true", help="Print the system prompt and first step; no API call")
    args = ap.parse_args(argv)

    root = args.root or find_root(Path.cwd())
    engine = ContentEngine(root)
    req = Request(topic=args.topic, format=args.format, channel=args.channel, angle=args.angle, keywords=args.keyword)

    if args.dry_run:
        print(json.dumps(engine.dry_run(req), indent=2))
        return 0
    try:
        result = engine.run(req)
    except LLMError as e:
        print(f"content-engine: {e}", file=sys.stderr)
        return 1
    print(result_json(result))
    return 0 if result.status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
