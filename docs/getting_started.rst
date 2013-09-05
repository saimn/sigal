=================
 Getting started
=================

How to Use
~~~~~~~~~~

Init
  To get started, just run ``sigal init`` which will copy an example
  :doc:`configuration file <configuration>` in the current directory. All
  configuration values have a default; values that are commented out serve to
  show the default.  Default values are specified when modified in this example
  config file.

Build
  After adapting the configuration to your needs, put your images in
  a sub-directory (``pictures`` by default) and run ``sigal build <your images
  directory>``. The next time you run ``sigal build``, only the new images will
  be processed. Use the ``-f`` flag to force the reprocessing of all the
  images. Images that are smaller than the size specified by the ``img_size``
  setting will not be resized.

Serve
  To visualize your gallery, you can use ``sigal serve`` which runs a basic
  web server. This server should only be used for local browsing, not in
  production. Another option is to use the ``index_in_url = True`` setting,
  which will add ``index.html`` to the urls to allow browsing without a
  server.


Help of the ``sigal build`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ sigal build [-h] [-d] [-v] [-f] [-c CONFIG] [-t THEME]
            [source] [destination]

Required arguments:

``source``
  Input directory

``destination``
  Output directory (default: ``_build/``)

Optional arguments:

``-h, --help``
  Show this help message and exit

``-f, --force``
  Force the reprocessing of existing images and thumbnails

``-v, --verbose``
  Show all messages

``-d, --debug``
  Show all message, including debug messages

``-c CONFIG, --config CONFIG``
  Configuration file (default: ``sigal.conf.py`` in the current working
  directory)

``-t THEME, --theme THEME``
  Specify a theme directory, or a theme name for the themes included with Sigal
