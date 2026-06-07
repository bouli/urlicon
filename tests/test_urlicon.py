import pytest
from bs4 import BeautifulSoup

from urlicon import urlicon


def test_get_url_icon_returns_default_image_for_domainless_input(monkeypatch):
    monkeypatch.setattr(
        urlicon,
        "get_default_img",
        lambda text: f"https://avatar.test/?name={text}",
    )

    assert urlicon.get_url_icon("example") == "https://avatar.test/?name=example"


def test_get_url_icon_prefers_meta_icon(monkeypatch):
    monkeypatch.setattr(
        urlicon,
        "get_meta_icon_from_url",
        lambda url: ("https://cdn.example.com/meta.png", "parsed-soup"),
    )
    monkeypatch.setattr(
        urlicon,
        "get_favicon_from_url",
        lambda url: pytest.fail("favicon should not be checked"),
    )

    assert (
        urlicon.get_url_icon("https://example.com/page")
        == "https://cdn.example.com/meta.png"
    )


def test_get_url_icon_uses_favicon_when_meta_icon_is_missing(monkeypatch):
    monkeypatch.setattr(urlicon, "get_meta_icon_from_url", lambda url: (None, None))
    monkeypatch.setattr(
        urlicon,
        "get_favicon_from_url",
        lambda url: "https://example.com/favicon.ico",
    )
    monkeypatch.setattr(
        urlicon,
        "get_first_img_from_url",
        lambda *args, **kwargs: pytest.fail("first image should not be checked"),
    )

    assert (
        urlicon.get_url_icon("https://example.com/page")
        == "https://example.com/favicon.ico"
    )


def test_get_url_icon_uses_first_image_from_requested_url(monkeypatch):
    def fake_first_img(url, url_soup=None):
        if url == "https://example.com/page":
            return "/images/cover.png"
        pytest.fail("domain homepage should not be checked")

    monkeypatch.setattr(urlicon, "get_meta_icon_from_url", lambda url: (None, None))
    monkeypatch.setattr(urlicon, "get_favicon_from_url", lambda url: None)
    monkeypatch.setattr(urlicon, "get_first_img_from_url", fake_first_img)

    assert (
        urlicon.get_url_icon("https://example.com/page")
        == "https://example.com/images/cover.png"
    )


def test_get_url_icon_uses_first_image_from_domain_homepage(monkeypatch):
    def fake_first_img(url, url_soup=None):
        if url == "https://example.com/page":
            return None
        if url == "https://example.com":
            return "/images/home.png"
        pytest.fail(f"unexpected url: {url}")

    monkeypatch.setattr(urlicon, "get_meta_icon_from_url", lambda url: (None, None))
    monkeypatch.setattr(urlicon, "get_favicon_from_url", lambda url: None)
    monkeypatch.setattr(urlicon, "get_first_img_from_url", fake_first_img)

    assert (
        urlicon.get_url_icon("https://example.com/page")
        == "https://example.com/images/home.png"
    )


def test_get_url_icon_returns_default_image_when_no_candidate_exists(monkeypatch):
    monkeypatch.setattr(urlicon, "get_meta_icon_from_url", lambda url: (None, None))
    monkeypatch.setattr(urlicon, "get_favicon_from_url", lambda url: None)
    monkeypatch.setattr(urlicon, "get_first_img_from_url", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        urlicon,
        "get_default_img",
        lambda text: f"https://avatar.test/?name={text}",
    )

    assert (
        urlicon.get_url_icon("https://example.com/page")
        == "https://avatar.test/?name=https://example.com/page"
    )


def test_get_url_content_file_icon_fetches_discovered_icon(monkeypatch):
    monkeypatch.setattr(
        urlicon,
        "get_url_icon",
        lambda url: "https://example.com/favicon.ico",
    )

    def fake_requests_get(url):
        assert url == "https://example.com/favicon.ico"
        return b"icon-bytes"

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    assert urlicon.get_url_content_file_icon("https://example.com") == b"icon-bytes"


def test_get_meta_icon_from_url_selects_largest_available_icon(monkeypatch):
    soup = BeautifulSoup(
        """
        <html>
          <link rel="icon" href="https://cdn.example.com/icon-16.png" sizes="16x16">
          <link rel="icon" href="https://cdn.example.com/icon-32.png" sizes="32x32">
          <link rel="apple-touch-icon" href="https://cdn.example.com/apple.png">
        </html>
        """,
        features="html.parser",
    )
    requested_urls = []

    def fake_requests_get(url):
        requested_urls.append(url)
        return b"image"

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    icon, returned_soup = urlicon.get_meta_icon_from_url(
        "https://example.com/page",
        soup,
    )

    assert icon == "https://cdn.example.com/icon-32.png"
    assert returned_soup is soup
    assert requested_urls == ["https://cdn.example.com/icon-32.png"]


