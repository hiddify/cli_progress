.ONESHELL:
# uv manages the environment (.venv), the dependencies (pyproject.toml, uv.lock) and the builds.

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@uv run python -V
	@uv tree

.PHONY: install
install:          ## Install the project and its dev tools (.venv, from uv.lock).
	uv sync

.PHONY: fmt
fmt:              ## Format code using black & isort.
	uv run isort cli_progress/ tests/
	uv run black cli_progress/ tests/

.PHONY: lint
lint:             ## Run flake8, black, mypy.
	uv run flake8 cli_progress/
	uv run black --check cli_progress/ tests/
	uv run mypy cli_progress/

.PHONY: test
test:             ## Run the tests with coverage (make check: lint, then tests).
	uv run pytest -v --cov=cli_progress -l --tb=short --maxfail=1 tests/
	uv run coverage xml
	uv run coverage html

.PHONY: check
check: lint test  ## Everything CI runs: lint and tests.

.PHONY: build
build:            ## Build the sdist and the wheel into dist/.
	rm -rf dist && uv build

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr uv run pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > cli_progress/VERSION
	@uv run --with gitchangelog gitchangelog > HISTORY.md
	@git add cli_progress/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: docs
docs:             ## Build the documentation.
	@echo "building documentation ..."
	@uv run --group docs mkdocs build
	URL="site/index.html"; xdg-open $$URL || sensible-browser $$URL || x-www-browser $$URL || gnome-open $$URL || open $$URL

.PHONY: init
init:             ## Initialize the project based on an application template.
	@./.github/init.sh


# This project has been generated from rochacbruno/python-project-template
# __author__ = 'rochacbruno'
# __repo__ = https://github.com/rochacbruno/python-project-template
# __sponsor__ = https://github.com/sponsors/rochacbruno/
