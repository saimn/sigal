GALLERIA_PATH=galleria/static/css

all: galleria

galleria:
	sass --watch $(GALLERIA_PATH)/style.scss:$(GALLERIA_PATH)/style.min.css \
	     --style compressed

.PHONY: galleria
