#!/usr/bin/env python
from setuptools import find_packages, setup

from uncms import VERSION

DEPENDENCIES = [
    'requests',
    'Pillow',
    'sorl-thumbnail',
    'Jinja2==3.1.2',

    'beautifulsoup4',
    'bleach>=5.0.1,<6',
    'django>=3.2,<3.3',
    'django-watson',
    'django-reversion',
    'django-jinja==2.10.2',
    'psycopg2',
    'python-magic==0.4.15',
]


setup(
    name='uncms',
    version='.'.join(str(n) for n in VERSION),
    url='https://github.com/lewiscollard/uncms',
    author='Lewis Collard',
    author_email='lewis@lewiscollard.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    description='Not quite a content management system.',
    install_requires=DEPENDENCIES,
    extras_require={
        'dev': [
            'factory-boy==3.2.1',
            'flake8==3.7.9',
            'isort==4.3.21',
            'pylint==2.4.4',
            'pytest==7.1.3',
            'pytest-cov',
            'pytest-django==4.5.2',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
