#!/bin/sh
set -eu
git config blame.ignoreRevsFile .git-blame-ignore-revs
rm -rf .venv
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
# silence a warning, i don't like yellow on my console
pip install wheel
pip install -e .[dev]

. ~/.nvm/nvm.sh
nvm install
npm install
