# A walkthrough

This walkthrough will take you through setting up UnCMS on an existing project, and it will introduce several core UnCMS concepts.
If you prefer to learn from code than learn from a wall of text,
you probably want to look at the companion [tiny UnCMS project repo](https://github.com/uncms-dev/tiny-uncms-project).

## Install UnCMS

`pip install uncms`

## Django settings

We'll need to add a few settings that UnCMS depends on.
Don't worry too much about what these do for now; the concepts behind them will be explained in depth over the course of the walkthrough.

First, create an UNCMS dictionary for all of UnCMS's settings,
and add the `SITE_DOMAIN` key with your default domain:

```python
UNCMS = {
    # Note that you do not want "www." before this - we'll obey the Django
    # PREPEND_WWW setting when constructing URLs.
    'SITE_DOMAIN': 'example.com',
}
```

This is the _only_ required setting in this dictionary, because it cannot always be guessed.
It is used by template tags to turn relative /urls/ into `https://actual.absolute/urls/`.
It is safe to set this to `'example.com'` - or any other value - if you do not know what your domain will be yet.

Add our core UnCMS apps to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # your other apps here...

    # Reversion is used for version control and rollback. It is required by
    # UnCMS.
    'reversion',
    # sorl-thumbnail is used for thumbnailing image fields in the admin, and
    # as such is required by UnCMS.
    'sorl.thumbnail',
    # watson is used for full-text search. You don't need to use it on the
    # front-end of your site, but it is used in the admin.
    'watson',

    # These are the core UnCMS apps.
    'uncms',
    'uncms.pages',
    'uncms.media',
    # Links is optional, but it's very handy to have.
    'uncms.links',
]
```

Add two necessary context processors to our template context processors (in `['OPTIONS']['context_processors']`):

```python
'django.template.context_processors.request',
'uncms.pages.context_processors.pages',
```

Add the page management middleware to your `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ...
    'uncms.middleware.PublicationMiddleware',
    'uncms.pages.middleware.PageMiddleware',
]
```

Make sure your `MEDIA_URL` is defined.
It defaults to `"/"` if you created your Django project with `django-admin startproject`,
but UnCMS's pages middleware is smart enough to skip requests for static files and media files by checking them for the `MEDIA_URL` prefix.
And since all page URLs start with `"/"`, no pages will be served, ever!
So UnCMS will throw an error if you don't set it.

```python
MEDIA_URL = '/media/'
```

Finally, you will need something like this in your root URLconf.
You may change the path part, but do not change the namespace.

```
urlpatterns = [
    # ... your other stuff here ...
    path('library/', include('uncms.media.urls', namespace='media_library')),
]
```

## Let's make a content model

First, create an app called "content". Assuming that your apps all live in a folder called `apps`, this will do:

```
mkdir apps/content
touch apps/content/__init__.py
```

Now add your `content` app to your `INSTALLED_APPS`.

Then, add this to your `models.py`:

```python
from uncms.pages.models import ContentBase
from django.db import models


class MyContent(ContentBase):
    introduction = models.TextField(
        null=True,
        blank=True,
    )
```

Let's unpack this!

The `Page` model in UnCMS defines its place in the hierarchy, some invisible metadata fields, and some publication controls, and that is it.
It has no opinions about what the _user-visible_ content should look like - not so much as an HTML field!
This is the job of **content models**.

That's what derivatives of `ContentBase` are. Anything that inherits from `ContentBase` will be available as a page type in your project.
_There is no explicit registration of content models_; it just works.

?> **Note:** We've named this model MyContent.
In our companion <a href="https://github.com/uncms-dev/tiny-uncms-project">tiny UnCMS project</a>, we've named it simply "Content".
We use "MyContent" here to avoid confusion between the concept of a "content model", and our model that is named "Content".

`introduction` is, of course, a standard Django field, which we'll use this later in our template.
We don't have to define any fields at all on this model! Just its existence as a non-abstract class inheriting from ContentBase will make it available in the page types.

Now go to your admin and add a Page. You will be prompted to select a page type. Once you have selected "My content" as your page type, your page will appear with the `introduction` field all ready to fill out. Do that now, save the page, then go to the root URL on your website.

Surprise! It's totally empty.
Just as it doesn't have any assumptions about what your content looks like, it doesn't have any opinions on what the front end of your site should look like either.
But UnCMS is in fact rendering this view, and is making an educated guess as to what template it should use. It's falling back to your `base.html` at the moment, but that's not its first choice. Let's create a template called `content/mycontent.html`:

```
{% extends 'base.html' %}

