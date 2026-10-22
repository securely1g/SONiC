#!/usr/bin/env python3
"""Format the derived Upstream PRs display; never parse canonical dependencies."""

from __future__ import annotations

import html
import json
import re
import sys


PR_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)/?\Z")


def format_grouped_upstream(urls: list[str]) -> str:
    """Keep every destination clickable, grouping repositories in first-seen order."""
    groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
    labels: dict[tuple[str, str], tuple[str, str]] = {}
    seen: set[tuple[str, str, str]] = set()
    for url in urls:
        match = PR_URL.fullmatch(url)
        if match is None:
            raise ValueError(f"Invalid GitHub pull-request URL: {url!r}")
        owner, repository, number = match.groups()
        identity = (owner.lower(), repository.lower(), number)
        if identity in seen:
            continue
        seen.add(identity)
        labels.setdefault(identity[:2], (owner, repository))
        groups.setdefault(identity[:2], []).append((number, url.rstrip("/")))

    sections = []
    for identity, references in groups.items():
        owner, repository = labels[identity]
        label = repository.removeprefix("sonic-")
        if owner.lower() != "securely1g":
            label = f"{owner}/{label}"
        links = [f'<a href="{html.escape(url, quote=True)}">#{number}</a>'
                 for number, url in references]
        sections.append(f'{html.escape(label)}: {" · ".join(links)}')
    result = " | ".join(sections)
    if len(result) > 1024:
        raise ValueError("Grouped clickable upstream list exceeds GitHub's 1,024-character limit; retain the saved cell")
    return result


if __name__ == "__main__":
    values = json.load(sys.stdin)
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise SystemExit("Expected a JSON list of verified full GitHub PR URLs on stdin")
    print(format_grouped_upstream(values))
