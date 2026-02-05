.PHONY: build, tests
build:
	uv sync
	rm -rf dist
	uv build

tests:
	uv run --dev coverage run --omit="./tests/*" -m pytest -s

report:
	uv run --dev coverage report -m

prepare:
	rm -rf dist
	rm -rf build
	git log v0.2.3..HEAD --oneline --format="* %h %s (%an)" > CHANGELOG.md
