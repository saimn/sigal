COLORBOX_PATH=sigal/themes/colorbox/static/css
GALLERIA_PATH=sigal/themes/galleria/static/css

all: colorbox galleria

init:
	pip install -r requirements.txt

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"

colorbox:
	cat $(COLORBOX_PATH)/{base,skeleton,colorbox,style}.css | cssmin > $(COLORBOX_PATH)/style.min.css

galleria:
	cat $(GALLERIA_PATH)/{normalize,style}.css | cssmin > $(GALLERIA_PATH)/style.min.css

test:
	py.test

coverage:
	py.test --cov sigal --cov-report term --cov-report=html

publish:
	python setup.py register
	python setup.py sdist upload
	python setup.py bdist_wheel upload

.PHONY: colorbox galleria
