==============
 Installation
==============

With pip::

    $ pip install sigal

Or to install with optional dependencies (listed below)::

    $ pip install sigal\[all\]

To install the development version, see the :doc:`contribute`.

Also, note that Sigal depends on `Pillow
<https://github.com/python-pillow/Pillow>`_, which needs specific libraries when
building from sources. See their `Installation documentation
<https://pillow.readthedocs.io/en/stable/installation.html>`_ for more details.

Dependencies
~~~~~~~~~~~~

The mandatory dependencies are:

- Blinker
- Click
- Jinja2
- Pilkit
- Pillow
- Python Markdown

There are also a number of optional dependencies for the :doc:`plugins`, listed
in the ``requirements.txt`` file:

- Brotli, zopfli (compress assets plugin)
- Boto (upload to S3 plugin)
- feedgenerator (feeds plugin)

Packages
~~~~~~~~

Some packages are available for Linux distributions:

- `Archlinux <https://www.archlinux.org/packages/community/any/sigal/>`_
- `Gentoo <https://packages.gentoo.org/packages/media-gfx/sigal>`_
- `OpenSuse
  <https://build.opensuse.org/package/show/openSUSE:Factory/python-sigal>`_
- `NixOS <https://nixos.org/nixos/packages.html#sigal>`_
