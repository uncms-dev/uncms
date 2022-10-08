# Middleware required for proper testing of pages.
REQUIRED_PAGE_MIDDLEWARE = [
    'cms.middleware.PublicationMiddleware',
    'cms.apps.pages.middleware.PageMiddleware',
    'watson.middleware.SearchContextMiddleware',
]
