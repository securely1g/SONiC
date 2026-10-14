#!/usr/bin/env python3
"""Order securely1g Project 1 prerequisites before consumers; dry-run by default."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from html.parser import HTMLParser
import heapq
import json
import re
import subprocess
import sys
from typing import Any


PROJECT_ID = "PVT_kwHOD5OsO84Bk3xL"
CANONICAL_FIELD_ID = "PVTF_lAHOD5OsO84Bk3xLzhjpYx4"
FIELD_NAME = "All upstream PRs"
PR_URL = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pull/([1-9][0-9]*)/?\Z")
COMPACT_PR = re.compile(r"(?:(?P<owner>[A-Za-z0-9_.-]+)/)?(?P<repo>[A-Za-z0-9_.-]+)#(?P<number>[1-9][0-9]*)\Z")
ITEM_QUERY = """query($cursor:String) {
  viewer {login}
  user(login:"securely1g") {projectV2(number:1) {
    id
    field(name:"All upstream PRs") {
      __typename ... on ProjectV2Field {id name dataType}
    }
    items(first:100,after:$cursor,orderBy:{field:POSITION,direction:ASC}) {
      totalCount pageInfo {hasNextPage endCursor}
      nodes {
        id isArchived
        content {__typename ... on PullRequest {url state}}
        fieldValueByName(name:"All upstream PRs") {
          __typename ... on ProjectV2ItemFieldTextValue {
            text field {... on ProjectV2Field {id name dataType}}
          }
        }
      }
    }
  }}
}"""
VIEW_QUERY = """query($cursor:String) {
  user(login:"securely1g") {projectV2(number:1) {
    id views(first:100,after:$cursor) {
      totalCount pageInfo {hasNextPage endCursor}
      nodes {
        id number name filter layout
        sortByFields(first:100) {
          nodes {direction field {... on ProjectV2FieldCommon {id name}}}
          pageInfo {hasNextPage endCursor}
        }
        groupByFields(first:100) {
          nodes {... on ProjectV2FieldCommon {id name}}
          pageInfo {hasNextPage endCursor}
        }
        verticalGroupByFields(first:100) {
          nodes {... on ProjectV2FieldCommon {id name}}
          pageInfo {hasNextPage endCursor}
        }
      }
    }
  }}
}"""
MOVE_MUTATION = """mutation($item:ID!, $after:ID) {
  updateProjectV2ItemPosition(input:{
    projectId:"PVT_kwHOD5OsO84Bk3xL", itemId:$item, afterId:$after
  }) {clientMutationId}
}"""


class OrderError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OrderError(message)


def normalized_pr_url(value: str) -> str:
    match = PR_URL.fullmatch(value)
    require(match is not None, f"Invalid prerequisite PR URL: {value!r}")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner.lower()}/{repo.lower()}/pull/{number}"


class PrLinks(HTMLParser):
    """Read the canonical HTML anchors, rejecting text that could hide an edge."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.inside = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        require(tag == "a" and not self.inside, "Canonical dependencies must be HTML PR anchors")
        hrefs = [value for name, value in attrs if name == "href"]
        require(len(hrefs) == 1 and isinstance(hrefs[0], str), "Prerequisite anchor needs one href")
        self.links.append(normalized_pr_url(hrefs[0]))
        self.inside = True

    def handle_endtag(self, tag: str) -> None:
        require(tag == "a" and self.inside, "Malformed prerequisite anchor")
        self.inside = False

    def handle_data(self, value: str) -> None:
        if not self.inside:
            require(not value.strip(" \t\r\n·"), "Unlinked text in canonical dependencies")

    def handle_comment(self, value: str) -> None:
        raise OrderError("Comments are not canonical dependency links")

    def handle_decl(self, value: str) -> None:
        raise OrderError("Declarations are not canonical dependency links")


def parse_anchors(text: str) -> tuple[str, ...]:
    parser = PrLinks()
    parser.feed(text)
    parser.close()
    require(not parser.inside, "Unclosed prerequisite anchor")
    return tuple(dict.fromkeys(parser.links))


def repository_aliases(repositories: set[str]) -> dict[str, str]:
    """Resolve display names from verified repositories, never a guessed prefix."""
    aliases: dict[str, str] = {}
    for repository in sorted(repositories):
        owner, repo = repository.lower().split("/", 1)
        if owner != "securely1g":
            continue
        for alias in {repo, repo.removeprefix("sonic-")}:
            require(alias not in aliases or aliases[alias] == repository.lower(),
                    f"Ambiguous prerequisite repository alias: {alias!r}")
            aliases[alias] = repository.lower()
    return aliases


