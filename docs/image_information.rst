===================
 Image information
===================

Additional information on an image can be given in a file using the `markdown`_
syntax, named ``<imagename>.md`` (example: ``IMG_5206.md``)::

    Title: My awesome photo

    And a description with *Markdown* syntax.

EXIF data is directly extracted, see :ref:`simple-exif-data`. Some meta-data
keys are used by Sigal to get the useful informations on the gallery:

- *Title*: the image title.

Any additional meta-data is available in the templates. For instance::

    Location: Las Vegas

can be used in the template with:

.. code-block:: jinja

    {% if media.meta.location %}
    <p>Location: {{ media.meta.location[0] }}</>
    {% endif %}

.. _markdown: http://daringfireball.net/projects/markdown/
