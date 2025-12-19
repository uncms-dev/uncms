#!/bin/sh
set -eu

NO_FRONTEND=false
PYTHON_VERSION="python3"

while [ $# -gt 0 ]; do
    case $1 in
        --no-frontend)
            NO_FRONTEND=true
            shift
            ;;
        --python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

git config blame.ignoreRevsFile .git-blame-ignore-revs
rm -rf .venv
$PYTHON_VERSION -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
# silence a warning, i don't like yellow on my console
pip install wheel
pip install -e .[dev]

if [ "$NO_FRONTEND" = false ]; then
    . ~/.nvm/nvm.sh
    nvm install
    npm install
fi
