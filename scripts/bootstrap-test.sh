#!/bin/sh

rm -rf .venv
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
# silence a warning, i don't like yellow on my console
pip install wheel
# Use 3.2 until 4.2 LTS is out.
pip install "django>3.2,<3.3"
pip install -e .[dev]
