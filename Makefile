# Load .env file if existing
-include .env

export DOCKER_NETWORK_NAME=scrum-apis

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-lint.txt
	docker network create --driver bridge scrum-apis
.PHONY: install

lint:
	./bin/lint
.PHONY: lint

build:
	docker-compose build server
.PHONY: build

build-api-test:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		build tester
.PHONY: build-api-test

api-test:
	@rm -fv docker-compose.override.yml
	./api-tester/ci/prepare.sh
	./api-tester/ci/run.sh
.PHONY: api-test

run:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		up
.PHONY: run

restart:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		restart server
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		restart migrations
.PHONY: restart

run-local-api-test:
	@rm -fv docker-compose.override.yml
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		-f docker/docker-compose.tester.local.yml \
		run --no-deps --use-aliases tester /app/tests
.PHONY: run-local-api-test

clean:
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.tester.yml \
		down -v
	@docker-compose -f docker-compose.yml \
		-f docker/docker-compose.local.yml \
		down -v
	@rm -fv docker-compose.override.yml
.PHONY: clean
