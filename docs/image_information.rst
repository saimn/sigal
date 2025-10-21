===================
 Image information
===================

Additional information on an image can be given in a file using the `markdown`_
syntax, named ``<imagename>.md`` (example: ``IMG_5206.md``)::

    Title: My awesome photo
    Date: 2020-01-01T09:00:00

    And a description with *Markdown* syntax.

EXIF data is directly extracted, see :ref:`simple-exif-data`. Some meta-data
keys are used by Sigal to get the useful informations on the gallery:

- *Title*: the image title.
- *Date*: the file date, useful when it cannot be read from the EXIF metadata,
  e.g. for videos and some image formats.
- *Lat* and *Lon*: geo-location for positioning the image on map galleries.
  Note that this overrides EXIF coordinates, so except for localizing when
  EXIF coordinates are missing it can also be used to localize the image
  based on what is depicted instead of where the camera was standing.

Any additional meta-data is available in the templates. For instance::

    Location: Las Vegas

can be used in the template with:

.. code-block:: jinja

    {% if media.meta.location %}
    <p>Location: {{ media.meta.location[0] }}</>
    {% endif %}

.. _markdown: http://daringfireball.net/projects/markdown/
