=========
 Plugins
=========

How to use plugins
------------------

Plugins must be specified with the ``plugins`` setting:

.. code-block:: python

   plugins = ['sigal.plugins.adjust', 'sigal.plugins.copyright']

You can either specify the name of the module which contains the plugin, or
import the plugin before adding it to the list:

.. code-block:: python

   from sigal.plugins import copyright
   plugins = ['sigal.plugins.adjust', copyright]

.. note:: Using an import like this will break the multiprocessing feature,
    because the settings dict must be serializable. So in most cases you should
    prefer the first option.

The ``plugin_paths`` setting can be used to specify paths to search for plugins
(if they are not in the python path).

Write a new plugin
------------------

Plugins are based on signals with the blinker_ library. A plugin must
subscribe to a signal (the list is given below). New signals can be added if
need. See an example with the copyright plugin:

.. _blinker: http://pythonhosted.org/blinker/

.. literalinclude:: ../sigal/plugins/copyright.py
   :language: python

Signals
-------

.. function:: sigal.signals.album_initialized(album)
   :noindex:

   Called after the :class:`~sigal.gallery.Album` is initialized.

   :param album: the :class:`~sigal.gallery.Album` object.

.. data:: sigal.signals.gallery_initialized(gallery)
   :noindex:

   Called after the gallery is initialized.

   :param gallery: the :class:`Gallery` object.

.. data:: sigal.signals.media_initialized(media)
   :noindex:

   Called after the :class:`~sigal.gallery.Media`
   (:class:`~sigal.gallery.Image` or :class:`~sigal.gallery.Video`) is
   initialized.

   :param media: the media object.

.. data:: sigal.signals.gallery_build(gallery)
   :noindex:

   Called after the gallery is build (after media are resized and html files
   are written).

   :param gallery: the :class:`Gallery` object.

.. data:: sigal.signals.img_resized(img, settings=settings)
   :noindex:

   Called after the image is resized. This signal work differently, the
   modified image object must be returned by the registered function.

   :param img: the PIL image object.
   :param settings: the settings dict.

List of plugins
---------------

Adjust plugin
=============

.. automodule:: sigal.plugins.adjust

Compress assets plugin
======================

.. automodule:: sigal.plugins.compress_assets

Copyright plugin
================

.. automodule:: sigal.plugins.copyright

Extended caching plugin
=======================

.. automodule:: sigal.plugins.extended_caching

Feeds plugin
============

.. automodule:: sigal.plugins.feeds

Media page plugin
=================

.. automodule:: sigal.plugins.media_page

Nomedia plugin
==============

.. automodule:: sigal.plugins.nomedia

ZIP Gallery plugin
==================

.. automodule:: sigal.plugins.zip_gallery

Upload to S3 plugin
===================

.. automodule:: sigal.plugins.upload_s3

Watermark plugin
================

.. automodule:: sigal.plugins.watermark
