#!/usr/bin/env python3
"""Keep compact dashboard cells lossless and prerequisite ordering unambiguous."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from order_dashboard import (
    CANONICAL_FIELD_ID, DETAIL_QUERY, FIELD_NAME, IDENTITY_QUERY, PROJECT_ID, VIEW_QUERY,
    Item, OrderError, Snapshot, desired_order, main, move_after, parse_links, read_snapshot,
    reconcile, repository_aliases,
)


def pr(repo, number, owner="securely1g"):
    return f"https://github.com/{owner}/{repo}/pull/{number}"


class CompactPrerequisiteTests(unittest.TestCase):
    def setUp(self):
        self.aliases = repository_aliases({
            "securely1g/sonic-buildimage", "securely1g/sonic-bazel-registry",
            "securely1g/agi-projects", "securely1g/SONiC",
        })

    def test_all_eighteen_dependencies_survive_compact_round_trip_and_ordering(self):
        """The long base-image dependency list keeps historical and open edges alike."""
        pairs = [("sonic-buildimage", n) for n in (19, 21, 22, 23, 24, 25, 27)]
        pairs += [("sonic-bazel-registry", n) for n in (53, 55, 56, 57, 61, 62, 63, 64, 65, 67, 70)]
        urls = tuple(pr(repo, number) for repo, number in pairs)
        text = " · ".join(f"{repo.removeprefix('sonic-')}#{number}" for repo, number in pairs)
        self.assertLessEqual(len(text), 1024)
        self.assertEqual(parse_links(text, self.aliases), urls)
        states = ("OPEN", "MERGED", "CLOSED")
        upstream = tuple(Item(str(i), url, state=states[i % 3]) for i, url in enumerate(urls))
        consumer = Item("consumer", pr("sonic-buildimage", 30), text, "OPEN")
        order, missing = desired_order(Snapshot((consumer,) + upstream))
        self.assertEqual(order, [item.id for item in upstream] + [consumer.id])
        self.assertEqual(missing, [])

    def test_short_html_labels_do_not_change_repository_identity(self):
        """Linked labels are presentation; href remains authoritative."""
        url = pr("sonic-swss-common", 6)
        self.assertEqual(parse_links(f'<a href="{url}">swss-common#6</a>'), (url,))

    def test_non_sonic_repositories_and_qualified_references_are_not_prefixed(self):
        """Existing repository names remain intact when aliases shorten SONiC names."""
        text = "agi-projects#44 · SONiC#3 · other/buildimage#7 · sonic-build-infra#44"
        self.assertEqual(parse_links(text, self.aliases), (
            pr("agi-projects", 44), pr("sonic", 3), pr("buildimage", 7, "other"),
            pr("sonic-build-infra", 44),
        ))

    def test_unknown_or_ambiguous_aliases_fail_without_guessing(self):
        """A colliding real repository name must never redirect an edge silently."""
        with self.assertRaisesRegex(OrderError, "Ambiguous"):
            repository_aliases({"securely1g/buildimage", "securely1g/sonic-buildimage"})
        with self.assertRaisesRegex(OrderError, "Unknown"):
            parse_links("unlisted#2", self.aliases)

    def test_full_external_reference_without_project_row_is_reported(self):
        """Outside-graph dependencies remain in the report instead of disappearing."""
        consumer = Item("consumer", pr("sonic-buildimage", 30), "other/sonic-tool#9")
        order, missing = desired_order(Snapshot((consumer,)))
        self.assertEqual(order, ["consumer"])
        self.assertEqual(missing, [{"consumer": consumer.url, "prerequisite": pr("sonic-tool", 9, "other")}])

    def test_html_catalog_resolves_prerequisites_without_project_rows(self):
        """Known hrefs supply exact repository identities for compact references."""
        linked = Item("linked", pr("sonic-buildimage", 1),
                      f'<a href="{pr("sonic-other", 2)}">other#2</a>')
        compact = Item("compact", pr("sonic-buildimage", 3), "other#4")
        _, missing = desired_order(Snapshot((linked, compact)))
        self.assertEqual([entry["prerequisite"] for entry in missing],
                         [pr("sonic-other", 2), pr("sonic-other", 4)])

    def test_duplicate_references_deduplicate_and_malformed_lists_fail(self):
        """Compact syntax must not discard unrecognized text or create duplicate edges."""
        self.assertEqual(parse_links("buildimage#19 · sonic-buildimage#19", self.aliases),
                         (pr("sonic-buildimage", 19),))
        for text in ("buildimage#19 · +2 more", "buildimage#19 ·", "[buildimage#19](url)"):
            with self.subTest(text=text), self.assertRaises(OrderError):
                parse_links(text, self.aliases)


class MixedOwnerClient:
    """Reject any attempt to load or move the excluded fixture row."""

    def __init__(self, change_owner=False):
        self.order = ["consumer", "excluded", "prerequisite", "note"]
        self.owners = {"consumer": "securely1g", "excluded": "other", "prerequisite": "securely1g"}
        self.detail_batches = []
        self.moves = []
        self.change_owner = change_owner

    @staticmethod
    def field():
        return {"__typename": "ProjectV2Field", "id": CANONICAL_FIELD_ID,
                "name": FIELD_NAME, "dataType": "TEXT"}

    def query(self, query, variables):
        if query == IDENTITY_QUERY:
            nodes = [{"id": item, "isArchived": False,
                      "content": {"__typename": "PullRequest", "baseRepository": {"owner": {"login": self.owners[item]}}}
                      if item in self.owners else {"__typename": "DraftIssue"}}
                     for item in self.order]
            return {"viewer": {"login": "securely1g"}, "user": {"projectV2": {
                "id": PROJECT_ID, "field": self.field(), "items": {"totalCount": len(nodes),
                "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}}}}
        if query == DETAIL_QUERY:
            requested = variables["ids"]
            assert set(requested) <= {"consumer", "prerequisite"}, requested
            self.detail_batches.append(tuple(requested))
            nodes = []
            for item in requested:
                number = 2 if item == "consumer" else 1
                text = "buildimage#1 · other/tool#9" if item == "consumer" else ""
                field = self.field().copy(); field.pop("__typename")
                nodes.append({"id": item, "isArchived": False, "project": {"id": PROJECT_ID},
                              "content": {"__typename": "PullRequest", "url": pr("sonic-buildimage", number),
                                          "state": "OPEN", "baseRepository": {"owner": {"login": self.owners[item]}}},
                              "fieldValueByName": {"__typename": "ProjectV2ItemFieldTextValue", "text": text,
                                                   "field": field} if text else None})
            if self.change_owner:
                self.owners["consumer"] = "other"
            return {"viewer": {"login": "securely1g"}, "nodes": nodes}
        if query == VIEW_QUERY:
            return {"user": {"projectV2": {"id": PROJECT_ID, "views": {"totalCount": 0,
                    "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []}}}}
        raise AssertionError("Unexpected query")

    def move(self, item, after):
        assert item in {"consumer", "prerequisite"}, item
        self.moves.append((item, after))
        self.order = move_after(self.order, item, after)


class OwnerScopeTests(unittest.TestCase):
    def test_cli_defaults_to_owner_scope_without_flag(self):
        client = MixedOwnerClient()
        output = io.StringIO()
        with patch("order_dashboard.GitHub", return_value=client), redirect_stdout(output):
            result = main(["--github-cli", "/reviewed/gh-securely1g", "--apply"])
        self.assertEqual(result, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["base_owner"], "securely1g")
        self.assertTrue(report["verified"])
        self.assertEqual(client.order, ["prerequisite", "excluded", "consumer", "note"])
        self.assertTrue(all(set(batch) == {"consumer", "prerequisite"} for batch in client.detail_batches))

    def test_scoped_ordering_keeps_excluded_details_opaque_and_final_positions_fixed(self):
        client = MixedOwnerClient()
        result = reconcile(client, apply=True, base_owner="securely1g")
        self.assertTrue(result["verified"])
        self.assertEqual(client.order, ["prerequisite", "excluded", "consumer", "note"])
        self.assertEqual(result["missing_prerequisites"], [])
        self.assertEqual(result["excluded_items"], [{"item": "excluded", "base_owner": "other"}])
        self.assertEqual(result["excluded_prerequisites"], [{"consumer": pr("sonic-buildimage", 2),
                                                             "prerequisite": pr("tool", 9, "other")}])
        self.assertEqual(len(result["scope_limitations"]), 1)
        self.assertTrue(client.detail_batches)
        self.assertTrue(all(set(batch) == {"consumer", "prerequisite"} for batch in client.detail_batches))
        self.assertTrue(all(item != "excluded" for item, _ in client.moves))

    def test_unavailable_owner_stops_before_loading_any_pr_details(self):
        client = MixedOwnerClient()
        client.owners["excluded"] = None
        with self.assertRaisesRegex(OrderError, "Missing PR base owner identity"):
            read_snapshot(client, base_owner="securely1g")
        self.assertEqual(client.detail_batches, [])
        self.assertEqual(client.moves, [])

    def test_owner_change_during_detail_loading_stops_before_moves(self):
        client = MixedOwnerClient(change_owner=True)
        with self.assertRaisesRegex(OrderError, "ownership or membership changed"):
            read_snapshot(client, base_owner="securely1g")
        self.assertEqual(client.moves, [])


if __name__ == "__main__":
    unittest.main()
