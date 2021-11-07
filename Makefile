.PHONY: test
test:
	pipenv run tox -e isort,black,mypy,flake8 -p 2
	pipenv run tox -e py310

.PHONY: benchmark
benchmark:
	pipenv run tox -e bench

requirements.txt:
	pipenv lock -r > requirements.txt

.PHONY: dev
dev: requirements.txt
	python setup.py develop

.PHONY: dist
dist: requirements.txt
	python setup.py sdist
