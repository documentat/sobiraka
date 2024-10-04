.PHONY: *

PYTHON := 3.13
PANDOC := 3.5

DOCKER_RUN := docker run --rm -it
ifdef CI
  DOCKER_RUN := docker run --rm
endif

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

test:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--build-arg PYTHON=$(PYTHON) \
		--build-arg PANDOC=$(PANDOC) \
		--tag sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC)
	@$(DOCKER_RUN) \
		sobiraka:test-with-python$(PYTHON)-pandoc$(PANDOC)

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
