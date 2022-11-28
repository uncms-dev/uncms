#!/bin/sh
pytest --cov=uncms --cov=tests tests
isort --diff --check-only
flake8 uncms/ tests/
pylint uncms/ tests/
