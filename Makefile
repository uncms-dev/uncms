PYTHON = "python3"

.PHONY: python-bootstrap node-bootstrap bootstrap

bootstrap: python-bootstrap node-bootstrap

node-bootstrap:
	. ~/.nvm/nvm.sh && nvm install && npm install

python-bootstrap:
	git config blame.ignoreRevsFile .git-blame-ignore-revs
	rm -rf .venv
	$(PYTHON) -m venv .venv
	. .venv/bin/activate; \
	pip install --upgrade pip; \
	pip install wheel; \
	pip install -e .[dev]
