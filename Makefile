# Load .env file if existing
-include .env

local:
	ln -sfv docker/docker-compose.local.yml docker-compose.override.yml
	docker-compose config
.PHONY: local

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-lint.txt
	docker network create --driver bridge scrum-apis
.PHONY: install

lint:
	# lint check (flake)
	docker run --rm \
		--workdir /app \
		-e APP_DIR=/app \
		-e CONF_DIR=/app/conf \
		--volume ${PWD}/.flake8:/app/.flake8 \
		--volume ${PWD}/requirements-lint.txt:/app/requirements-lint.txt \
		--volume ${PWD}/bin/:/app/bin/ \
		--volume ${PWD}/conf/:/app/conf/ \
		--volume ${PWD}/migrations/:/app/migrations/ \
		--volume ${PWD}/src/:/app/src/ \
		--entrypoint /bin/sh \
		python:3.7-alpine /app/bin/lint
.PHONY: lint

build:
	docker-compose build server
.PHONY: build
