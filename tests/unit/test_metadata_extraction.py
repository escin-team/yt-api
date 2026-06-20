"""Unit tests for metadata extraction logic."""

from youtube_search.services.scraper import YouTubeScraper


def test_get_text_extracts_from_runs():
    """Verify _get_text extracts text from runs structure."""
    scraper = YouTubeScraper()
    node = {"runs": [{"text": "Sample Title"}]}
    assert scraper._get_text(node) == "Sample Title"


def test_get_text_returns_none_for_empty_runs():
    """Verify _get_text returns None when runs is empty."""
    scraper = YouTubeScraper()
    node = {"runs": []}
    assert scraper._get_text(node) is None


def test_get_text_returns_none_for_non_dict():
    """Verify _get_text returns None for non-dict input."""
    scraper = YouTubeScraper()
    assert scraper._get_text("not a dict") is None
    assert scraper._get_text(None) is None


def test_extract_channel_url_from_navigation_endpoint():
    """Verify _extract_channel_url constructs proper URL."""
    node = {
        "runs": [
            {
                "text": "Channel Name",
                "navigationEndpoint": {
                    "browseEndpoint": {"canonicalBaseUrl": "/c/example"}
                },
            }
        ]
    }
    result = YouTubeScraper._extract_channel_url(node)
    assert result == "https://www.youtube.com/c/example"


def test_extract_channel_url_returns_none_when_missing():
    """Verify _extract_channel_url returns None when endpoint missing."""
    node = {"runs": [{"text": "Channel Name"}]}
    assert YouTubeScraper._extract_channel_url(node) is None


def test_extract_view_count_parses_thousands():
    """Verify _extract_view_count parses comma-separated numbers."""
    node = {"runs": [{"text": "1,234 views"}]}
    assert YouTubeScraper._extract_view_count(node) == 1234


def test_extract_view_count_parses_millions():
    """Verify _extract_view_count parses M suffix."""
    node = {"runs": [{"text": "1.2M views"}]}
    assert YouTubeScraper._extract_view_count(node) == 1_200_000


def test_extract_view_count_returns_none_for_invalid():
    """Verify _extract_view_count returns None for unparseable text."""
    node = {"runs": [{"text": "No views here"}]}
    assert YouTubeScraper._extract_view_count(node) is None


def test_extract_publish_date_returns_text():
    """Verify _extract_publish_date extracts relative time text."""
    node = {"runs": [{"text": "2 days ago"}]}
    result = YouTubeScraper._extract_publish_date(node)
    assert result == "2 days ago"
