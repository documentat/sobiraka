.PHONY: *

tests:
	@rm -f $${COVERAGE_FILE:-.coverage}
	@(cd tests && PYTHONPATH=../src python -m coverage run --source=sobiraka -m unittest discover --start-directory=. --verbose)
	@(cd tests && python -m coverage report --precision=1 --skip-empty --skip-covered --show-missing)

lint:
	@PYTHONPATH=src python -m pylint sobiraka

docs:
	@rm -rf docs/modules
	@rm -rf build/docs/*
	@SPHINX_APIDOC_OPTIONS=members sphinx-apidoc src/sobiraka --force --separate --output-dir docs/modules
	@sphinx-build -a -j auto docs docs/build