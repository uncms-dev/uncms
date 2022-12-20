#!/usr/bin/env python
from setuptools import find_packages, setup

from uncms import VERSION

DEPENDENCIES = [
    'requests',
    'Pillow',
    'sorl-thumbnail',

    'beautifulsoup4',
    'bleach>=5.0.1,<6',
    'django>=3.2,<3.3',
    'django-watson',
    'django-reversion',
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
    description='A CMS toolkit for Django, with an emphasis on speed, simplicity and familiarity.',
    install_requires=DEPENDENCIES,
    extras_require={
        'dev': [
            'factory-boy==3.2.1',
            'flake8==6.0.0',
            'isort==4.3.21',
            'Jinja2==3.1.2',
            'pylint==2.15.6',
            'pylint-django==2.5.3',
            'pytest==7.2.0',
            'pytest-cov',
            'pytest-django==4.5.2',
        ],
        'jinja2': [
            'Jinja2==3.1.2',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
