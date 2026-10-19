#!/usr/bin/env python3
"""Verify that shorter Project displays preserve every clickable destination."""

from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from format_grouped_upstream import format_grouped_upstream


def pr(repo, number, owner="securely1g"):
    return f"https://github.com/{owner}/{repo}/pull/{number}"


class Display(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attributes):
        if tag == "a":
            self.links.append(dict(attributes)["href"])

    def handle_data(self, text):
        self.text.append(text)


class GroupedUpstreamTests(unittest.TestCase):
    def test_grouping_keeps_repository_order_and_each_pr_link(self):
        urls = [pr("sonic-buildimage", 19), pr("sonic-bazel-registry", 62),
                pr("sonic-buildimage", 21)]
        display = Display(format_grouped_upstream(urls))
        self.assertEqual(display.links, [urls[0], urls[2], urls[1]])
        self.assertEqual("".join(display.text),
                         "buildimage: #19 · #21 | bazel-registry: #62")

    def test_long_list_fits_without_losing_clickability(self):
        urls = [pr("sonic-buildimage", 13)]
        urls += [pr("sonic-bazel-registry", n) for n in (72, 77, 74, 75, 79, 76, 73, 70)]
        urls += [pr("sonic-fips", n) for n in (1, 2, 3)]
        result = format_grouped_upstream(urls)
        self.assertLessEqual(len(result), 1024)
        self.assertEqual(Display(result).links, urls)

    def test_other_owners_and_repository_names_remain_distinct(self):
        urls = [pr("SONiC", 3), pr("sonic-buildimage", 19, "other-owner"),
                pr("agi-projects", 44)]
        display = Display(format_grouped_upstream(urls))
        self.assertEqual(display.links, urls)
        self.assertEqual("".join(display.text),
                         "SONiC: #3 | other-owner/buildimage: #19 | agi-projects: #44")

    def test_duplicates_are_removed_by_identity_and_empty_subset_is_empty(self):
        url = pr("sonic-buildimage", 19)
        display = Display(format_grouped_upstream([url, url + "/", url.replace("securely1g", "Securely1g")]))
        self.assertEqual(display.links, [url])
        self.assertEqual(format_grouped_upstream([]), "")

    def test_invalid_destinations_and_overlength_lists_fail_without_partial_output(self):
        for url in ("javascript:alert(1)", "https://github.com.evil/owner/repo/pull/1",
                    "https://github.com/owner/repo/issues/1", pr("sonic-buildimage", 0)):
            with self.subTest(url=url), self.assertRaises(ValueError):
                format_grouped_upstream([url])
        with self.assertRaisesRegex(ValueError, "1,024-character limit"):
            format_grouped_upstream([pr("sonic-buildimage", number) for number in range(1, 30)])


if __name__ == "__main__":
    unittest.main()
