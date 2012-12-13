COLORBOX_PATH=colorbox/static/css
GALLERIA_PATH=galleria/static/css

all:
	sass $(COLORBOX_PATH)/style.scss:$(COLORBOX_PATH)/style.min.css --style compressed
	sass $(GALLERIA_PATH)/style.scss:$(GALLERIA_PATH)/style.min.css --style compressed

colorbox:
	sass --watch $(COLORBOX_PATH)/style.scss:$(COLORBOX_PATH)/style.min.css \
	     --style compressed

galleria:
	sass --watch $(GALLERIA_PATH)/style.scss:$(GALLERIA_PATH)/style.min.css \
	     --style compressed

.PHONY: colorbox galleria
