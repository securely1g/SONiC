#!/usr/bin/env python3
"""Keep compact dashboard cells lossless and prerequisite ordering unambiguous."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from order_dashboard import Item, OrderError, Snapshot, desired_order, parse_links, repository_aliases


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


if __name__ == "__main__":
    unittest.main()
