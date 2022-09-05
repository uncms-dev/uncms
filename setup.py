#!/usr/bin/env python
# coding: utf-8
import platform

from setuptools import find_packages, setup

from cms import VERSION

DEPENDENCIES = [
    'python-magic==0.4.15',
    'requests',
    'Pillow',
    'sorl-thumbnail',
    'Jinja2==3.1.2',

    'beautifulsoup4',
    'django>=3.2,<3.3',
    'django-historylinks',
    'django-watson',
    'django-reversion',
    'django-jinja==2.10.2',
    'python-magic',
    'tinypng',
]

if platform.python_implementation() == 'PyPy':
    DEPENDENCIES.append('psycopg2cffi')
else:
    DEPENDENCIES.append('psycopg2')


setup(
    name='onespacemedia-cms',
    version='.'.join(str(n) for n in VERSION),
    url='https://github.com/onespacemedia/cms',
    author='Lewis Collard',
    author_email='lewis@lewiscollard.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    description='CMS used by Onespacemedia',
    install_requires=DEPENDENCIES,
    extras_require={
        'dev': [
            'flake8==3.7.9',
            'isort==4.3.21',
            'pylint==2.4.4',
            'pytest>=3.8',
            'pytest-cov',
            'pytest-django',
            'pytest-xdist',
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
