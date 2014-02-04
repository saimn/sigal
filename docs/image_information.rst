===================
Image information
===================

Additional information on an image can be given in a file using the `markdown`_ syntax,
named ``<imagename>.md`` (example: IMG_5206.jpg.md):

::

    Title: My awesome photo

    And a description with *Markdown* syntax.

EXIF data is directly extracted

Some meta-data keys are used by Sigal to get the useful informations on the
gallery:

- *Title*: the image title.

Any additional meta-data is available in the templates. For instance::

    Location: Las Vegas

can be used in the template with:

.. code-block:: jinja

    {% if media.desc.meta.location %}
    <p>Location: {{ media.desc.meta.location[0] }}</>
    {% endif %}

.. _markdown: http://daringfireball.net/projects/markdown/
