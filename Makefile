COLORBOX_PATH=sigal/themes/colorbox/static/css
GALLERIA_PATH=sigal/themes/galleria/static/css

all: colorbox galleria

colorbox:
	cat $(COLORBOX_PATH)/{base,skeleton,colorbox,style}.css | cssmin > $(COLORBOX_PATH)/style.min.css

galleria:
	cat $(GALLERIA_PATH)/{normalize,style}.css | cssmin > $(GALLERIA_PATH)/style.min.css

.PHONY: colorbox galleria
