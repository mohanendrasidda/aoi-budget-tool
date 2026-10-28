"""Collector safety rules, tested offline (no network)."""

import urllib.robotparser

import pytest

from aoi_budget.collect.fetch import Fetcher
from aoi_budget.collect.nu_regents import agenda_urls, slug


def _fetcher_with_robots(tmp_path, host, rules):
    f = Fetcher(root=tmp_path, delay_s=0)
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(rules.splitlines())
    f._robots[host] = rp
    return f


def test_robots_disallow_is_respected(tmp_path):
    f = _fetcher_with_robots(tmp_path, "example.org", "User-agent: *\nDisallow: /archive/")
    assert f.allowed("https://example.org/docs/a.pdf")
    assert not f.allowed("https://example.org/archive/a.pdf")


def test_blanket_disallow_blocks_everything(tmp_path):
    f = _fetcher_with_robots(tmp_path, "example.org", "User-agent: *\nDisallow: /")
    assert not f.allowed("https://example.org/price-list.pdf")


def test_plain_http_is_refused(tmp_path):
    assert not Fetcher(root=tmp_path, delay_s=0).allowed("http://example.org/a.pdf")


@pytest.mark.parametrize("bad", ["../outside.pdf", "a/../../outside.pdf", "/etc/passwd"])
def test_writes_cannot_escape_root(tmp_path, bad):
    with pytest.raises(ValueError):
        Fetcher(root=tmp_path / "raw").safe_path(bad)


def test_agenda_urls_keep_materials_only_and_allowed_hosts():
    html = """
    <a href="https://docs.nebraska.edu/x/Agenda 2-11-22 with Materials.pdf">a</a>
    <a href="https://docs.nebraska.edu/x/Agenda%202-11-22%20with%20Materials.pdf">dup</a>
    <a href="https://docs.nebraska.edu/x/Minutes 2-11-22.pdf">minutes</a>
    <a href="https://evil.example/Agenda with Materials.pdf">other host</a>
    """
    urls = agenda_urls(html)
    assert urls == ["https://docs.nebraska.edu/x/Agenda%202-11-22%20with%20Materials.pdf"]
    assert slug(urls[0]) == "agenda-2-11-22-with-materials"


SAMPLE_TABLE = """
Business and Finance Report – Bids and Contracts
 Type of Action  Campus  Description     Funding      Budget     Contract   Vendor
 Contract        UNL     Courier         Revolving    $1,500     $1,500     Example Co
 Furniture       UNO     Example Hall    State        $900,000   $812,345   Example
                         replacement                                        Interiors Inc.
 Consultant      UNL     Example Field   Campus       $50,000    $40,000    Example Group
 Agreement               (multiple)
                                                                            Page 4 of 9
*Approved budget amount represents the entirety of the applicable budget lines.
"""


def test_bids_rows_joins_wrapped_lines_and_two_word_types():
    from aoi_budget.collect.nu_regents import bids_rows

    rows = bids_rows(SAMPLE_TABLE)
    assert len(rows) == 3
    assert "replacement" in rows[1] and "Interiors Inc." in rows[1]
    assert rows[2].endswith("Agreement (multiple)")


def test_furniture_rows_need_furniture_and_money():
    from aoi_budget.collect.nu_regents import furniture_rows

    rows = furniture_rows(SAMPLE_TABLE)
    assert len(rows) == 1 and "$812,345" in rows[0]
