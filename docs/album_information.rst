===================
 Album information
===================

Information on an album can be given in a file using the `markdown`_ syntax,
named ``index.md`` :

::

    Title: Another example gallery
    Thumbnail: test2.jpg

    And a description with *Markdown* syntax.

Some meta-data keys are used by Sigal to get the useful informations on the
gallery:

- *Title*: the gallery title.
- *Thumbnail*: the thumbnail that will be used in the parent directory to
  represent the gallery.

Any additional meta-data is available in the templates. For instance::

    Authors: Waylan Limberg
             John Doe

can be used in the template with:

.. code-block:: jinja

    {% if 'authors' in meta %}
    <p>Authors: {{ meta.authors|join(', ') }}</>
    {% endif %}

If this file does not exist or if some meta-data is missing:

- The directory's name is used for the title (dashes and underscores are
  replaced with spaces).
- The first image of the directory is used as thumbnail.

.. _markdown: http://daringfireball.net/projects/markdown/
