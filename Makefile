
init:
	pip install -e .
	pip install -r requirements.txt

docs:
	make -C docs html

test:
	pytest

coverage:
	pytest --cov sigal --cov-report term --cov-report=html

demo:
	sigal build -c tests/sample/sigal.conf.py && sigal serve tests/sample/_build

publish:
	python setup.py register
	python setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: docs
