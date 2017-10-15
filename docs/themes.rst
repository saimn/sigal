========
 Themes
========

Gallery pages are created from a `Jinja2`_ template ``index.html`` that must
be located in ``THEME_DIR/templates``.

.. _Jinja2: http://jinja.pocoo.org/docs/

Bundled themes
~~~~~~~~~~~~~~

Sigal comes with three themes, located in the ``sigal/themes`` folder:

**colorbox**:
    `source <http://www.jacklmoore.com/colorbox>`__, `demo
    <http://saimon.org/sigal-demo/colorbox/>`__. This theme uses a Swipe plugin
    to browse pictures on touch devices.

**galleria**:
    `source <http://galleria.io/>`__, `demo
    <http://saimon.org/sigal-demo/galleria/>`__. This theme is based on the
    classic theme, pictures can be browsed with left/right keys, fullscreen
    support is available with the `f` key, and a map can be shown with the `m`
    key if the ``show_map`` setting is True. The ``leaflet_provider`` setting
    can be used to customize the tile provider (using `Leaflet-providers
    <https://github.com/leaflet-extras/leaflet-providers#providers>`_).

**photoswipe**:
    `source <http://photoswipe.com/>`__, `demo
    <http://saimon.org/sigal-demo/photoswipe/>`__.

For developers, a Makefile is available to concatenate and minify the css
files, using `cssmin <https://pypi.python.org/pypi/cssmin>`_ (``pip install
cssmin``).

Variables
~~~~~~~~~

You can use the following variables in your template:

``album``
    The current album that is rendered in the HTML file, represented by an
    :class:`~sigal.gallery.Album` object.  ``album.medias`` contains the list
    of all medias in the album (represented by the
    :class:`~sigal.gallery.Image` and :class:`~sigal.gallery.Video` objects,
    inherited from :class:`~sigal.gallery.Media`).

``index_title``
    Name of the index. This is either the directory name or the title specified
    in the ``index.md`` of the ``source`` directory.

``settings``
    The entire dictionary from ``sigal.conf.py``.

``sigal_link``
    URL to the Sigal homepage.

``theme.name``, ``theme.url``
    Name and url of the currently used theme.

Filters
~~~~~~~

You can define custom jinja filters for your template by creating a ``filters.py`` script
at the root of your template directory.

This script will then be imported and all defined functions will be available as jinja filters
with the same names in your templates.

Documentation of sigal's main classes
-------------------------------------

.. autoclass:: sigal.gallery.Album
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: sigal.gallery.Media
   :members:
   :undoc-members:

.. autoclass:: sigal.gallery.Image
   :members:
   :undoc-members:

.. autoclass:: sigal.gallery.Video
   :members:
   :undoc-members:

.. _simple-exif-data:

Simpler EXIF data output
~~~~~~~~~~~~~~~~~~~~~~~~

Because the tags in the ``media.raw_exif`` dictionary are a little bit
cumbersome to use, some common tags are extracted and formatted for easy use in
templates. If available, you can use:

``media.exif.iso``
    The ISO speed rating.

``media.exif.focal``
    The focal length, formatted as a decimal number.

``media.exif.exposure``
    The exposure time formatted as a fractional number, e.g. "1/500".

``media.exif.fstop``
    The aperture value given as an F-number and formatted as a decimal.

``media.exif.datetime``
    The time the image was *taken*. It is a datetime object, that can be
    formatted with ``strftime``:

    .. code-block:: jinja

        {% if media.exif.datetime %}
            {{ media.exif.datetime.strftime('%A, %d. %B %Y') }}
        {% endif %}

    This will output something like "Monday, 25. June 2013", depending on your
    locale.

``media.exif.gps``
    If not None, the dict contains two keys ``lat`` and ``lon`` denoting the
    GPS coordinates of the location where the image was taken. ``lat`` will
    always be referenced to the north pole whereas ``lon`` will be referenced to
    east to the prime meridan. To provide a link on an OpenStreetMap you could
    write a template like this:

    .. code-block:: jinja

        {% if media.exif.gps %}
            <a href="http://openstreetmap.org/index.html?lat={{
            media.exif.gps.lat }}&lon={{ media.exif.long}}">Go to location</a>
        {% endif %}