def test_get_meta_icon_from_url_returns_none_when_no_icon_links_exist():
    soup = BeautifulSoup("<html><head></head></html>", features="html.parser")

    icon, returned_soup = urlicon.get_meta_icon_from_url("https://example.com", soup)

    assert icon is None
    assert returned_soup is soup


def test_get_meta_icon_from_url_returns_none_when_icon_request_raises(monkeypatch):
    soup = BeautifulSoup(
        '<html><link rel="icon" href="https://cdn.example.com/icon.png"></html>',
        features="html.parser",
    )

    def fake_requests_get(url):
        raise urlicon.requests.RequestException

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    icon, returned_soup = urlicon.get_meta_icon_from_url("https://example.com", soup)

    assert icon is None
    assert returned_soup is soup


def test_get_soup_icons_from_url_uses_provided_soup_without_fetching(monkeypatch):
    soup = BeautifulSoup(
        '<html><link rel="icon" href="/favicon.png"><link rel="stylesheet"></html>',
        features="html.parser",
    )
    monkeypatch.setattr(
        urlicon,
        "requests_get",
        lambda url: pytest.fail("provided soup should avoid fetching"),
    )

    soup_icons, returned_soup = urlicon.get_soup_icons_from_url(
        "https://example.com",
        soup,
    )

    assert [icon["href"] for icon in soup_icons] == ["/favicon.png"]
    assert returned_soup is soup


def test_get_soup_icons_from_url_fetches_and_parses_html(monkeypatch):
    monkeypatch.setattr(
        urlicon,
        "requests_get",
        lambda url: b'<html><link rel="apple-touch-icon" href="/apple.png"></html>',
    )

    soup_icons, url_soup = urlicon.get_soup_icons_from_url("https://example.com")

    assert [icon["href"] for icon in soup_icons] == ["/apple.png"]
    assert url_soup.find("link")["rel"] == ["apple-touch-icon"]


def test_get_soup_icons_from_url_returns_none_when_fetch_fails(monkeypatch):
    def fake_requests_get(url):
        raise urlicon.requests.RequestException

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    assert urlicon.get_soup_icons_from_url("https://example.com") == (None, None)


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ('<link rel="icon" sizes="64x64">', 64),
        ('<link rel="icon">', 1),
        ('<link rel="icon" sizes="bad">', 1),
    ],
)
def test_get_soup_icon_size(html, expected):
    soup_icon = BeautifulSoup(html, features="html.parser").find("link")

    assert urlicon.get_soup_icon_size(soup_icon) == expected


def test_get_favicon_from_url_returns_favicon_when_response_is_not_html(monkeypatch):
    monkeypatch.setattr(urlicon, "requests_get", lambda url: b"\x00\x01icon")

    assert (
        urlicon.get_favicon_from_url("https://example.com/page")
        == "https://example.com/favicon.ico"
    )


@pytest.mark.parametrize("favicon_response", [None, b"<html>not an icon</html>"])
def test_get_favicon_from_url_returns_none_for_missing_or_html_response(
    monkeypatch,
    favicon_response,
):
    monkeypatch.setattr(urlicon, "requests_get", lambda url: favicon_response)

    assert urlicon.get_favicon_from_url("https://example.com/page") is None


def test_get_favicon_from_url_returns_none_when_request_raises(monkeypatch):
    def fake_requests_get(url):
        raise urlicon.requests.RequestException

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    assert urlicon.get_favicon_from_url("https://example.com/page") is None


def test_get_first_img_from_url_returns_absolute_image_url(monkeypatch):
    monkeypatch.setattr(
        urlicon,
        "requests_get",
        lambda url: b'<html><img src="/images/first.png"></html>',
    )

    assert (
        urlicon.get_first_img_from_url("https://example.com/page")
        == "https://example.com/images/first.png"
    )


def test_get_first_img_from_url_uses_provided_soup(monkeypatch):
    soup = BeautifulSoup('<html><img src="images/first.png"></html>', "html.parser")
    monkeypatch.setattr(urlicon, "requests_get", lambda url: b"already fetched")

    assert (
        urlicon.get_first_img_from_url("https://example.com/page", soup)
        == "https://example.com/images/first.png"
    )


