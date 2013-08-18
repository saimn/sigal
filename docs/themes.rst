========
 Themes
========

Gallery pages are created from a `Jinja2`_ template ``index.html`` that must
be located in ``THEME_DIR/templates``.

.. _Jinja2: http://jinja.pocoo.org/docs/

Bundled themes
~~~~~~~~~~~~~~

Sigal comes with two themes, based on the `colorbox`_ and `galleria`_
Javascript libraries, and located in the ``sigal/themes`` folder.

The stylesheets for these themes are written with sass_ (``gem install sass``).
A Makefile is available to compile the scss files to css
(``sigal/themes/Makefile``).

.. _galleria: http://galleria.io/
.. _colorbox: http://www.jacklmoore.com/colorbox
.. _sass: http://sass-lang.com/

Variables
~~~~~~~~~

You can use the following variables in your template:

``albums``
    List of ``album`` objects. An ``album`` object has the following attributes:

    - ``album.name``
    - ``album.title``
    - ``album.url``
    - ``album.thumb``

``breadcrumb``
    List of ``(url, title)`` tuples defining the current breadcrumb path.

``index_title``
    Name of the index. This is either the directory name or the title specified
    in the ``index.md``.

``index_url``
    URL to the index page.

``medias``
    List of ``media`` objects. A ``media`` object has the following attributes:

    - ``media.type``: Either ``"img"`` or ``"vid"``.
    - ``media.file``: Location of the resized image.
    - ``media.thumb``: Location of the corresponding thumbnail image.
    - ``media.big``: If not None, location of the unmodified image.
    - ``media.exif``: If not None contains a dict with the most common tags. For
      more information, see :ref:`simple-exif-data`.
    - ``media.raw_exif``: If not ``None``, it contains the raw EXIF tags.

``meta`` and ``description``
    Meta data and album description. For details how to annotate your albums
    with meta data, see :doc:`album_information`.

``theme.name``
    Name of the currently used theme.

``settings``
    The entire dictionary from ``sigal.conf.py``. For example, you could use
    this to output an optional download link for zipped archives:

    .. code-block:: jinja

        {% if settings.zip_gallery %}
        <a href="{{ settings.zip_gallery }}">Download archive</a>
        {% endif %}

``sigal_link``
    URL to the Sigal homepage.

``zip_gallery``
    If not None, it contains the location of a zip archive with all original
    images of the corresponding directory.


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

