# Using Jinja2 with UnCMS

UnCMS has extensive support for using Jinja2 as your template engine,
using Django's built-in Jinja2 backend.

Here is a sample entry for your `TEMPLATES` setting in Django:


```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            # put your project's template dirs here :)
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
                # These two are necessary to make UnCMS work.
                'django.template.context_processors.request',
                'uncms.pages.context_processors.pages',
            ],
            'environment': 'uncms.jinja2_environment.all.environment',
        },
    },
    # Don't forget to put Django's template backend after this! It is omitted
    # here for brevity.
]
```

That's mostly it!

Most importantly is `uncms.jinja2_environment.all.environment`.
This environment will add all of UnCMS's functions and filters to your environment.
Because of differing conventions in Jinja2 vs Django templates,
UnCMS's Jinja2 functions will have different names to Django template tags.
This is noted in the documentation as appropriate.

There is another `environment` available in UnCMS, called `uncms.jinja2_environment.all.sensible_defaults`.
This gives you all of UnCMS's functions and filters,
and adds a few more from Django.
It adds Django's
`date`,
`filesizeformat`,
`floatformat`,
`linebreaks`,
`linebreaksbr`,
`time`, and
`urlize`
filters.
It also adds equivalents to Django's `static` and `url` template tags,
as every site will probably use these.

Of course, you will want to add some of your own filters as well.
You can build your own environment based on UnCMS's environment like so:

```python
from uncms.jinja2_environment.all import sensible_defaults


def environment(**options):
    env = sensible_defaults(**options)
    # add list builtin to templates
    env.globals.update({
        'list': list,
    })
    env.filters.update({
        # add your own filters here
    })
    return env
```

...and add the dotted path to this `environment` function as your `'environment'` option to your Jinja2 engine
(e.g. `'yoursite.jinja2_environment.environment'`).