@pytest.mark.parametrize("html", [None, b"<html><p>No image</p></html>"])
def test_get_first_img_from_url_returns_none_when_no_image_exists(monkeypatch, html):
    monkeypatch.setattr(urlicon, "requests_get", lambda url: html)

    assert urlicon.get_first_img_from_url("https://example.com/page") is None


def test_get_first_img_from_url_returns_none_when_request_raises(monkeypatch):
    def fake_requests_get(url):
        raise urlicon.requests.RequestException

    monkeypatch.setattr(urlicon, "requests_get", fake_requests_get)

    assert urlicon.get_first_img_from_url("https://example.com/page") is None


def test_get_default_img_sanitizes_and_encodes_input_text():
    assert (
        urlicon.get_default_img("https://www.example.com/some path?q=1!")
        == "https://ui-avatars.com/api/?name=example%20com%20somepathq1"
    )


def test_get_img_from_a_soup_item_uses_large_embedded_image(monkeypatch):
    long_src = "data:image/png;base64," + ("a" * 200)
    soup_item = BeautifulSoup(
        f'<a href="/post"><img src="{long_src}"></a>',
        "html.parser",
    ).find("a")
    monkeypatch.setattr(
        urlicon,
        "get_url_icon",
        lambda href: pytest.fail("large embedded image should be used"),
    )

    assert urlicon.get_img_from_a_soup_item(soup_item, "https://example.com") == long_src
    assert soup_item["href"] == "https://example.com/post"


def test_get_img_from_a_soup_item_discovers_href_icon_for_small_image(monkeypatch):
    soup_item = BeautifulSoup(
        '<a href="/post"><img src="/tiny.png"></a>',
        "html.parser",
    ).find("a")

    def fake_get_url_icon(href):
        assert href == "https://example.com/post"
        return "https://example.com/post-icon.png"

    monkeypatch.setattr(urlicon, "get_url_icon", fake_get_url_icon)

    assert (
        urlicon.get_img_from_a_soup_item(soup_item, "https://example.com")
        == "https://example.com/post-icon.png"
    )


class FakeCache:
    def __init__(self, values=None):
        self.values = values or {}
        self.set_calls = []

    def get(self, cache_id):
        return self.values.get(cache_id)

    def set(self, content, cache_id):
        self.set_calls.append((cache_id, content))
        self.values[cache_id] = content


def test_requests_get_returns_cached_content_without_http_request(monkeypatch):
    cache = FakeCache({"sniff-urf:https://example.com": b"cached"})
    monkeypatch.setattr(urlicon, "cache", cache)
    monkeypatch.setattr(
        urlicon.requests,
        "get",
        lambda **kwargs: pytest.fail("cache hit should avoid HTTP"),
    )

    assert urlicon.requests_get("https://example.com") == b"cached"
    assert cache.set_calls == []


def test_requests_get_caches_successful_response(monkeypatch):
    cache = FakeCache()
    monkeypatch.setattr(urlicon, "cache", cache)

    class Response:
        status_code = 200
        content = b"fresh"

    def fake_get(**kwargs):
        assert kwargs == {"url": "https://example.com", "timeout": 5}
        return Response()

    monkeypatch.setattr(urlicon.requests, "get", fake_get)

    assert urlicon.requests_get("https://example.com") == b"fresh"
    assert cache.set_calls == [("sniff-urf:https://example.com", b"fresh")]


def test_requests_get_returns_none_for_non_200_response(monkeypatch):
    cache = FakeCache()
    monkeypatch.setattr(urlicon, "cache", cache)

    class Response:
        status_code = 404
        content = b"missing"

    monkeypatch.setattr(urlicon.requests, "get", lambda **kwargs: Response())

    assert urlicon.requests_get("https://example.com/missing") is None
    assert cache.set_calls == []


def test_is_file_binary_returns_false_for_text_file(tmp_path):
    file_path = tmp_path / "text.txt"
    file_path.write_text("plain text")

    assert urlicon.is_file_binary(str(file_path)) is False


def test_is_file_binary_returns_true_for_binary_file(tmp_path):
    file_path = tmp_path / "binary.dat"
    file_path.write_bytes(b"\xff\xfe\x00\x00")

    assert urlicon.is_file_binary(str(file_path)) is True
