# Load .env file if existing
-include .env

export UNIT_TESTER_IMAGE=estimations-api-tester

# Local commands
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-lint.txt
	docker network create --driver bridge scrum-apis
.PHONY: install

lint:
	./bin/lint
.PHONY: lint

unit-tests:
	@docker build --tag ${UNIT_TESTER_IMAGE} --file ./tests/Dockerfile .
	@docker run --rm --volume ${PWD}/tests/out:/app/tests/out ${UNIT_TESTER_IMAGE} --junitxml=/app/tests/out/results.xml /app/tests
.PHONY: unit-tests

build:
	docker-compose build server
.PHONY: build

build-api-test:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		build tester
.PHONY: build-api-test

run:
	@./docker/boot-local.sh
.PHONY: run

run-local-api-test:
	@rm -fv docker-compose.override.yml
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		run --no-deps --use-aliases tester /app/tests
.PHONY: run-local-api-test

restart:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		restart server
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		restart migrations
.PHONY: restart

clean:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		down -v
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		down -v
	@rm -fv docker-compose.override.yml
.PHONY: clean

# CI commands

build-image:
	@./ci/cli do build
.PHONY: build-image

push-image:
	@./ci/cli do push
.PHONY: push-image

api-test:
	@./ci/cli do api-tests
.PHONY: api-test
