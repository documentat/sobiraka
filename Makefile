.PHONY: *

IMAGE ?= sobiraka-dev

DOCKER_RUN = \
	docker run --rm -it \
	--user $$(id -u):$$(id -g) \
	--volume $$(pwd):/WORKDIR \
	${IMAGE}

docker:
	@echo Preparing Docker image
	@DOCKER_BUILDKIT=1 docker build . \
		--file Dockerfile.ci \
		--tag ${IMAGE} \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g)

tests:
	@rm -f .coverage
	@(cd tests && PYTHONPATH=../src python -m coverage run --source=sobiraka -m unittest discover --start-directory=. --verbose)
	@(cd tests && python -m coverage report --precision=1 --skip-empty --skip-covered --show-missing --fail-under=65.9)

tests-in-docker:
	@docker run --rm -it -v ${PWD}:/PRJ ${IMAGE} make tests