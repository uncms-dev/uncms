# Building a robots.txt

Most sites will have a robots.txt,
if only to direct search engines to your [sitemap](sitemaps.md).
UnCMS has helpers for building one.

Let's create this view in e.g. `yoursite.views`:

```python
from uncms import robots

class MyRobotsTxtView(robots.RobotsTxtView):
    pass
```

And in your root urlconf:

```python
from yoursite.views import MyRobotsTxtView

urlpatterns = [
    # ...
    path('robots.txt', MyRobotsTxtView.as_view(), name='robots_txt'),
]
```

If you now visit `/robots.txt` you will find...an empty `robots.txt`!
That is because  we haven't defined any rules to go in it.

Let's start with a sitemap.
Hopefully you have added one as per its [documentation](sitemaps.md).
If you haven't, go do that now!
If you have, let's add our sitemap to our `RobotsTxtView`:

```python
from django.urls import reverse_lazy

from uncms import RobotsTxtView


class MyRobotsTxtView(robots.RobotsTxtView):
    sitemaps = [reverse_lazy('django.contrib.sitemaps.views.sitemap')]
```

Sitemaps may be a a single string (`'/sitemap.xml`),
a string-like thing such as the result of `reverse_lazy`,
or a list of either of the previous two things.

Let's see what our `/robots.txt` looks like now:

```
Sitemap: http://example.com/sitemap.xml
```

This is all you need for most websites.
However, you might find yourself needing to add robots entries.
Let's say we have a robot called "Badbot" which you do not want to crawl the site,
but this bot _is_ polite enough to obey `robots.txt`. Let's block it:

```python
class MyRobotsTxtView(robots.RobotsTxtView)
    sitemaps = [reverse_lazy('django.contrib.sitemaps.views.sitemap')]

    user_agents = [
        robots.UserAgentRule(
            agent='Badbot',
            disallow='/',
            # You may specify a comment which will be placed immediately above
            # the rule.
            comment='Go away',
        ),
    ]
```

This will render the following robots.txt:

```
# Go away
User-agent: Badbot
Disallow: /

Sitemap: http://example.com/sitemap.xml
```

`UserAgentRule` may be instantiated with the following options:

* `agent` (string, or list of strings): required; the user agent or agents to which this rule will apply.
* `allow` (string, or list of strings): paths which the bot should be allowed to crawl. You may use lazy objects such as the return value of `reverse_lazy` here instead of strings.
* `disallow`(string, or list of strings): paths which this bot should _not_ be allowed to crawl. As above, you may use lazy objects instead of strings. Note that you should not use this for things that are truly _secret_, because robots.txt is public. Nor should you use this to unindex things from e.g. Google; you will want to use the meta robots tag in the _document_ for this.
* `crawl_delay` (integer): ignored by some major robots; delay in seconds between fetching any two URLs from the site
* `comment`: a comment to place immediately above the user agent rule

At least one of `allow`, `disallow`, or `crawl_delay` must be provided.

## Alternatively...

...you can forgo all this over-engineering and render a `robots.txt` from a template with the same name!
It might be less effort than all of the above,
even though you'll be dealing with finicky behaviour around whitespace.
For that purpose, there is `uncms.views.TextTemplateView`,
a trivial subclass of Django's `TemplateView` which adds a plain text `Content-Type` header.

```python
from django.urls import path

from uncms.views import TextTemplateView

urlpatterns = [
    # ..
    path('robots.txt', TextTemplateView.as_view(template_name='robots.txt')),
]
```

Now create your `robots.txt` in one of your template directories and this will be rendered at `/robots.txt`.
