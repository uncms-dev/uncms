#!/bin/sh
pytest --cov=cms cms
isort --diff --check-only
flake8 cms/
pylint cms/
