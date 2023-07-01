.PHONY: *

PREFIX ?= sobiraka

build: build-release build-tester-dist build-tester-src build-linter

build-release:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--tag sobiraka:release

build-tester-dist:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester-dist \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:tester-dist

build-tester-src:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester-src \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:tester-src

build-linter:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target linter \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:linter

test-src:
	@docker run --rm -it -v $(PWD):/W:ro -e COVERAGE_FILE=~/coverage sobiraka:tester-src

test-dist:
	@docker run --rm -it -e COVERAGE_FILE=~/coverage sobiraka:tester-dist

lint:
	@docker run --rm -it -v $(PWD):/W:ro sobiraka:linter

docs:
	@mkdir -p docs/build
	@docker run --rm -it \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		sobiraka html docs/docs.yaml docs/build
	@docker run --rm -it \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		chown -R $$(id -u):$$(id -g) docs/build