def parse_links(text: str, aliases: dict[str, str] | None = None) -> tuple[str, ...]:
    """Read full HTML links or the lossless compact fallback for long cells."""
    if not text.strip():
        return ()
    if "<" in text:
        return parse_anchors(text)
    links = []
    for reference in text.split("·"):
        match = COMPACT_PR.fullmatch(reference.strip())
        require(match is not None, f"Invalid compact prerequisite: {reference!r}")
        owner, repo, number = match.group("owner", "repo", "number")
        repo = repo.lower()
        if owner:
            # Qualified references retain the actual repository name.
            repository = f"{owner.lower()}/{repo}"
        elif repo.startswith("sonic-"):
            repository = f"securely1g/{repo}"
        else:
            repository = (aliases or {}).get(repo)
            require(repository is not None,
                    f"Unknown prerequisite repository alias: {repo!r}; use owner/full-repository#number")
        links.append(normalized_pr_url(f"https://github.com/{repository}/pull/{number}"))
    return tuple(dict.fromkeys(links))


@dataclass(frozen=True)
class Item:
    id: str
    url: str | None
    upstream: str = ""
    state: str | None = None
    archived: bool = False


@dataclass(frozen=True)
class Snapshot:
    items: tuple[Item, ...]
    views: tuple[dict[str, Any], ...] = ()


