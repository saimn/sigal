COLORBOX_PATH=sigal/themes/colorbox/static/css

all: colorbox

init:
	pip install -r requirements.txt

docs:
	make -C docs html

colorbox:
	cat $(COLORBOX_PATH)/{base,skeleton,colorbox,style}.css | cssmin > $(COLORBOX_PATH)/style.min.css

test:
	py.test

coverage:
	py.test --cov sigal --cov-report term --cov-report=html

publish: colorbox
	python setup.py register
	python setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: colorbox  docs
