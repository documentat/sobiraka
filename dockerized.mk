.PHONY: *

PREFIX ?= sobiraka

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

test-src:
	@docker run --rm -it -v $(PWD):/W:ro -e COVERAGE_FILE=~/coverage sobiraka:tester-src

test-dist:
	@docker run --rm -it -e COVERAGE_FILE=~/coverage sobiraka:tester-dist