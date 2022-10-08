#!/bin/sh
pytest cms
isort --diff --check-only
flake8 cms/
pylint cms/
