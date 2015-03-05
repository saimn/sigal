
init:
	pip install -r requirements.txt

docs:
	make -C docs html

test:
	py.test

coverage:
	py.test --cov sigal --cov-report term --cov-report=html

demo:
	sigal build -c tests/sample/sigal.conf.py && sigal serve tests/sample/_build

publish:
	python setup.py register
	python setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: docs
