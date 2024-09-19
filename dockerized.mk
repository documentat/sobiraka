.PHONY: *

PREFIX ?= sobiraka

build: build-release-html build-release build-tester-python3.11 build-tester-python3.12 build-linter

build-release-html:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target release-html \
		--tag sobiraka:release-html

build-release:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target release \
		--tag sobiraka:release

build-tester-python3.12:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:tester-python3.12

build-tester-python3.11:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--build-arg PYTHON_VERSION=3.11 \
		--tag sobiraka:tester-python3.11

build-linter:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target linter \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:linter

test-python3.12:
	@docker run --rm -it -e COVERAGE_FILE=~/coverage sobiraka:tester-python3.12

test-python3.11:
	@docker run --rm -it -e COVERAGE_FILE=~/coverage sobiraka:tester-python3.11

lint:
	@docker run --rm -it -v $(PWD):/W:ro sobiraka:linter

docs-html:
	@mkdir -p docs/build
	@docker run --rm -it \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-html \
		sobiraka html docs/docs.yaml --output docs/build
	@docker run --rm -it \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-html \
		chown -R $$(id -u):$$(id -g) docs/build

docs-pdf:
	@mkdir -p docs/build
	@docker run --rm -it \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-html \
		sobiraka pdf docs/docs.yaml --output docs/build/sobiraka.pdf
	@docker run --rm -it \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-html \
		chown $$(id -u):$$(id -g) docs/build/sobiraka.pdf
