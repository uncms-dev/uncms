#!/bin/sh
pytest --cov=src --cov=tests tests
isort --diff --check-only .
flake8
pylint src/ tests/
