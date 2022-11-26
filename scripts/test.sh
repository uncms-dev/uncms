#!/bin/sh
pytest --cov=uncms uncms
isort --diff --check-only
flake8 uncms/
pylint uncms/
