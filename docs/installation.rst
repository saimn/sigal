==============
 Installation
==============

Install the extension with one of the following commands::

    $ easy_install sigal

or alternatively if you have pip installed::

    $ pip install sigal

Dependencies
~~~~~~~~~~~~

- Click
- Jinja2
- Pilkit
- Python Imaging Library (PIL / Pillow, see below)
- Python Markdown

PIL or Pillow ?
~~~~~~~~~~~~~~~

PIL_ is almost dead, the last release was in 2009. If possible you should
prefer to use Pillow_, a fork of PIL which is actively developped, with
packaging improvements, Python 3 compatibility, etc.

You can install Pillow with ``pip install Pillow``, preferably in a
virtualenv_. To have JPG and PNG support, you must first install the
developpement packages of libjpeg, freetype2 and zlib.

- For Debian/Ubuntu, this is possible with::

    apt-get build-dep python-dev python-imaging

  Debian/Sid users can use the experimental ``python-imaging`` package that is
  built from Pillow source.

- For Archlinux, there is a package_ for sigal in the AUR which already uses
  Pillow.

.. _PIL: http://www.pythonware.com/products/pil/
.. _Pillow: https://github.com/python-imaging/Pillow
.. _package: https://aur.archlinux.org/packages/sigal/
.. _virtualenv: http://www.virtualenv.org/
