import pytest

from urlicon import urls


@pytest.mark.parametrize(
    ("url", "domain", "expected"),
    [
        (
            "/favicon.ico",
            "https://example.com/articles/1",
            "https://example.com/favicon.ico",
        ),
        (
            "https://cdn.example.com/icon.png",
            "https://example.com",
            "https://cdn.example.com/icon.png",
        ),
        (
            "http://example.com/icon.png",
            "https://fallback.test",
            "https://example.com/icon.png",
        ),
    ],
)
def test_ensure_domain_returns_https_absolute_url(url, domain, expected):
    assert urls.ensure_domain(url=url, domain=domain) == expected


def test_ensure_domain_requires_url_or_domain_with_netloc():
    with pytest.raises(ValueError, match="`url` or `domain` must be a domain"):
        urls.ensure_domain(url="/favicon.ico", domain="/articles/1")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/articles/1?ref=feed", "https://example.com"),
        ("http://www.example.co.uk/path", "http://www.example.co.uk"),
        ("not-a-url", ""),
        ("/relative/path", ""),
    ],
)
def test_extract_domain_from_url(url, expected):
    assert urls.extract_domain_from_url(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com", "example"),
        ("https://www.example.com", "example"),
        ("https://docs.python.org", "python_docs"),
        ("https://www.example.com.br", "example"),
        ("https://blog.product.example.com", "example_product"),
    ],
)
def test_get_name_from_domain(url, expected):
    assert urls.get_name_from_domain(url) == expected


def test_get_name_from_domain_requires_domain():
    with pytest.raises(ValueError, match="`url` must have a domain"):
        urls.get_name_from_domain("example.com")


@pytest.mark.parametrize(
    ("path", "url", "expected"),
    [
        (
            "/assets/icon.png",
            "https://example.com/articles/1?ref=feed",
            "https://example.com/assets/icon.png",
        ),
        (
            "https://cdn.example.com/icon.png",
            "https://example.com/articles/1",
            "https://cdn.example.com/icon.png",
        ),
        (
            "images/icon.png",
            "https://example.com/articles/1",
            "https://example.com/articles/1/images/icon.png",
        ),
        (
            "images/icon.png",
            "https://example.com/articles/page.html?ref=feed#comments",
            "https://example.com/articles/images/icon.png",
        ),
    ],
)
def test_ensure_relative_path(path, url, expected):
    assert urls.ensure_relative_path(path=path, url=url) == expected


def test_read_from_url_or_path_reads_matching_html_file(tmp_path):
    html_file = tmp_path / "sample.html"
    html_file.write_text("<html>ok</html>")

    assert urls.read_from_url_or_path(str(tmp_path / "sample.md")) == "<html>ok</html>"


def test_read_from_url_or_path_reads_https_response(monkeypatch):
    class Response:
        text = "<html>remote</html>"

    def fake_get(url):
        assert url == "https://example.com"
        return Response()

    monkeypatch.setattr(urls.requests, "get", fake_get)

    assert urls.read_from_url_or_path("https://example.com") == "<html>remote</html>"


def test_read_from_url_or_path_returns_empty_string_when_https_request_fails(
    monkeypatch,
):
    def fake_get(url):
        raise urls.requests.RequestException

    monkeypatch.setattr(urls.requests, "get", fake_get)

    assert urls.read_from_url_or_path("https://example.com") == ""
