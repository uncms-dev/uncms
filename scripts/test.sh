#!/bin/sh
pytest --cov=uncms --cov=tests tests
isort --diff --check-only
flake8
pylint uncms/ tests/
