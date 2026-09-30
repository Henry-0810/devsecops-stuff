PYTHON ?= python
IMAGE ?= devsecops-stuff:local
PORT ?= 8080

.PHONY: install lint format test build run docker-build docker-test docker-run lock

install:
	$(PYTHON) -m pip install --require-hashes -r requirements-dev.txt

lint:
	$(PYTHON) -m ruff check app tests scripts
	$(PYTHON) -m ruff format --check app tests scripts

format:
	$(PYTHON) -m ruff check --fix app tests scripts
	$(PYTHON) -m ruff format app tests scripts

test:
	$(PYTHON) -m pytest

# Python has no separate binary bundle: validate source and template compilation.
build:
	$(PYTHON) -m compileall -q app
	$(PYTHON) -c "import tempfile; from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('app/templates')); target = tempfile.TemporaryDirectory(); env.compile_templates(target.name, zip=None, ignore_errors=False); target.cleanup()"

run:
	$(PYTHON) -m uvicorn app.main:app --reload --port $(PORT)

docker-build:
	docker build --provenance=false --sbom=false --tag $(IMAGE) .

docker-test:
	$(PYTHON) scripts/docker_smoke.py $(IMAGE)

docker-run:
	docker run --rm -p $(PORT):8080 -v ideas-data:/data $(IMAGE)

# uv is pinned in the development lock. Commit both generated files together.
lock:
	$(PYTHON) -m uv pip compile --python-version 3.12 --universal --generate-hashes --custom-compile-command "make lock" requirements.in -o requirements.txt
	$(PYTHON) -m uv pip compile --python-version 3.12 --universal --generate-hashes --custom-compile-command "make lock" requirements-dev.in -o requirements-dev.txt