{% block main %} {# or whatever your main block is on your site :) #}
  <h1>{{ pages.current.title }}</h1>

  <p>{{ pages.current.content.introduction }}</p>
{% endblock %}
```

Now reload your page. It has content! That's because if it hasn't been told to do anything else, it will look for a template at `<app_label>/<model_name>.html`. Convention over configuration ahoy!

Where did `pages` come from? That would be the template context processor you added earlier.
`pages.current` refers to the currently active Page.
`pages.current.content` refers to the instance of your content model that is attached to the page.

This is the very simplest example of rendering a page's content model on the front end.
There's all sorts of other things we can do with content models, but if your model has some fields, and maybe some inlines, you don't _need_ to write any views, just a template.

Did we (royal we) say inlines? We definitely did.

## Lets add some admin inlines

OK, so let's say you want to build your new content page out of an entirely arbitrary number of sections.
That's fine too!
We can add inlines to our change-page view in the admin.
Here is what your model looks like.
Pay special attention to the ForeignKey if nothing else - this is essential, and note that it is to `pages.Page` and _not_ your content model:

```python
class ContentSection(models.Model):
    page = models.ForeignKey(
        'pages.Page',
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        max_length=100,
    )

    text = models.TextField(
        null=True,
        blank=True,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ['order']
```

We've defined a section model with a title, text, and an ordering field.
Now let's register it as an inline for MyContent:

```python
from uncms.pages.admin import page_admin
from django.contrib.admin import StackedInline

from .models import MyContent, ContentSection


class ContentSectionInline(StackedInline):
    model = ContentSection

page_admin.register_content_inline(MyContent, ContentSectionInline)
```

That's it! It's just as easy as adding inlines to any other model.
We've told UnCMS "be prepared to display these inlines only when the page type is MyContent".
This won't appear on pages whose type is any other model, because it might not make sense there.

Now, stick this just before the `{% endblock %}` in your `content/mycontent.html` template:

```
{% for section in pages.current.contentsection_set.all() %}
  <section>
    <h2>{{ section.title }}</h2>

    {% if section.text %}
      {{ section.text }}
    {% endif %}
  </section>
{% endfor %}
```

And that concludes part 1: You can now build pages out of an arbitrary number of sections
In fact, for a lot of sites, you might not even need to write a single view!

## Let's make another content model: a deeper dive

For the second part of this walkthrough, we are going to create a simple blog app using some of UnCMS's more advanced tooling.

First, create an app called "news", add it to your `INSTALLED_APPS`, and add this to your `news/models.py`:

```python
from uncms.pages.models import ContentBase

class NewsFeed(ContentBase):

    classifier = 'apps'

    icon = 'icons/news.png'
```

Notice that we're not declaring any model fields here - for now, we won't need to.
Instead, we've introduced two new class attributes that will be used on the "Add a page" screen in your admin: `classifier` and `icon`.

On the "Add a page" screen, the available page types are broken down into classifiers.
Really, this is just a heading under which this page type will appear.
At Onespacemedia we use 'apps' for content models whose primary purpose it is to display links to other content, and 'content' for content models for which the content is primarily on-page.
That's just our convention; you can actually name this anything you like. UnCMS doesn't mind!

The `icon` attribute will, as you may have guessed, be displayed in the "Add a page" screen too.
This attribute should be a path inside your static files directory.
The icon itself should be 96x96, but making it a little larger won't hurt.

We don't actually _have_ to specify an icon here; `ContentBase` from which `NewsFeed` inherits has a default icon.
Our news app is super-special, though, so let's give it an icon all its own.
At Onespacemedia we made a whole lot of icons, all in the same style, which are perfect for the 'Add a page' screen.
For now, go grab
[this one](https://github.com/onespacemedia/cms-icons/blob/master/png/news.png)
for your news app and put it in your `static/icons` directory.

This content model will be a news feed, to which articles can be assigned (with a normal `ForeignKey`).
We want to be able to have multiple types of news feed.
For example, we might want to have a page of articles called "News" (what your cat did today) vs "Blog" (insights on cat behaviour).
We'll get to exactly how this will happen shortly.
But first, we're going to need an Article model.

## Let's use UnCMS's helper models

UnCMS comes with a lot of handy helper models, and some nice helper fields too.
You will want to use them, because you should always use the batteries! We're going to be introducing a couple of them in our `Article` model.

First, add these imports to your `news/models.py`:

```python
from uncms.media.models import ImageRefField
from uncms.models import HtmlField, PageBase
```

And add the model itself:

```python
class Article(PageBase):
    page = models.ForeignKey(
        'news.NewsFeed',
        on_delete=models.PROTECT,
        null=True,
        blank=False,
        verbose_name='News feed',
    )

    image = ImageRefField(
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    content = HtmlField()

    date = models.DateTimeField(
        default=now,
    )

    summary = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title
```

Let's talk about PageBase!
It's a helper (abstract) model to make it easier for you to have article-like fields on your model.
It has nearly all the fields that the Page model itself does, but does not consider itself part of any hierarchy.
In fact, the UnCMS Page itself inherits from PageBase.
Here's what you get (see the [helper models](helpers.md) section for more):

* A title and slug
* Online/offline controls (enforced by the manager)
* SEO fields like meta descriptions and a title override
* OpenGraph fields

On to `ImageRefField`.
You can read about the [media app](media-app.md) later on, but the short version is: it's a model wrapper around Django's `FileField`.
`ImageRefField` is a ForeignKey to `media.File`, but it uses a raw ID widget by default, and is constrained to only select files that appear to be images (just a regex on the filename).

`HtmlField` is a `TextField` with a nice WYSIWYG editor as its default widget.
You can use a standard TextField here if you like, or you can bring your own HTML editor; nothing in UnCMS requires `HtmlField` to be used.

Now, in our `admin.py` for our news app, we're going to register our Article:

```python
from uncms.admin import PageBaseAdmin
from django.contrib import admin

from .models import Article, NewsFeed


@admin.register(Article)
class ArticleAdmin(PageBaseAdmin):
    fieldsets = [
        (None, {
            'fields': ['title', 'slug', 'page', 'content', 'summary'],
        }),
        PageBaseAdmin.PUBLICATION_FIELDS,
        PageBaseAdmin.SEO_FIELDS,
        PageBaseAdmin.OPENGRAPH_FIELDS,
    ]
```

`PageBaseAdmin` defines some useful default behaviour for the article-like things it is intended to enable.
It also defines some useful fieldsets that you will definitely want, such as the publication controls (turning things on/offline), and those SEO and social media controls mentioned earlier.
You should use it for anything that inherits from `PageBase`, though nothing in UnCMS forces you to.

Now, go create a "News feed" page, if you haven't already, and add an Article, setting "Page" to your new news feed.

## Let's add URL routing

We've examined the simple case of how to render a content model using a template.
But what if we want total control over everything under a page's URL?
Like, for example, if we have a page at `/news/`, we want `/news/` to render a list of news articles, and `/news/my-article/` to render the article with the slug `my-article`, but without hard-coding anything in your root urlconf?

Glad you asked! First, let's create a `urls.py` inside your news app, and make it look like this:

```python
from django.urls import path

from . import views

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
]
```

You _don't_ want to add this to your root urlconf, because we don't need to.
Instead, add this to your `NewsFeed` model:

```python
urlconf = 'your_project.apps.news.urls'
```

You'll want to correct the path; we've assumed your news app lives at `your_project.apps.news`.
However you do this, this must be an absolute import path from the root of your Django application.

And there you have it: your page's URLs will now be controlled by your news app's urlconf!
In fact, even the default template-rendering behaviour we visited earlier comes from a default urlconf on ContentBase, which routes to an extremely simple TemplateView derivative.

You'll get an exception thrown now, because we didn't actually implement `news.views`. Let's add a `views.py` in there now:

## Let's access the pages system in a view

```python
from django.views.generic import ListView


class ArticleListView(ListView):
    model = Article

    def get_queryset(self):
        return super().get_queryset().filter(
            page__page=self.request.pages.current
        )

```

This is just a generic Django list view, nothing surprising here.
But we've overridden `get_queryset` so it only returns the articles that have their `page` attribute set to the `NewsFeed` content object of the current page.
We now have multiple news feeds!

Unpacking that `page__page` a bit: the first `page` is the content object, the second is the Page for which it is the content model (content models have a foreign key to Page).

Just like we had access to `pages`, `pages.current`, etc in the context in our template in our first content model example, we have them available in our view, as attributes of the current request.

Let's make a detail view for the article. Add this to your imports:

```python
from uncms.views import PageDetailView
```

And make our detail view here:

```python
class ArticleDetailView(PageDetailView):
    model = Article
```

`PageDetailView` is a subclass of Django's `DetailView` that takes care of putting the page title, SEO information and all the other `PageBase` metadata into the template context, where it can be accessed by UnCMS's template functions that render them on the page.
If you have a `DetailView` for a model that inherits from `PageBase`, you almost certainly want to inherit from `PageDetailView`, but nothing forces you to.

## Let's reverse some page URLs

Just as a page can define a `urlconf` to render it, that `urlconf` can be reversed any time you have access to a page. It so happens that our Article does: it has a `ForeignKey` to the content model, which has a foreign key to its Page, so we can access it via `self.page.page`.

Like all good models, our article deserves to know what URL it lives at. Let's write a `get_absolute_url` function:

```python
def get_absolute_url(self):
    return self.page.page.reverse('article_detail', kwargs={
        'slug': self.slug,
    })
```

We use `page.reverse` almost exactly like we do Django's `django.urls.reverse` -
in fact, the `reverse` function on Page uses `django.urls.reverse` internally, passing it the content model's urlconf.

Now that we have a `get_absolute_url` on our news article, we can add a `news/article_list.html` template, where Django's generic `ListView` is expecting to find it:

```
{% extends 'base.html' %}

{% block main %}
  <ul>
    {% for object in object_list %}
      <li>
        <a href="{{ object.get_absolute_url }}">{{ object.title }}</a>
      </li>
    {% endfor %}
  </ul>
{% endblock %}
```

And now that we can actually make our way to it, an article detail template at `news/article_detail.html`:

```
{% extends 'base.html' %}

{% block main %}
  <h1>{{ object.title }}</h1>

  {% if object.image %}
    <p>
      <img src="{{ object.image.get_absolute_url }}" alt="">
    </p>
  {% endif %}

  {{ object.content|safe }}
{% endblock %}
```

## Let's add some per-page settings

Now that we have a news feed, and our cats are writing countless articles about themselves, we'll probably find the need to paginate the news list at some point.
The simple data model of UnCMS makes it really easy to define page settings that are not visible to non-admin users.

Add this to our `NewsFeed` content model:

```python
per_page = models.IntegerField(
    verbose_name='articles per page',
    default=12,
)
```

Then, we can override `ListView`'s  `get_paginate_by` in our `ArticleListView`:

```python
    def get_paginate_by(self, queryset):
        return self.request.pages.current.content.per_page

```

There are many use cases for this sort of thing.
If we had a "Contact" content model that rendered a contact form, you could add an `EmailField` to decide who the submissions go to.
Or you may want to make certain `NewsFeed` pages use a different layout; in this case you could add a `layout` field and override `get_template_names` in your view.
There's no need to hard-code anything with UnCMS!
Some CMSes make this harder for developers than it needs to be; here you're just writing Django.

## Let's add fieldsets to our content model

You may remember that content models do not have `ModelAdmin`s at all - their fields get patched onto the admin form for the _Page_.
But, we like fieldsets! So we simply define them on the NewsFeed content model.
There's no need to list the various SEO and publication fields on the Page here, only ones that our content model has.

```python
fieldsets = [
    ('Settings', {
        'fields': ['per_page'],
    }),
]
```

Of course, this is a silly example as we only have one field on our content model, which doesn't really merit a fieldset.
But it's nice knowing that we have the option if we need it.

## Let's fix your base template

Finally, many times we mentioned about all of that SEO and OpenGraph goodness that would be available in your page's context if we used certain helper models and helper views.
Put this into the `<head>` of our site's base template:

```
{% include 'pages/head_meta.html' %}
```

## Next steps

If you haven't already, you'll want to clone the [tiny UnCMS project](https://github.com/uncms-dev/tiny-uncms-project) and have a look around.
It's a slightly-more-fleshed out version of the example we've written here. It has an absurd comment-to-code ratio and serves as a mini walkthrough all by itself.

If you're the reading type, you'll want to read [more about the pages system](pages-app.md).
