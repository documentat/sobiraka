.PHONY: *

PYTHON := 3.13
PANDOC := 3.6

DOCKER_RUN := docker run --rm -it
ifdef CI
  DOCKER_RUN := docker run --rm
endif

prepull-all:
	docker pull python:3.11
	docker pull python:3.12
	docker pull python:3.13

	docker pull pandoc/latex:3.2-ubuntu
	docker pull pandoc/latex:3.3-ubuntu
	docker pull pandoc/latex:3.4-ubuntu
	docker pull pandoc/latex:3.5-ubuntu
	docker pull pandoc/latex:3.6-ubuntu

	docker pull pandoc/core:3.2-ubuntu
	docker pull pandoc/core:3.3-ubuntu
	docker pull pandoc/core:3.4-ubuntu
	docker pull pandoc/core:3.5-ubuntu
	docker pull pandoc/core:3.6-ubuntu

prebuild-all:
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.2
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.11 PANDOC=3.6

	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.2
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.12 PANDOC=3.6

	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.2
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.3
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.4
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.5
	$(MAKE) build-tester PYTHON=3.13 PANDOC=3.6

release-latex:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target release-latex \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--tag sobiraka:release-latex

release:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target release \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--tag sobiraka:release

build-tester:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--tag sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC)

test: build-tester
	@$(DOCKER_RUN) \
		sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC)

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
