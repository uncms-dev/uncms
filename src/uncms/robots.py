"""
Helpers for generating robots.txt.
"""

from dataclasses import dataclass
from typing import Union

from django.http import HttpResponse
from django.views.generic import View

from uncms.utils import canonicalise_url


def to_list(obj):
    """
    `to_list` normalises the given `obj` to a list. It permits passing either
    a string or a list and getting a list back.
    """
    if obj is None:
        return []

    if isinstance(obj, (list, tuple)):
        return list(obj)
    return [obj]


@dataclass
class UserAgentRule:
    """
    UserAgentRule represents a "User-agent: xxx" rule in robots.txt.
    """

    agent: Union[list, str]
    allow: Union[list, str] = None
    disallow: Union[list, str] = None
    crawl_delay: int = None
    comment: str = None

    def __post_init__(self):
        # make sure the rule makes some sort of sense
        if not self.allow and not self.disallow and self.crawl_delay is None:
            raise TypeError(
                'At least one of "allow", "disallow", or "crawl_delay" must be non-empty for UserAgentRule.'
            )

    def get_text(self):
        lines = []
        if self.comment:
            lines.append(f"# {self.comment}")
        # Google's interpretation of the sitemaps standard is that we may
        # group User-Agent together.
        # https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt#grouping-of-lines-and-rules
        for agent in to_list(self.agent):
            lines.append(f"User-agent: {agent}")
        if self.crawl_delay is not None:
            lines.append(f"Crawl-delay: {self.crawl_delay}")
        for allowed in to_list(self.allow):
            lines.append(f"Allow: {allowed}")
        for allowed in to_list(self.disallow):
            lines.append(f"Disallow: {allowed}")
        return "\n".join(lines)


class RobotsTxtView(View):
    user_agents = []

    sitemaps = []

    def get(self, request, *args, **kwargs):
        text = "\n\n".join(self.get_blocks())
        return HttpResponse(f"{text}\n", content_type="text/plain; charset=utf-8")

    def get_blocks(self):
        user_agents = [agent.get_text() for agent in self.user_agents]
        sitemaps = "\n".join(
            [
                f"Sitemap: {canonicalise_url(sitemap)}"
                for sitemap in to_list(self.sitemaps)
            ]
        )
        return [block for block in user_agents + [sitemaps] if block]
