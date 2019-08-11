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

api-test:
	@rm -fv docker-compose.override.yml
	./api-tester/prepare.sh
	DOCKER_NETWORK_NAME=scrum-apis docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		up tester /app/tests --junitxml=/app/out/junit.xml
.PHONY: api-test

build-api-test:
	@DOCKER_NETWORK_NAME=scrum-apis docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		build tester
.PHONY: build-api-test

local-api-test:
	@rm -fv docker-compose.override.yml
	@DOCKER_NETWORK_NAME=scrum-apis docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		run --no-deps tester /app/tests
.PHONY: local-api-test

clean:
	@DOCKER_NETWORK_NAME=scrum-apis docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		down -v
	@rm -fv docker-compose.override.yml
.PHONY: clean