class GitHub:
    def __init__(self, executable: str) -> None:
        self.executable = executable

    def query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [self.executable, "api", "graphql", "--input", "-"],
                input=json.dumps({"query": query, "variables": variables}),
                text=True, capture_output=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OrderError(f"GitHub request failed: {exc}") from exc
        require(result.returncode == 0, f"GitHub request failed: {result.stderr.strip()}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OrderError("GitHub returned invalid JSON") from exc
        require(isinstance(payload, dict), "GitHub returned a non-object response")
        require(not payload.get("errors"), f"GraphQL errors: {payload.get('errors')}")
        require(isinstance(payload.get("data"), dict), "Missing GraphQL data")
        return payload["data"]

    def move(self, item: str, after: str | None) -> None:
        result = self.query(MOVE_MUTATION, {"item": item, "after": after})
        require(isinstance(result.get("updateProjectV2ItemPosition"), dict), "Move returned no result")


def read_connection(client: GitHub, query: str, name: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    ids: set[str] = set()
    cursors: set[str] = set()
    cursor = None
    expected_total = None
    while True:
        data = client.query(query, {"cursor": cursor})
        owner = data.get("user")
        require(isinstance(owner, dict), "Missing Project owner")
        project = owner.get("projectV2")
        require(isinstance(project, dict) and project.get("id") == PROJECT_ID, "Unexpected Project identity")
        if name == "items":
            viewer = data.get("viewer")
            require(isinstance(viewer, dict) and viewer.get("login") == "securely1g", "Use the securely1g GitHub account")
            expected = {"__typename": "ProjectV2Field", "id": CANONICAL_FIELD_ID,
                        "name": FIELD_NAME, "dataType": "TEXT"}
            require(project.get("field") == expected, "Canonical upstream field identity/type changed")
        connection = project.get(name)
        require(isinstance(connection, dict), f"Missing {name} connection")
        total, batch, info = (connection.get(key) for key in ("totalCount", "nodes", "pageInfo"))
        require(type(total) is int and total >= 0 and isinstance(batch, list) and len(batch) <= 100,
                f"Invalid {name} page")
        require(isinstance(info, dict) and type(info.get("hasNextPage")) is bool, f"Invalid {name} pagination")
        require(expected_total is None or expected_total == total, f"{name} changed during pagination")
        expected_total = total
        for node in batch:
            require(isinstance(node, dict) and isinstance(node.get("id"), str), f"Unidentified {name} node")
            require(node["id"] not in ids, f"Duplicate {name} node during pagination")
            ids.add(node["id"])
            nodes.append(node)
        require(len(nodes) <= total, f"Too many {name} nodes")
        if not info["hasNextPage"]:
            require(len(nodes) == total, f"Incomplete {name} pagination")
            return nodes
        cursor = info.get("endCursor")
        require(bool(batch) and isinstance(cursor, str) and cursor and cursor not in cursors,
                f"{name} cursor did not advance")
        cursors.add(cursor)


def read_snapshot(client: GitHub) -> Snapshot:
    items = []
    for node in read_connection(client, ITEM_QUERY, "items"):
        content = node.get("content") or {}
        require(isinstance(content, dict), "Unexpected Project item content")
        url = normalized_pr_url(content["url"]) if content.get("__typename") == "PullRequest" else None
        value = node.get("fieldValueByName")
        if value is not None:
            require(isinstance(value, dict) and value.get("__typename") == "ProjectV2ItemFieldTextValue"
                    and value.get("field") == {"id": CANONICAL_FIELD_ID, "name": FIELD_NAME, "dataType": "TEXT"}
                    and isinstance(value.get("text"), str), "Unexpected canonical item field")
        items.append(Item(node["id"], url, value["text"] if value else "",
                          content.get("state"), node.get("isArchived", False)))
    views = read_connection(client, VIEW_QUERY, "views")
    for view in views:
        for name in ("sortByFields", "groupByFields", "verticalGroupByFields"):
            connection = view.get(name)
            require(isinstance(connection, dict) and isinstance(connection.get("nodes"), list)
                    and isinstance(connection.get("pageInfo"), dict)
                    and connection.get("pageInfo", {}).get("hasNextPage") is False,
                    f"Incomplete {name} for view {view.get('name')}")
    return Snapshot(tuple(items), tuple(views))


def desired_order(snapshot: Snapshot) -> tuple[list[str], list[dict[str, str]]]:
    """Stable Kahn sort over every PR row; keep non-PR rows in their original slots."""
    prs = {item.url: item for item in snapshot.items if item.url}
    require(len(prs) == sum(item.url is not None for item in snapshot.items), "Duplicate Project PR rows")
    position = {item.id: index for index, item in enumerate(snapshot.items)}
    indegree = {item.id: 0 for item in prs.values()}
    dependents: dict[str, set[str]] = {item.id: set() for item in prs.values()}
    missing = []
    repositories = {"/".join(PR_URL.fullmatch(url).groups()[:2]) for url in prs}
    for item in prs.values():
        if "<" in item.upstream:
            repositories.update("/".join(PR_URL.fullmatch(url).groups()[:2])
                                for url in parse_anchors(item.upstream))
    aliases = repository_aliases(repositories)
    for item in prs.values():
        for url in parse_links(item.upstream, aliases):
            upstream = prs.get(url)
            if upstream is None:
                missing.append({"consumer": item.url, "prerequisite": url})
            elif item.id not in dependents[upstream.id]:
                dependents[upstream.id].add(item.id)
                indegree[item.id] += 1
    ready = [(position[item], item) for item, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        _, item = heapq.heappop(ready)
        ordered.append(item)
        for dependent in dependents[item]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, (position[dependent], dependent))
    blocked = [item.url for item in snapshot.items if item.url and indegree[item.id]]
    require(not blocked, "Dependency cycle prevents ordering: " + ", ".join(blocked))
    iterator = iter(ordered)
    return [next(iterator) if item.url else item.id for item in snapshot.items], missing


def move_after(order: list[str], item: str, after: str | None) -> list[str]:
    result = [value for value in order if value != item]
    result.insert(result.index(after) + 1 if after is not None else 0, item)
    return result


def plan_moves(snapshot: Snapshot, target: list[str]) -> list[dict[str, str | None]]:
    current = [item.id for item in snapshot.items]
    movable = {item.id for item in snapshot.items if item.url}
    moves = []
    for index, item in enumerate(target):
        if item not in movable:
            continue
        after = target[index - 1] if index else None
        updated = move_after(current, item, after)
        if updated != current:
            moves.append({"item": item, "after": after})
            current = updated
    require(current == target, "Could not preserve non-PR positions while ordering PRs")
    return moves


def view_warnings(snapshot: Snapshot) -> list[str]:
    warnings = []
    for view in snapshot.views:
        if view["sortByFields"]["nodes"]:
            warnings.append(f"{view['name']}: saved sorting overrides manual item order; apply is blocked")
        if view["groupByFields"]["nodes"] or view["verticalGroupByFields"]["nodes"]:
            warnings.append(f"{view['name']}: grouping remains; prerequisite order applies within groups, not across groups")
    return warnings


def reconcile(client: GitHub, apply: bool = False) -> dict[str, Any]:
    snapshot = read_snapshot(client)
    target, missing = desired_order(snapshot)
    moves = plan_moves(snapshot, target)
    report = {"project": "https://github.com/users/securely1g/projects/1",
              "canonical_field_id": CANONICAL_FIELD_ID, "apply": apply,
              "moves": moves, "missing_prerequisites": missing,
              "view_warnings": view_warnings(snapshot), "desired_order": target,
              "verified": False}
    if not apply:
        return report
    require(not any(view["sortByFields"]["nodes"] for view in snapshot.views),
            "Saved view sorting overrides manual order; no changes made")
    expected = snapshot
    completed = 0
    try:
        for move in moves:
            require(read_snapshot(client) == expected, "Project graph, views, or order changed concurrently")
            client.move(move["item"], move["after"])
            completed += 1
            by_id = {item.id: item for item in expected.items}
            order = move_after([item.id for item in expected.items], move["item"], move["after"])
            expected = replace(expected, items=tuple(by_id[item] for item in order))
        require(read_snapshot(client) == expected, "Project final readback differs from the expected graph, views, or order")
    except OrderError as exc:
        raise OrderError(f"{exc}; {completed} move(s) completed. Rerun from the current Project state.") from exc
    report["verified"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-cli", required=True, help="GitHub CLI/account selector authenticated as securely1g")
    parser.add_argument("--apply", action="store_true", help="move PR rows after validating the complete graph and current order")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(reconcile(GitHub(args.github_cli), args.apply), indent=2))
        return 0
    except (OrderError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
