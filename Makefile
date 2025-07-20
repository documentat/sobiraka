.PHONY: *

PYTHON := 3.13
PANDOC := 3.7

DOCKER_RUN := docker run --rm -it
VERSION := $(shell cat src/sobiraka/VERSION)
ifdef CI
  DOCKER_RUN := docker run --rm
  VERSION := $(GITHUB_SHA)
endif

prepull-all:
	docker pull python:3.11-alpine3.21
	docker pull python:3.12-alpine3.21
	docker pull python:3.13-alpine3.21
	docker pull kjarosh/latex:2025.1-small
	docker pull node:20.18.1-alpine3.21
	docker pull alpine:3.21

prebuild-all:
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.6
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.7

	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.6
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.7

	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.6
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.7

package:
	$(eval IMAGE:=sobiraka:package)
	@docker build . --target build-package --tag $(IMAGE)
	@mkdir -p dist
	@$(DOCKER_RUN) -v $(PWD)/dist:/DIST $(IMAGE) sh -c 'cp /PIP/* /DIST'
	@docker image rm $(IMAGE) --force >/dev/null

release:
	$(eval IMAGE:=sobiraka:release)
	@docker build . \
		--target release \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--build-arg CREATED='$(shell date -u +%Y-%m-%dT%H:%M:%SZ)' \
		--build-arg GITHUB_REF_NAME='$(GITHUB_REF_NAME)' \
		--build-arg GITHUB_SHA='$(GITHUB_SHA)' \
		--build-arg VERSION='$(shell cat src/sobiraka/VERSION)' \
		--build-arg PUBLIC_REPOSITORY_URL='$(PUBLIC_REPOSITORY_URL)' \
		--build-arg DOCS_MASTER_URL='$(DOCS_MASTER_URL)' \
		--tag $(IMAGE)

release-latex:
	$(eval IMAGE:=sobiraka:release-latex)
	@docker build . \
		--target release-latex \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--build-arg CREATED='$(shell date -u +%Y-%m-%dT%H:%M:%SZ)' \
		--build-arg GITHUB_REF_NAME='$(GITHUB_REF_NAME)' \
		--build-arg GITHUB_SHA='$(GITHUB_SHA)' \
		--build-arg VERSION='$(shell cat src/sobiraka/VERSION)' \
		--build-arg PUBLIC_REPOSITORY_URL='$(PUBLIC_REPOSITORY_URL)' \
		--build-arg DOCS_MASTER_URL='$(DOCS_MASTER_URL)' \
		--tag $(IMAGE)

build-tester:
	$(eval IMAGE:=sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC))
	@docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--tag $(IMAGE)

build-linter:
	$(eval IMAGE:=sobiraka:linter)
	@docker build . \
		--target linter \
		--tag $(IMAGE)

test: build-tester test-nobuild

test-nobuild:
	$(eval IMAGE:=sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC))
	@$(DOCKER_RUN) \
		-v $(PWD)/pyproject.toml:/W/pyproject.toml:ro \
		-v $(PWD)/src:/W/src:ro \
		-v $(PWD)/tests:/W/tests:rw \
		$(IMAGE)

lint-production: build-linter
	@$(DOCKER_RUN) \
		-v $(PWD)/.pylintrc:/W/.pylintrc:ro \
		-v $(PWD)/pyproject.toml:/W/pyproject.toml:ro \
		-v $(PWD)/src/sobiraka:/W/src/sobiraka:ro \
		sobiraka:linter \
		python -m pylint sobiraka src/sobiraka/files/themes/*/extension.py

lint-tests: build-linter
	@$(DOCKER_RUN) \
		-v $(PWD)/.pylintrc:/W/.pylintrc:ro \
		-v $(PWD)/src/sobiraka:/W/src/sobiraka:ro \
		-v $(PWD)/tests:/W/tests:ro \
		sobiraka:linter \
		python -m pylint tests

prover: release
	@$(DOCKER_RUN) \
		-v $(PWD)/docs:/W/docs:ro \
		sobiraka:release \
		sobiraka prover docs/docs.yaml

docs-web: release
	@mkdir -p docs/build
	@$(DOCKER_RUN) \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		sobiraka web docs/docs.yaml --output docs/build
	@$(DOCKER_RUN) \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		chown -R $$(id -u):$$(id -g) docs/build

docs-pdf: release
	@mkdir -p docs/build
	@$(DOCKER_RUN) \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		sobiraka pdf docs/docs.yaml --output docs/build/sobiraka.pdf
	@$(DOCKER_RUN) \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release \
		chown $$(id -u):$$(id -g) docs/build/sobiraka.pdf

docs-latex: release-latex
	@mkdir -p docs/build
	@$(DOCKER_RUN) \
		-v $(PWD)/docs:/W/docs:ro \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-latex \
		sobiraka latex docs/docs.yaml --output docs/build/sobiraka.pdf
	@$(DOCKER_RUN) \
		-v $(PWD)/docs/build:/W/docs/build \
		sobiraka:release-latex \
		chown $$(id -u):$$(id -g) docs/build/sobiraka.pdf
