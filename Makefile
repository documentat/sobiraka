.PHONY: *

build-docker-release:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--tag sobiraka:release

build-docker-tester:
	@DOCKER_BUILDKIT=1 \
		docker build . \
		--target tester \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag sobiraka:tester

tests:
	@rm -f .coverage
	@(cd tests && PYTHONPATH=../src python -m coverage run --source=sobiraka -m unittest discover --start-directory=. --verbose)
	@(cd tests && python -m coverage report --precision=1 --skip-empty --skip-covered --show-missing)

docs:
	@rm -rf docs/modules
	@rm -rf build/docs/*
	@SPHINX_APIDOC_OPTIONS=members sphinx-apidoc src/sobiraka --force --separate --output-dir docs/modules
	@sphinx-build -a -j auto docs build/docs