from textwrap import dedent

import pytest
from django.test import RequestFactory
from django.urls import reverse_lazy

from uncms import robots


def test_to_list():
    # pylint:disable-next=use-implicit-booleaness-not-comparison
    assert robots.to_list(None) == []
    assert robots.to_list(["1", "2", "3"]) == ["1", "2", "3"]
    assert robots.to_list(("1", "2", "3")) == ["1", "2", "3"]
    assert robots.to_list("1") == ["1"]


def test_useragentrule_validation():
    with pytest.raises(TypeError) as exc:
        robots.UserAgentRule(agent="Megabot 9000")
    assert (
        str(exc.value)
        == 'At least one of "allow", "disallow", or "crawl_delay" must be non-empty for UserAgentRule.'
    )

    robots.UserAgentRule(agent="Megabot 9000", allow=["/"])
    robots.UserAgentRule(agent="Megabot 9000", disallow=["/"])
    robots.UserAgentRule(agent="Megabot 9000", crawl_delay=5)


def test_useragentrule_get_text():
    roots = ("/", ["/"])
    subpaths = ["/admin/", ["/admin/"], reverse_lazy("admin:index")]

    for path in roots:
        rule = robots.UserAgentRule(agent="Megabot 9000", allow=path)
        assert (
            rule.get_text()
            == dedent(
                """
            User-agent: Megabot 9000
            Allow: /
        """
            ).strip()
        )

        for subpath in subpaths:
            rule = robots.UserAgentRule(
                agent="Megabot 9000", allow=path, disallow=subpath
            )
            assert (
                rule.get_text()
                == dedent(
                    """
                User-agent: Megabot 9000
                Allow: /
                Disallow: /admin/
            """
                ).strip()
            )

    for subpath in subpaths:
        rule = robots.UserAgentRule(agent="Megabot 9000", disallow=subpath)
        assert (
            rule.get_text()
            == dedent(
                """
            User-agent: Megabot 9000
            Disallow: /admin/
        """
            ).strip()
        )

    rule = robots.UserAgentRule(
        agent="Megabot 9000", allow="/", disallow="/admin/", comment="Testing"
    )
    assert (
        rule.get_text()
        == dedent(
            """
        # Testing
        User-agent: Megabot 9000
        Allow: /
        Disallow: /admin/
    """
        ).strip()
    )

    # Check that it works when specifying multiple user agents.
    rule = robots.UserAgentRule(agent=["Megabot 9000", "Turbotron 9001"], disallow="/")
    assert (
        rule.get_text()
        == dedent(
            """
        User-agent: Megabot 9000
        User-agent: Turbotron 9001
        Disallow: /
    """
        ).strip()
    )

    # Make sure the crawl_delay branch works.
    rule = robots.UserAgentRule(agent="Megabot 9000", crawl_delay=5)
    assert (
        rule.get_text()
        == dedent(
            """
        User-agent: Megabot 9000
        Crawl-delay: 5
    """
        ).strip()
    )


def test_robotstxtview_empty():
    """
    Ensure that an empty robots.txt is rendered properly.
    """

    class TestRobotsTxtView(robots.RobotsTxtView):
        pass

    request = RequestFactory().get("/robots.txt")
    response = TestRobotsTxtView.as_view()(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert response.content == b"\n"


def test_robotstxtview_with_robots():
    class TestRobotsTxtView(robots.RobotsTxtView):
        user_agents = [
            robots.UserAgentRule(
                agent="Megabot 9000",
                allow="/",
                # check both lists and lazy strings at the same time
                disallow=[reverse_lazy("admin:index")],
            ),
            robots.UserAgentRule(
                agent="Turbotron 9001",
                disallow="/",
                comment="Go away",
            ),
        ]

    request = RequestFactory().get("/robots.txt")
    response = TestRobotsTxtView.as_view()(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert (
        response.content.decode("utf8")
        == dedent(
            """
        User-agent: Megabot 9000
        Allow: /
        Disallow: /admin/

        # Go away
        User-agent: Turbotron 9001
        Disallow: /
        """
        ).lstrip()
    )


def test_robotstxtview_sitemaps():
    class TestRobotsTxtView(robots.RobotsTxtView):
        sitemaps = "/sitemap.xml"

    request = RequestFactory().get("/robots.txt")
    response = TestRobotsTxtView.as_view()(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert (
        response.content.decode("utf8")
        == dedent(
            """
        Sitemap: https://example.com/sitemap.xml
        """
        ).lstrip()
    )


def test_robotstxtview_with_everything():
    class TestRobotsTxtView(robots.RobotsTxtView):
        user_agents = [
            robots.UserAgentRule(
                agent="Megabot 9000",
                allow="/",
                # check both lists and lazy strings at the same time
                disallow=[reverse_lazy("admin:index")],
            ),
            robots.UserAgentRule(
                agent="Turbotron 9001",
                disallow="/",
                comment="Go away",
            ),
        ]

        sitemaps = ["/sitemap.xml", "/sitemap-pages.xml"]

    request = RequestFactory().get("/robots.txt")
    response = TestRobotsTxtView.as_view()(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert (
        response.content.decode("utf8")
        == dedent(
            """
        User-agent: Megabot 9000
        Allow: /
        Disallow: /admin/

        # Go away
        User-agent: Turbotron 9001
        Disallow: /

        Sitemap: https://example.com/sitemap.xml
        Sitemap: https://example.com/sitemap-pages.xml
        """
        ).lstrip()
    )
